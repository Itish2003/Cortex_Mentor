# System Architecture Diagram

## High-Level System Overview

```mermaid
graph TB
    subgraph "Observers"
        GH[Git Hook Observer]
        FW[File Watcher]
        VSC[VS Code Extension]
    end
    
    subgraph "API Gateway - FastAPI"
        API["/api/events<br/>Event Ingestion"]
        WS["/ws<br/>WebSocket Server"]
        MAIN["main.py<br/>Application Entry"]
    end
    
    subgraph "Task Queue - ARQ + Redis"
        REDIS[(Redis)]
        ARQ[ARQ Worker]
        PUBSUB[Redis Pub/Sub<br/>insights_channel]
    end
    
    subgraph "Processing Pipelines"
        COMP[Comprehension Pipeline]
        SYNTH[Synthesis Pipeline]
        CURE[Curation Pipeline]
    end
    
    subgraph "Knowledge Stores"
        subgraph "Private Knowledge - Local"
            KG[Markdown Knowledge Graph<br/>Zettelkasten Style]
            CHROMA[(ChromaDB<br/>Vector Database)]
        end
        
        subgraph "Public Knowledge - Cloud"
            UPSTASH[(Upstash Vector DB)]
        end
    end
    
    subgraph "AI Services"
        subgraph "Local - Privacy Preserving"
            OLLAMA[Ollama LLM<br/>llama3.1, nomic-embed]
        end
        
        subgraph "Cloud - Complex Reasoning"
            GEMINI[Google Gemini<br/>2.5 Flash, 2.5 Pro]
            ADK[Google ADK<br/>Multi-Agent Framework]
            TTS[Google Cloud TTS<br/>Audio Generation]
        end
    end
    
    subgraph "Clients"
        VSCODE[VS Code Extension<br/>WebSocket Client]
        AUDIO[Audio Playback]
    end
    
    %% Event Ingestion Flow
    GH -->|POST event| API
    FW -->|POST event| API
    VSC -->|POST event| API
    
    API -->|Enqueue| REDIS
    REDIS -->|Dispatch| ARQ
    
    %% Comprehension Pipeline
    ARQ -->|Process Event| COMP
    COMP -->|Local LLM| OLLAMA
    COMP -->|Write| KG
    COMP -->|Embed & Store| CHROMA
    COMP -->|Trigger Synthesis| REDIS
    
    %% Synthesis Pipeline
    ARQ -->|Synthesis Task| SYNTH
    SYNTH -->|Query Private| CHROMA
    SYNTH -->|Traverse| KG
    SYNTH -->|Query Public| UPSTASH
    SYNTH -->|Evaluate| GEMINI
    SYNTH -.->|If Needed| CURE
    
    %% Curation Pipeline
    CURE -->|Web Search| ADK
    CURE -->|Analyze| GEMINI
    CURE -->|Augment| UPSTASH
    
    %% Delivery
    SYNTH -->|Final Insight| GEMINI
    SYNTH -->|Generate Audio| TTS
    SYNTH -->|Publish| PUBSUB
    
    %% WebSocket Broadcast
    PUBSUB -->|Broadcast| WS
    WS -->|Stream| VSCODE
    VSCODE -->|Play| AUDIO
    
    style COMP fill:#e1f5ff
    style SYNTH fill:#e1f5ff
    style CURE fill:#e1f5ff
    style KG fill:#fff4e6
    style CHROMA fill:#fff4e6
    style UPSTASH fill:#ffe6f0
    style OLLAMA fill:#e8f5e9
    style GEMINI fill:#fce4ec
```

## Component Layer Diagram

```mermaid
graph LR
    subgraph "Layer 1: API Gateway"
        L1A[FastAPI Routes]
        L1B[WebSocket Manager]
        L1C[Event Validation]
    end
    
    subgraph "Layer 2: Task Queue"
        L2A[ARQ Workers]
        L2B[Redis Pool]
        L2C[Job Scheduling]
    end
    
    subgraph "Layer 3: Pipeline Orchestration"
        L3A[Pipeline Class]
        L3B[Processor Base]
        L3C[Parallel Executor]
    end
    
    subgraph "Layer 4: Business Logic"
        L4A[Comprehension]
        L4B[Synthesis]
        L4C[Curation]
        L4D[Delivery]
    end
    
    subgraph "Layer 5: Services"
        L5A[LLM Service]
        L5B[Knowledge Graph]
        L5C[Vector DB Service]
        L5D[Prompt Manager]
    end
    
    subgraph "Layer 6: External Systems"
        L6A[Ollama API]
        L6B[Gemini API]
        L6C[ChromaDB]
        L6D[Upstash]
        L6E[Google TTS]
    end
    
    L1A --> L2A
    L1B --> L2B
    L2A --> L3A
    L3A --> L4A
    L3A --> L4B
    L3A --> L4C
    L3A --> L4D
    L4A --> L5A
    L4B --> L5B
    L4B --> L5C
    L4C --> L5A
    L5A --> L6A
    L5A --> L6B
    L5B --> L6C
    L5C --> L6D
    L4D --> L6E
    
    style L1A fill:#e3f2fd
    style L2A fill:#f3e5f5
    style L3A fill:#e8f5e9
    style L4A fill:#fff9c4
    style L5A fill:#ffe0b2
    style L6A fill:#ffccbc
```

## Data Flow Architecture

```mermaid
flowchart TD
    START([Developer Action])
    
    subgraph "Ingestion"
        EVENT[Git Commit /<br/>File Change]
        VALIDATE{Validate<br/>Event}
        QUEUE[Enqueue to<br/>ARQ Task Queue]
    end
    
    subgraph "Comprehension Pipeline"
        DESER[Deserialize Event<br/>EventDeserializer]
        INSIGHT[Generate Insight<br/>InsightGenerator<br/>🔒 Local Ollama]
        
        subgraph "Parallel Storage"
            KGWRITE[Write Markdown<br/>KnowledgeGraphWriter]
            CHROMAWRITE[Embed & Store<br/>ChromaWriter]
        end
        
        SYNCTRIG[Trigger Synthesis<br/>SynthesisTrigger]
    end
    
    subgraph "Synthesis Pipeline"
        subgraph "Parallel Knowledge Retrieval"
            PVTQUERY[Query ChromaDB<br/>PrivateKnowledgeQuerier]
            PVTTRAV[Traverse Graph<br/>GraphTraversalProcessor]
            PUBQUERY[Query Upstash<br/>PublicKnowledgeQuerier]
            GATEWAY[Evaluate Quality<br/>KnowledgeGatewayProcessor<br/>☁️ Gemini Flash]
        end
        
        CURE_COND{Needs<br/>Improvement?}
        CURATION[Curation Pipeline<br/>Web Search + Analysis<br/>☁️ Multi-Agent ADK]
        
        SYNTHESIZE[Synthesize Insight<br/>InsightSynthesizer<br/>☁️ Gemini Pro]
    end
    
    subgraph "Delivery Pipeline"
        AUDIO[Generate Audio<br/>AudioDeliveryProcessor<br/>☁️ Google TTS]
        PUBLISH[Publish to Redis<br/>insights_channel]
        BROADCAST[Broadcast via<br/>WebSocket]
    end
    
    END([VS Code Extension<br/>Audio Playback])
    
    START --> EVENT
    EVENT --> VALIDATE
    VALIDATE -->|Valid| QUEUE
    VALIDATE -->|Invalid| ERROR[Return Error]
    
    QUEUE --> DESER
    DESER --> INSIGHT
    INSIGHT --> KGWRITE
    INSIGHT --> CHROMAWRITE
    KGWRITE --> SYNCTRIG
    CHROMAWRITE --> SYNCTRIG
    
    SYNCTRIG --> PVTQUERY
    SYNCTRIG --> PUBQUERY
    
    PVTQUERY --> PVTTRAV
    PUBQUERY --> GATEWAY
    
    PVTTRAV --> SYNTHESIZE
    GATEWAY --> CURE_COND
    
    CURE_COND -->|Yes| CURATION
    CURE_COND -->|No| SYNTHESIZE
    CURATION --> SYNTHESIZE
    
    SYNTHESIZE --> AUDIO
    AUDIO --> PUBLISH
    PUBLISH --> BROADCAST
    BROADCAST --> END
    
    style INSIGHT fill:#c8e6c9
    style KGWRITE fill:#c8e6c9
    style CHROMAWRITE fill:#c8e6c9
    style GATEWAY fill:#f8bbd0
    style CURATION fill:#f8bbd0
    style SYNTHESIZE fill:#f8bbd0
    style AUDIO fill:#f8bbd0
```

## Privacy Boundaries

```mermaid
graph TB
    subgraph "🔒 LOCAL PROCESSING - Privacy Preserving"
        UC[User Code<br/>Commits<br/>File Changes]
        OLLAMA_LOCAL[Ollama LLM]
        KG_LOCAL[Markdown<br/>Knowledge Graph]
        CHROMA_LOCAL[ChromaDB<br/>Vector Store]
        
        UC -->|Process| OLLAMA_LOCAL
        OLLAMA_LOCAL -->|Store| KG_LOCAL
        OLLAMA_LOCAL -->|Embed| CHROMA_LOCAL
    end
    
    subgraph "☁️ CLOUD PROCESSING - Public Knowledge Only"
        PUB_KNOW[Public Knowledge<br/>Software Dev Best Practices]
        GEMINI_CLOUD[Google Gemini]
        UPSTASH_CLOUD[Upstash Vector DB]
        TTS_CLOUD[Google TTS]
        
        PUB_KNOW -->|Query| UPSTASH_CLOUD
        PUB_KNOW -->|Synthesize| GEMINI_CLOUD
        GEMINI_CLOUD -->|Audio| TTS_CLOUD
    end
    
    subgraph "🔄 SYNTHESIS - Combining Knowledge"
        MERGE[Insight Synthesizer<br/>Combines Private + Public]
        
        CHROMA_LOCAL -.->|Sanitized Context| MERGE
        KG_LOCAL -.->|Sanitized Context| MERGE
        UPSTASH_CLOUD -->|Public Knowledge| MERGE
        MERGE -->|Final Insight| GEMINI_CLOUD
    end
    
    BOUNDARY[❌ Privacy Boundary<br/>User Data Never Crosses]
    
    UC -.->|NEVER| GEMINI_CLOUD
    UC -.->|NEVER| UPSTASH_CLOUD
    
    style UC fill:#ffebee
    style OLLAMA_LOCAL fill:#e8f5e9
    style KG_LOCAL fill:#e8f5e9
    style CHROMA_LOCAL fill:#e8f5e9
    style GEMINI_CLOUD fill:#e1f5fe
    style UPSTASH_CLOUD fill:#e1f5fe
    style TTS_CLOUD fill:#e1f5fe
    style BOUNDARY fill:#ffcdd2
```

## Technology Stack Map

```mermaid
mindmap
  root((Cortex Mentor))
    Backend
      Language
        Python 3.12+
      Framework
        FastAPI 0.119
        Uvicorn 0.37
      Task Queue
        ARQ
        Redis 5.0.4
      Data Validation
        Pydantic 2.12
    AI & ML
      Local LLM
        Ollama
        llama3.1:latest
        nomic-embed-text
      Cloud LLM
        Google Gemini
        2.5 Flash
        2.5 Pro
      Agent Framework
        Google ADK 1.16
      Text-to-Speech
        Google Cloud TTS
    Data Storage
      Local Vector DB
        ChromaDB 0.5.4
      Cloud Vector DB
        Upstash Vector
      Knowledge Graph
        Markdown Files
        Zettelkasten Style
    Infrastructure
      Message Bus
        Redis Pub/Sub
      Real-time Comm
        WebSocket
      Configuration
        Pydantic Settings
        Environment Vars
    Frontend
      Platform
        VS Code Extension
      Language
        TypeScript
      Communication
        WebSocket Client
```

---

## Key Architectural Decisions

### 1. Pipeline & Processor Pattern
**Why**: Enables modular, testable, composable processing with clear separation of concerns.

### 2. Hybrid Knowledge Model
**Why**: Maintains privacy (local processing) while leveraging cloud AI for synthesis.

### 3. Parallel Execution
**Why**: Reduces latency by running independent operations concurrently (private + public queries).

### 4. Event-Driven Architecture
**Why**: Decouples event ingestion from processing, enables async workflows.

### 5. Per-Request Agent Instantiation
**Why**: Prevents session state bugs in Google ADK agents.

---

## Scaling Considerations

| Component | Current State | Scaling Strategy |
|-----------|---------------|------------------|
| **API Gateway** | Single FastAPI instance | Horizontal scaling behind load balancer |
| **Redis** | Single instance | Redis Cluster for HA |
| **ARQ Workers** | Single worker | Multiple workers with queue partitioning |
| **ChromaDB** | Embedded local DB | Migrate to Chroma Cloud for distributed access |
| **WebSocket** | In-process | Separate WebSocket server with Redis adapter |

---

## Deployment Architecture (Future State)

```mermaid
graph TB
    LB[Load Balancer]
    
    subgraph "API Layer"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N]
    end
    
    subgraph "Worker Layer"
        W1[ARQ Worker 1]
        W2[ARQ Worker 2]
        W3[ARQ Worker N]
    end
    
    subgraph "Data Layer"
        REDIS_CLUSTER[(Redis Cluster)]
        CHROMA_CLOUD[(Chroma Cloud)]
        UPSTASH_CLOUD[(Upstash)]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> REDIS_CLUSTER
    API2 --> REDIS_CLUSTER
    API3 --> REDIS_CLUSTER
    
    REDIS_CLUSTER --> W1
    REDIS_CLUSTER --> W2
    REDIS_CLUSTER --> W3
    
    W1 --> CHROMA_CLOUD
    W2 --> CHROMA_CLOUD
    W3 --> CHROMA_CLOUD
    
    W1 --> UPSTASH_CLOUD
    W2 --> UPSTASH_CLOUD
    W3 --> UPSTASH_CLOUD
```
