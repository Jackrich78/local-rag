"""
FastAPI endpoints for the agentic RAG system.
"""

import os
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from dotenv import load_dotenv

from .agent import rag_agent, AgentDependencies
from .db_utils import (
    initialize_database,
    close_database,
    create_session,
    get_session,
    add_message,
    get_session_messages,
    test_connection
)
from .graph_utils import initialize_graph, close_graph, test_graph_connection
from .models import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    StreamDelta,
    ErrorResponse,
    HealthStatus,
    ToolCall,
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIMessage,
    OpenAIChoice,
    OpenAIDelta,
    OpenAIUsage
)
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    list_documents_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    DocumentListInput
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Application configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our module during development
if APP_ENV == "development":
    logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting up agentic RAG API...")
    
    try:
        # Initialize database connections
        await initialize_database()
        logger.info("Database initialized")
        
        # Initialize graph database
        await initialize_graph()
        logger.info("Graph database initialized")
        
        # Test connections
        db_ok = await test_connection()
        graph_ok = await test_graph_connection()
        
        if not db_ok:
            logger.error("Database connection failed")
        if not graph_ok:
            logger.error("Graph database connection failed")
        
        logger.info("Agentic RAG API startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down agentic RAG API...")
    
    try:
        await close_database()
        await close_graph()
        logger.info("Connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Agentic RAG with Knowledge Graph",
    description="AI agent combining vector search and knowledge graph for tech company analysis",
    version="0.1.0",
    lifespan=lifespan
)

# Add middleware with flexible CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Helper functions for OpenAI compatibility
def convert_openai_to_internal(openai_request: OpenAIChatRequest) -> tuple[str, Optional[str]]:
    """
    Convert OpenAI chat request to internal format.
    
    Args:
        openai_request: OpenAI chat completion request
        
    Returns:
        Tuple of (user_message, user_id)
    """
    # Extract the latest user message
    user_messages = [msg for msg in openai_request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found in request")
    
    latest_message = user_messages[-1].content
    user_id = openai_request.user
    
    return latest_message, user_id


def create_openai_response(content: str, session_id: str, model: str = "gpt-4o-mini", is_stream: bool = False) -> OpenAIChatResponse:
    """
    Create OpenAI-compatible response.
    
    Args:
        content: Response content
        session_id: Session ID for tracking
        model: Model name
        is_stream: Whether this is a streaming response
        
    Returns:
        OpenAI-compatible response
    """
    import time
    
    response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    timestamp = int(time.time())
    
    if is_stream:
        choice = OpenAIChoice(
            index=0,
            delta=OpenAIDelta(content=content),
            finish_reason=None
        )
        object_type = "chat.completion.chunk"
    else:
        choice = OpenAIChoice(
            index=0,
            message=OpenAIMessage(role="assistant", content=content),
            finish_reason="stop"
        )
        object_type = "chat.completion"
    
    # Estimate token usage (rough approximation)
    estimated_tokens = len(content.split()) * 1.3
    usage = OpenAIUsage(
        prompt_tokens=50,  # Rough estimate
        completion_tokens=int(estimated_tokens),
        total_tokens=int(estimated_tokens + 50)
    ) if not is_stream else None
    
    return OpenAIChatResponse(
        id=response_id,
        object=object_type,
        created=timestamp,
        model=model,
        choices=[choice],
        usage=usage
    )


# Helper functions for agent execution
async def get_or_create_session(request: ChatRequest) -> str:
    """Get existing session or create new one."""
    logger.info(f"get_or_create_session called with session_id: {request.session_id}, user_id: {request.user_id}")
    
    if request.session_id:
        logger.info(f"Checking existing session: {request.session_id}")
        session = await get_session(request.session_id)
        if session:
            logger.info(f"Found existing session: {request.session_id}")
            return request.session_id
        else:
            logger.info(f"Session {request.session_id} not found, creating new one")
    
    # Create new session
    logger.info(f"Creating new session for user_id: {request.user_id}")
    new_session_id = await create_session(
        user_id=request.user_id,
        metadata=request.metadata
    )
    logger.info(f"Created new session: {new_session_id}")
    return new_session_id


async def get_conversation_context(
    session_id: str,
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Get recent conversation context.
    
    Args:
        session_id: Session ID
        max_messages: Maximum number of messages to retrieve
    
    Returns:
        List of messages
    """
    messages = await get_session_messages(session_id, limit=max_messages)
    
    return [
        {
            "role": msg["role"],
            "content": msg["content"]
        }
        for msg in messages
    ]


def extract_tool_calls(result) -> List[ToolCall]:
    """
    Extract tool calls from Pydantic AI result.
    
    Args:
        result: Pydantic AI result object
    
    Returns:
        List of ToolCall objects
    """
    tools_used = []
    
    try:
        # Get all messages from the result
        messages = result.all_messages()
        
        for message in messages:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    # Check if this is a tool call part
                    if part.__class__.__name__ == 'ToolCallPart':
                        try:
                            # Debug logging to understand structure
                            logger.debug(f"ToolCallPart attributes: {dir(part)}")
                            logger.debug(f"ToolCallPart content: tool_name={getattr(part, 'tool_name', None)}")
                            
                            # Extract tool information safely
                            tool_name = str(part.tool_name) if hasattr(part, 'tool_name') else 'unknown'
                            
                            # Get args - the args field is a JSON string in Pydantic AI
                            tool_args = {}
                            if hasattr(part, 'args') and part.args is not None:
                                if isinstance(part.args, str):
                                    # Args is a JSON string, parse it
                                    try:
                                        import json
                                        tool_args = json.loads(part.args)
                                        logger.debug(f"Parsed args from JSON string: {tool_args}")
                                    except json.JSONDecodeError as e:
                                        logger.debug(f"Failed to parse args JSON: {e}")
                                        tool_args = {}
                                elif isinstance(part.args, dict):
                                    tool_args = part.args
                                    logger.debug(f"Args already a dict: {tool_args}")
                            
                            # Alternative: use args_as_dict method if available
                            if hasattr(part, 'args_as_dict'):
                                try:
                                    tool_args = part.args_as_dict()
                                    logger.debug(f"Got args from args_as_dict(): {tool_args}")
                                except:
                                    pass
                            
                            # Get tool call ID
                            tool_call_id = None
                            if hasattr(part, 'tool_call_id'):
                                tool_call_id = str(part.tool_call_id) if part.tool_call_id else None
                            
                            # Create ToolCall with explicit field mapping
                            tool_call_data = {
                                "tool_name": tool_name,
                                "args": tool_args,
                                "tool_call_id": tool_call_id
                            }
                            logger.debug(f"Creating ToolCall with data: {tool_call_data}")
                            tools_used.append(ToolCall(**tool_call_data))
                        except Exception as e:
                            logger.debug(f"Failed to parse tool call part: {e}")
                            continue
    except Exception as e:
        logger.warning(f"Failed to extract tool calls: {e}")
    
    return tools_used


async def save_conversation_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Save a conversation turn to the database.
    
    Args:
        session_id: Session ID
        user_message: User's message
        assistant_message: Assistant's response
        metadata: Optional metadata
    """
    # Save user message
    logger.info(f"Saving user message for session_id: {session_id}")
    await add_message(
        session_id=session_id,
        role="user",
        content=user_message,
        metadata=metadata or {}
    )
    
    # Save assistant message
    await add_message(
        session_id=session_id,
        role="assistant",
        content=assistant_message,
        metadata=metadata or {}
    )


async def execute_agent(
    message: str,
    session_id: str,
    user_id: Optional[str] = None,
    save_conversation: bool = True
) -> tuple[str, List[ToolCall]]:
    """
    Execute the agent with a message.
    
    Args:
        message: User message
        session_id: Session ID
        user_id: Optional user ID
        save_conversation: Whether to save the conversation
    
    Returns:
        Tuple of (agent response, tools used)
    """
    try:
        # Create dependencies
        deps = AgentDependencies(
            session_id=session_id,
            user_id=user_id
        )
        
        # Get conversation context
        context = await get_conversation_context(session_id)
        
        # Build prompt with context
        full_prompt = message
        if context:
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context[-6:]  # Last 3 turns
            ])
            full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {message}"
        
        # Run the agent
        result = await rag_agent.run(full_prompt, deps=deps)
        
        response = result.data
        tools_used = extract_tool_calls(result)
        
        # Save conversation if requested
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=response,
                metadata={
                    "user_id": user_id,
                    "tool_calls": len(tools_used)
                }
            )
        
        return response, tools_used
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        error_response = f"I encountered an error while processing your request: {str(e)}"
        
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=error_response,
                metadata={"error": str(e)}
            )
        
        return error_response, []


# OpenAI-compatible API Endpoints
@app.get("/v1/models")
async def get_models():
    """OpenAI-compatible models endpoint."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4o-mini",
                "object": "model", 
                "created": 1640995200,  # Static timestamp
                "owned_by": "local-ai-packaged",
                "permission": [],
                "root": "gpt-4o-mini",
                "parent": None
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    """OpenAI-compatible chat completions endpoint."""
    print(f">>> OpenAI endpoint called with model: {request.model}")
    logger.info(f"OpenAI endpoint called with model: {request.model}")
    try:
        # Convert OpenAI format to internal ChatRequest format
        logger.info("Converting OpenAI request to internal format")
        user_message, user_id = convert_openai_to_internal(request)
        logger.info(f"Converted: user_message='{user_message[:50]}...', user_id='{user_id}'")
        
        # Create internal ChatRequest to reuse working session logic
        internal_request = ChatRequest(
            message=user_message,
            session_id=None,  # Let system create new session
            user_id=user_id,
            metadata={"openai_format": True, "model": request.model}
        )
        
        # Use the working session logic from /chat endpoint
        logger.info(f"OpenAI endpoint calling get_or_create_session")
        session_id = await get_or_create_session(internal_request)
        logger.info(f"OpenAI endpoint created/retrieved session: {session_id}")
        
        # Verify session exists in database
        session_check = await get_session(session_id)
        logger.info(f"Session verification: {session_check is not None}")
        if not session_check:
            logger.error(f"Session {session_id} was not found in database after creation!")
        
        # For non-streaming requests
        if not request.stream:
            try:
                # Execute agent
                response, tools_used = await execute_agent(
                    message=user_message,
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception as agent_error:
                # Handle agent execution failures gracefully
                logger.error(f"Agent execution failed: {agent_error}")
                response = f"I'm experiencing technical difficulties: {str(agent_error)}"
                tools_used = []
            
            # Create OpenAI-compatible response
            openai_response = create_openai_response(
                content=response,
                session_id=session_id,
                model=request.model,
                is_stream=False
            )
            
            return openai_response
        
        # For streaming requests
        else:
            
            async def generate_openai_stream():
                """Generate OpenAI-compatible streaming response."""
                try:
                    import time
                    
                    response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                    timestamp = int(time.time())
                    
                    # Create dependencies
                    deps = AgentDependencies(
                        session_id=session_id,
                        user_id=user_id
                    )
                    
                    # Get conversation context
                    context = await get_conversation_context(session_id)
                    
                    # Build input with context
                    full_prompt = user_message
                    if context:
                        context_str = "\n".join([
                            f"{msg['role']}: {msg['content']}"
                            for msg in context[-6:]
                        ])
                        full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {user_message}"
                    
                    # Save user message immediately
                    await add_message(
                        session_id=session_id,
                        role="user",
                        content=user_message,
                        metadata={"user_id": user_id}
                    )
                    
                    full_response = ""
                    
                    # Stream using agent.iter() pattern
                    async with rag_agent.iter(full_prompt, deps=deps) as run:
                        async for node in run:
                            if rag_agent.is_model_request_node(node):
                                # Stream tokens from the model
                                async with node.stream(run.ctx) as request_stream:
                                    async for event in request_stream:
                                        from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta
                                        
                                        content = ""
                                        if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                            content = event.part.content
                                        elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                            content = event.delta.content_delta
                                        
                                        if content:
                                            # Create OpenAI streaming chunk
                                            chunk = OpenAIChatResponse(
                                                id=response_id,
                                                object="chat.completion.chunk",
                                                created=timestamp,
                                                model=request.model,
                                                choices=[OpenAIChoice(
                                                    index=0,
                                                    delta=OpenAIDelta(content=content),
                                                    finish_reason=None
                                                )]
                                            )
                                            
                                            yield f"data: {chunk.model_dump_json()}\n\n"
                                            full_response += content
                    
                    # Save assistant response
                    await add_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        metadata={"streamed": True}
                    )
                    
                    # Send final chunk with finish_reason
                    final_chunk = OpenAIChatResponse(
                        id=response_id,
                        object="chat.completion.chunk",
                        created=timestamp,
                        model=request.model,
                        choices=[OpenAIChoice(
                            index=0,
                            delta=OpenAIDelta(),
                            finish_reason="stop"
                        )]
                    )
                    
                    yield f"data: {final_chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"OpenAI streaming error: {e}")
                    error_chunk = OpenAIChatResponse(
                        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                        object="chat.completion.chunk",
                        created=int(time.time()),
                        model=request.model,
                        choices=[OpenAIChoice(
                            index=0,
                            delta=OpenAIDelta(content=f"Error: {str(e)}"),
                            finish_reason="stop"
                        )]
                    )
                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_openai_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        
    except Exception as e:
        logger.error(f"Chat completions endpoint failed: {e}")
        
        # Handle OpenAI quota errors gracefully
        error_message = str(e)
        if "insufficient_quota" in error_message or "429" in error_message:
            return create_openai_response(
                content="I'm currently experiencing high demand and cannot process your request. Please try again in a few minutes, or contact the administrator about API quota limits.",
                session_id=session_id if 'session_id' in locals() else "error-session",
                model=request.model,
                is_stream=False
            )
        
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoints
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connections
        db_status = await test_connection()
        graph_status = await test_graph_connection()
        
        # Determine overall status
        if db_status and graph_status:
            status = "healthy"
        elif db_status or graph_status:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            database=db_status,
            graph_database=graph_status,
            llm_connection=True,  # Assume OK if we can respond
            version="0.1.0",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        # Execute agent
        response, tools_used = await execute_agent(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id
        )
        
        return ChatResponse(
            message=response,
            session_id=session_id,
            tools_used=tools_used,
            metadata={"search_type": str(request.search_type)}
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        async def generate_stream():
            """Generate streaming response using agent.iter() pattern."""
            try:
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # Create dependencies
                deps = AgentDependencies(
                    session_id=session_id,
                    user_id=request.user_id
                )
                
                # Get conversation context
                context = await get_conversation_context(session_id)
                
                # Build input with context
                full_prompt = request.message
                if context:
                    context_str = "\n".join([
                        f"{msg['role']}: {msg['content']}"
                        for msg in context[-6:]
                    ])
                    full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {request.message}"
                
                # Save user message immediately
                await add_message(
                    session_id=session_id,
                    role="user",
                    content=request.message,
                    metadata={"user_id": request.user_id}
                )
                
                full_response = ""
                
                # Stream using agent.iter() pattern
                async with rag_agent.iter(full_prompt, deps=deps) as run:
                    async for node in run:
                        if rag_agent.is_model_request_node(node):
                            # Stream tokens from the model
                            async with node.stream(run.ctx) as request_stream:
                                async for event in request_stream:
                                    from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta
                                    
                                    if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                        delta_content = event.part.content
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                                        
                                    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                        delta_content = event.delta.content_delta
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                
                # Extract tools used from the final result
                result = run.result
                tools_used = extract_tool_calls(result)
                
                # Send tools used information
                if tools_used:
                    tools_data = [
                        {
                            "tool_name": tool.tool_name,
                            "args": tool.args,
                            "tool_call_id": tool.tool_call_id
                        }
                        for tool in tools_used
                    ]
                    yield f"data: {json.dumps({'type': 'tools', 'tools': tools_data})}\n\n"
                
                # Save assistant response
                await add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    metadata={
                        "streamed": True,
                        "tool_calls": len(tools_used)
                    }
                )
                
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Stream error: {str(e)}"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/vector")
async def search_vector(request: SearchRequest):
    """Vector search endpoint."""
    try:
        input_data = VectorSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await vector_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="vector",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/graph")
async def search_graph(request: SearchRequest):
    """Knowledge graph search endpoint."""
    try:
        input_data = GraphSearchInput(
            query=request.query
        )
        
        start_time = datetime.now()
        results = await graph_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            graph_results=results,
            total_results=len(results),
            search_type="graph",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def search_hybrid(request: SearchRequest):
    """Hybrid search endpoint."""
    try:
        input_data = HybridSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await hybrid_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="hybrid",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents_endpoint(
    limit: int = 20,
    offset: int = 0
):
    """List documents endpoint."""
    try:
        input_data = DocumentListInput(limit=limit, offset=offset)
        documents = await list_documents_tool(input_data)
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information."""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    
    return ErrorResponse(
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=str(uuid.uuid4())
    )


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "agent.api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_ENV == "development",
        log_level=LOG_LEVEL.lower()
    )