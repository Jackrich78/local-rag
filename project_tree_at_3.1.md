local-ai-packaged git:(feature/dockerised-agent) ✗ tree -L 2
.
├── assets
│   └── n8n-demo.gif
├── caddy-addon
├── Caddyfile
├── docker-compose.override.private.yml
├── docker-compose.override.public.supabase.yml
├── docker-compose.override.public.yml
├── docker-compose.yml
├── flowise
│   ├── create_google_doc-CustomTool.json
│   ├── get_postgres_tables-CustomTool.json
│   ├── send_slack_message_through_n8n-CustomTool.json
│   ├── summarize_slack_conversation-CustomTool.json
│   └── Web Search + n8n Agent Chatflow.json
├── LICENSE
├── Local_RAG_AI_Agent_n8n_Workflow.json
├── n8n
│   └── backup
├── n8n_pipe.py
├── n8n-tool-workflows
│   ├── Create_Google_Doc.json
│   ├── Get_Postgres_Tables.json
│   ├── Post_Message_to_Slack.json
│   └── Summarize_Slack_Conversation.json
├── neo4j
│   ├── config
│   ├── data
│   ├── logs
│   └── plugins
├── README.md
├── searxng
│   ├── settings-base.yml
│   └── settings.yml
├── secrets
│   ├── neo4j_auth
│   ├── openai_key
│   └── README.md
├── shared
├── start_services.py
└── supabase
    ├── CONTRIBUTING.md
    ├── data.sql
    ├── DEVELOPERS.md
    ├── docker
    ├── knip.jsonc
    ├── LICENSE
    ├── Makefile
    ├── package.json
    ├── pnpm-lock.yaml
    ├── pnpm-workspace.yaml
    ├── README.md
    ├── SECURITY.md -> apps/docs/public/.well-known/security.txt
    ├── supa-mdx-lint.config.toml
    ├── tsconfig.json
    └── turbo.json

17 directories, 39 files