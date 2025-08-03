# Makefile for Local RAG with Agentic Knowledge Graph
# Usage: make up, make down, make logs, etc.

# Default target
.DEFAULT_GOAL := help

# Colors for output
YELLOW := \033[1;33m
GREEN := \033[1;32m
RED := \033[1;31m
RESET := \033[0m

.PHONY: help up down build logs status test clean agent-logs health

help: ## Show this help message
	@echo "$(GREEN)Local RAG - Agentic Knowledge Graph$(RESET)"
	@echo "$(YELLOW)Available commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

up: ## Start all services (Supabase + Agent)
	@echo "$(GREEN)Starting Local RAG services...$(RESET)"
	cd local-ai-packaged && docker-compose up -d
	@echo "$(GREEN)Services started! Access points:$(RESET)"
	@echo "  🤖 Agent API:    http://localhost:8009"
	@echo "  📊 Supabase:     http://localhost:8005" 
	@echo "  🕸️  Neo4j:       http://localhost:8008"
	@echo "  📝 N8N:          http://localhost:8001"
	@echo "$(YELLOW)Wait ~60s for all services to be ready$(RESET)"

down: ## Stop all services
	@echo "$(RED)Stopping Local RAG services...$(RESET)"
	cd local-ai-packaged && docker-compose down
	@echo "$(GREEN)Services stopped$(RESET)"

build: ## Build the agent container
	@echo "$(GREEN)Building agent container...$(RESET)"
	cd local-ai-packaged && docker-compose build agent
	@echo "$(GREEN)Agent container built$(RESET)"

logs: ## Show logs for all services
	cd local-ai-packaged && docker-compose logs -f

agent-logs: ## Show logs for agent service only
	cd local-ai-packaged && docker-compose logs -f agent

status: ## Show status of all services
	@echo "$(GREEN)Service Status:$(RESET)"
	cd local-ai-packaged && docker-compose ps

health: ## Check health of all services
	@echo "$(GREEN)Health Check:$(RESET)"
	@echo "$(YELLOW)Agent Health:$(RESET)"
	@curl -s http://localhost:8009/health | python3 -m json.tool 2>/dev/null || echo "❌ Agent not responding"
	@echo "\n$(YELLOW)Supabase Health:$(RESET)"
	@curl -s http://localhost:8005/health 2>/dev/null && echo "✅ Supabase OK" || echo "❌ Supabase not responding"

seed: ## Run document ingestion
	@echo "$(GREEN)Running document ingestion...$(RESET)"
	cd local-ai-packaged && docker-compose --profile init up agent-init
	@echo "$(GREEN)Document ingestion completed$(RESET)"

test: build up ## Build, start services, and run basic tests
	@echo "$(GREEN)Running Phase 3.1 integration tests...$(RESET)"
	@sleep 60  # Wait for services to start (increased for database init)
	@echo "$(YELLOW)Testing all service health checks...$(RESET)"
	@curl -f http://localhost:8009/health > /dev/null 2>&1 && echo "✅ Agent health check passed" || echo "❌ Agent health check failed"
	@curl -f http://localhost:8005/health > /dev/null 2>&1 && echo "✅ Supabase health check passed" || echo "❌ Supabase health check failed"
	@echo "$(YELLOW)Testing database schema...$(RESET)"
	@cd local-ai-packaged && docker-compose exec -T supabase-db psql -U postgres -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('documents', 'chunks', 'sessions', 'messages');" | grep -q "documents" && echo "✅ Database schema initialized" || echo "❌ Database schema missing"
	@echo "$(YELLOW)Testing agent API...$(RESET)"
	@curl -X POST http://localhost:8009/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "Hello", "session_id": "test-session"}' \
		> /dev/null 2>&1 && echo "✅ Agent API test passed" || echo "❌ Agent API test failed"
	@echo "$(YELLOW)Testing CLI functionality...$(RESET)"
	@cd local-ai-packaged && docker-compose exec -T agent python -c "from agent.cli import main; print('✅ CLI import test passed')" 2>/dev/null || echo "❌ CLI import test failed"

clean: down ## Stop services and remove containers/volumes
	@echo "$(RED)Cleaning up containers and volumes...$(RESET)"
	cd local-ai-packaged && docker-compose down -v --remove-orphans
	@echo "$(GREEN)Cleanup complete$(RESET)"

restart: down up ## Restart all services

dev: ## Start in development mode with live reload
	@echo "$(GREEN)Starting in development mode...$(RESET)"
	cd local-ai-packaged && docker-compose up -d
	@echo "$(YELLOW)For local development:$(RESET)"
	@echo "  1. cd agentic-rag-knowledge-graph"
	@echo "  2. source venv/bin/activate"
	@echo "  3. python -m uvicorn agent.api:app --reload --port 8058"

# Development helpers
shell-agent: ## Open shell in agent container
	cd local-ai-packaged && docker-compose exec agent /bin/bash

shell-db: ## Open PostgreSQL shell
	cd local-ai-packaged && docker-compose exec supabase-db psql -U postgres

shell-neo4j: ## Open Neo4j shell
	cd local-ai-packaged && docker-compose exec neo4j cypher-shell -u neo4j

ingest: ## Run document ingestion in agent container
	@echo "$(GREEN)Running document ingestion...$(RESET)"
	cd local-ai-packaged && docker-compose exec agent python -m ingestion.ingest --documents test_docs --clean --verbose

# Phase 3.2 Targets
test-phase32: ## Run Phase 3.2 acceptance tests
	@echo "$(GREEN)Running Phase 3.2 acceptance tests...$(RESET)"
	@python3 test_phase32.py

health-phase32: ## Check Phase 3.2 health status
	@echo "$(GREEN)Phase 3.2 Health Check:$(RESET)"
	@echo "$(YELLOW)OpenAI Models Endpoint:$(RESET)"
	@curl -s http://localhost:8009/v1/models | python3 -m json.tool 2>/dev/null || echo "❌ Models endpoint not responding"
	@echo "\n$(YELLOW)OpenWebUI Status:$(RESET)"
	@curl -s http://localhost:8002 -o /dev/null && echo "✅ OpenWebUI accessible" || echo "❌ OpenWebUI not responding"
	@echo "\n$(YELLOW)Supabase Studio (Direct):$(RESET)"
	@curl -s http://localhost:8005 -o /dev/null && echo "✅ Supabase Studio accessible" || echo "❌ Supabase Studio not responding"
	@echo "\n$(YELLOW)Kong Containers:$(RESET)"
	@docker ps --format "{{.Names}}" | grep -i kong && echo "❌ Kong containers still running" || echo "✅ No Kong containers found"
	@echo "\n$(YELLOW)Agent Health:$(RESET)"
	@curl -s http://localhost:8009/health | python3 -m json.tool 2>/dev/null || echo "❌ Agent health check failed"

validate-phase32: up ## Full Phase 3.2 validation
	@echo "$(GREEN)Validating Phase 3.2 implementation...$(RESET)"
	@sleep 30  # Wait for services to start
	@echo "$(YELLOW)Running health checks...$(RESET)"
	@make health-phase32
	@echo "\n$(YELLOW)Running acceptance tests...$(RESET)"
	@make test-phase32
	@echo "\n$(GREEN)Phase 3.2 validation complete!$(RESET)"