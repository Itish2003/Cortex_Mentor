# Product Overview

## What This Project Does

Cortex Mentor is an AI-powered software development mentor that acts as a persistent, personalized assistant for developers. It observes developer workflow through VS Code extension and Git hooks, processes events through a multi-pipeline system, and delivers real-time audio insights to help developers improve their coding practices and understand their work better.

The system combines event-driven architecture with AI-powered analysis to provide contextual guidance as developers write code, make commits, and work on projects.

## Target Users

- **Software Developers**: Primary users who want an AI mentor that learns from their workflow and provides contextual insights
- **Development Teams**: Teams looking to improve code quality and share knowledge through AI-augmented development practices
- **Individual Learners**: Developers seeking to improve their skills through real-time feedback on their coding patterns

## Key Features

### 1. Workflow Observation
- Git post-commit hook captures commit messages and diffs
- VS Code extension monitors file changes and code edits
- Non-intrusive event collection maintains developer flow

### 2. Intelligent Insight Generation
- Automatic summarization of code changes using local LLMs
- Pattern detection across commits and file changes
- Privacy-preserving analysis using hybrid knowledge model

### 3. Real-Time Audio Delivery
- Text-to-speech conversion of insights via Google Cloud TTS
- WebSocket-based streaming to VS Code extension
- Ambient, non-disruptive audio feedback

### 4. Hybrid Knowledge System
- **Private Knowledge**: Local markdown knowledge graph + ChromaDB vector database
- **Public Knowledge**: Cloud-based Upstash vector database with curated software development knowledge
- Intelligent synthesis combining both knowledge sources

### 5. Multi-Agent Reasoning
- Google ADK framework for complex reasoning tasks
- Sequential agent pipelines for web search and knowledge augmentation
- Structured output using Pydantic schemas

## Technology Stack

### Backend
- **Framework**: FastAPI 0.119.0
- **Language**: Python 3.12+
- **Package Manager**: uv (Poetry-compatible pyproject.toml)
- **Task Queue**: ARQ (async task queue) with Redis 5.0.4
- **WebSocket Server**: FastAPI + Uvicorn 0.37.0

### AI & ML
- **Local LLM**: Ollama (llama3.1:latest, nomic-embed-text:v1.5, llava-llama3:latest)
- **Cloud LLM**: Google Gemini (2.5 Flash, 2.5 Pro) via google-genai 1.50.1
- **Agent Framework**: Google ADK 1.16.0
- **Vector Databases**: ChromaDB 0.5.4 (local), Upstash Vector 0.8.0 (cloud)

### Frontend
- **Platform**: VS Code Extension
- **Location**: `cortex-vs/` directory (TypeScript)
- **Communication**: WebSocket client connecting to FastAPI backend

### Infrastructure
- **Message Bus**: Redis Pub/Sub for real-time insight delivery
- **Text-to-Speech**: Google Cloud Text-to-Speech 2.33.0
- **File Watching**: Watchdog 6.0.0
- **Git Integration**: GitPython 3.1.43

### Key Libraries
- Pydantic 2.12.0 for data validation
- Jinja2 3.1.6 for prompt templating
- PyYAML 6.0.3 for configuration
- NumPy <2.0 for numerical operations

## Project Type

**Event-Driven AI Service with Client Extension**

- Backend: Asynchronous event processing system with multi-pipeline architecture
- Frontend: VS Code extension providing UI and WebSocket connectivity
- Architecture Pattern: Pipeline-based, microservices-inspired with parallel processing
- Deployment: Local-first with cloud AI services for complex reasoning

## Privacy Model

- **Local-First**: All user code, commits, and private data stay on the local machine
- **Hybrid Processing**: Sensitive data processed by local Ollama models
- **Cloud Enhancement**: Public knowledge and complex reasoning use cloud Gemini models
- **Zero User Data Leakage**: User-specific information never sent to cloud services
