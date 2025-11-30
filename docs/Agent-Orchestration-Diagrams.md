# Agent Orchestration Diagrams

## Multi-Agent System Overview

```mermaid
graph TB
    subgraph "Agent Types"
        LLM[LlmAgent<br/>Single-purpose reasoning]
        SEQ[SequentialAgent<br/>Orchestrates sub-agents<br/>in sequence]
        PAR[ParallelAgent<br/>Orchestrates sub-agents<br/>in parallel]
    end
    
    subgraph "Agent Lifecycle"
        INST[Instantiate per-request<br/>🔴 CRITICAL]
        EXEC[Execute with prompt]
        SESS[Session events tracked]
        RESP[Extract final response]
        DEST[Agent destroyed]
    end
    
    subgraph "Tools & Callbacks"
        FUNC[FunctionTool<br/>Python functions as tools]
        SEARCH[Google Search Tool<br/>via ADK]
        CALLBACK[before_model_callback<br/>Modify request dynamically]
    end
    
    LLM --> INST
    SEQ --> INST
    PAR --> INST
    
    INST --> EXEC
    EXEC --> SESS
    SESS --> RESP
    RESP --> DEST
    
    LLM -.->|Can have| FUNC
    LLM -.->|Can have| SEARCH
    LLM -.->|Can have| CALLBACK
    
    style INST fill:#ffcdd2
    style DEST fill:#c8e6c9
```

## Curation Agent Hierarchy

```mermaid
graph TD
    ROOT[SequentialAgent<br/>curation_agent]
    
    SEARCH[create_google_search_agent<br/>Web Search Agent<br/>Model: Gemini Flash]
    
    PARA[ParallelAgent<br/>parallel_analyzer]
    
    SEC[LlmAgent<br/>security_analyst<br/>Analyzes security implications<br/>Model: Gemini Flash]
    
    BP[LlmAgent<br/>best_practices_analyst<br/>Analyzes dev best practices<br/>Model: Gemini Flash]
    
    EDITOR[LlmAgent<br/>chief_editor<br/>Synthesizes all findings<br/>Model: Gemini Pro<br/>Tool: UpstashWriterTool]
    
    CALLBACK[before_model_callback<br/>Extracts session events<br/>Renders chief_editor.jinja2<br/>Modifies LLM request]
    
    TOOL[FunctionTool<br/>UpstashWriterTool<br/>Writes to Upstash DB]
    
    ROOT -->|Step 1| SEARCH
    ROOT -->|Step 2| PARA
    ROOT -->|Step 3| EDITOR
    
    PARA -->|Parallel 1| SEC
    PARA -->|Parallel 2| BP
    
    EDITOR -.->|Uses| CALLBACK
    EDITOR -.->|Has| TOOL
    
    style ROOT fill:#e1f5fe
    style PARA fill:#f3e5f5
    style EDITOR fill:#fff9c4
```

## Agent Execution Flow - SequentialAgent

```mermaid
sequenceDiagram
    participant Caller as CurationProcessor
    participant Runner as run_standalone_agent()
    participant Root as SequentialAgent<br/>curation_agent
    participant Agent1 as Web Search Agent
    participant Agent2 as ParallelAgent
    participant Agent3 as Chief Editor
    participant Session as Session Events
    participant Model as Gemini LLM
    
    Caller->>Runner: run_standalone_agent(<br/>curation_agent,<br/>query_text,<br/>target_agent="chief_editor")
    
    Runner->>Runner: Create Session
    Runner->>Root: execute(query_text, session)
    
    Note over Root: Sequential Execution
    
    Root->>Agent1: Execute web search
    Agent1->>Model: Search query via<br/>Google Search Tool
    Model-->>Agent1: Search results
    Agent1->>Session: Record event with results
    Agent1-->>Root: Response
    
    Root->>Agent2: Execute parallel analysis
    
    Note over Agent2: Parallel Execution
    
    par Security Analysis
        Agent2->>Agent2: Security Analyst
        Agent2->>Model: Analyze security
        Model-->>Agent2: Security findings
        Agent2->>Session: Record event
    and Best Practices Analysis
        Agent2->>Agent2: Best Practices Analyst
        Agent2->>Model: Analyze best practices
        Model-->>Agent2: BP findings
        Agent2->>Session: Record event
    end
    
    Agent2-->>Root: Combined results
    
    Root->>Agent3: Execute chief editor
    Agent3->>Agent3: before_model_callback
    Agent3->>Session: Read all previous events
    Session-->>Agent3: Web search + analyses
    Agent3->>Agent3: Render prompt template<br/>with all findings
    Agent3->>Model: Synthesize knowledge<br/>(Modified request)
    Model-->>Agent3: Synthesized knowledge
    Agent3->>Agent3: UpstashWriterTool called<br/>by model
    Agent3->>Agent3: Write to Upstash
    Agent3->>Session: Record final event
    Agent3-->>Root: Final response
    
    Root-->>Runner: Session complete
    Runner->>Runner: Extract final response<br/>from target_agent
    Runner-->>Caller: Synthesized knowledge
```

## KnowledgeGatewayProcessor Agent Pattern

```mermaid
flowchart TD
    START([KnowledgeGatewayProcessor<br/>.process called])
    
    DATA[Receive data:<br/>query_text<br/>public_results]
    
    SANITIZE[Sanitize public results<br/>Remove / and newlines]
    
    INST[🔴 INSTANTIATE AGENT<br/>Per-Request!<br/>LlmAgent with<br/>GatewayDecision schema]
    
    PROMPT[Render prompt:<br/>knowledge_gateway.jinja2<br/>with query + context]
    
    RUN[run_standalone_agent(<br/>gateway_agent, prompt)]
    
    SESSION[Agent creates session]
    MODEL[Call Gemini Flash]
    STRUCT[Return structured JSON<br/>per GatewayDecision schema]
    
    PARSE{Valid JSON?}
    
    VALIDATE[Parse with Pydantic:<br/>GatewayDecision.model_validate_json]
    
    FALLBACK[Fallback parsing:<br/>Check for 'true' or<br/>'NEEDS_IMPROVEMENT']
    
    RESULT[decision: bool]
    
    UPDATE[Update data:<br/>data['needs_improvement'] = decision]
    
    RETURN([Return data])
    
    START --> DATA
    DATA --> SANITIZE
    SANITIZE --> INST
    
    Note1[Why per-request?<br/>Prevents session state<br/>from previous requests<br/>bleeding into current one]
    INST -.-> Note1
    
    INST --> PROMPT
    PROMPT --> RUN
    RUN --> SESSION
    SESSION --> MODEL
    MODEL --> STRUCT
    STRUCT --> PARSE
    
    PARSE -->|Yes| VALIDATE
    PARSE -->|No| FALLBACK
    
    VALIDATE --> RESULT
    FALLBACK --> RESULT
    
    RESULT --> UPDATE
    UPDATE --> RETURN
    
    style INST fill:#ffcdd2
    style Note1 fill:#fff9c4
```

## Structured Output Pattern

```mermaid
classDiagram
    class GatewayDecision {
        <<Pydantic BaseModel>>
        +needs_improvement: bool
    }
    
    class LlmAgent {
        +name: str
        +instruction: str
        +model: str
        +output_schema: BaseModel
        +tools: List
        +before_model_callback: Callable
    }
    
    class Session {
        +events: List[Event]
        +add_event()
        +get_final_response()
    }
    
    class Event {
        +author: str
        +content: Content
        +is_final_response(): bool
    }
    
    class Content {
        +parts: List[Part]
    }
    
    class Part {
        +text: str
    }
    
    LlmAgent --> GatewayDecision : output_schema
    LlmAgent --> Session : creates
    Session --> Event : contains
    Event --> Content : has
    Content --> Part : has
    
    note for LlmAgent "output_schema forces<br/>model to return JSON<br/>matching Pydantic schema"
    
    note for Session "Session tracks all<br/>agent interactions<br/>for context"
```

## Agent Session State Bug (Fixed)

```mermaid
sequenceDiagram
    participant Req1 as Request 1
    participant Bad as ❌ BAD: Agent in __init__
    participant Req2 as Request 2
    participant Good as ✅ GOOD: Agent per-request
    participant Req3 as Request 3
    
    Note over Bad: Agent created once<br/>in processor __init__
    
    Req1->>Bad: process(data1)
    Bad->>Bad: Agent has session1
    Bad->>Bad: Session1: "Python security"
    Bad-->>Req1: Response with context
    
    Req2->>Bad: process(data2)
    Bad->>Bad: REUSES SAME AGENT!
    Bad->>Bad: Session still has:<br/>"Python security" + new data
    Bad-->>Req2: ❌ WRONG: Context leaked!
    
    Note over Good: Agent created fresh<br/>in each .process() call
    
    Req1->>Good: process(data1)
    Good->>Good: Create new agent
    Good->>Good: Fresh session: "Python security"
    Good->>Good: Destroy agent
    Good-->>Req1: Response
    
    Req3->>Good: process(data2)
    Good->>Good: Create new agent
    Good->>Good: Fresh session: "JavaScript testing"
    Good->>Good: Destroy agent
    Good-->>Req3: ✅ CORRECT: No context leak!
    
    style Bad fill:#ffcdd2
    style Good fill:#c8e6c9
```

## Code Fix Pattern

### ❌ BEFORE (Session State Bug)

```python
class KnowledgeGatewayProcessor(Processor):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        # ❌ BAD: Agent created once, session persists
        self.gateway_agent = LlmAgent(
            name="knowledge_gateway_agent",
            instruction=self.prompt_manager.render("knowledge_gateway.jinja2"),
            output_schema=GatewayDecision,
            model=self.llm_service.settings.gemini_flash_model,
        )
    
    async def process(self, data: dict, context: dict) -> dict:
        # Agent is reused across requests
        result = await run_standalone_agent(self.gateway_agent, prompt)
        # Previous request's context bleeds into this one!
```

### ✅ AFTER (Fixed)

```python
class KnowledgeGatewayProcessor(Processor):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        # ✅ GOOD: No agent instantiation here
    
    async def process(self, data: dict, context: dict) -> dict:
        # ✅ Create fresh agent for each request
        gateway_agent = LlmAgent(
            name="knowledge_gateway_agent",
            instruction=self.prompt_manager.render("knowledge_gateway.jinja2"),
            output_schema=GatewayDecision,
            model=self.llm_service.settings.gemini_flash_model,
        )
        
        result = await run_standalone_agent(gateway_agent, prompt)
        # Agent destroyed after request, no state leakage
```

## Tool Function Pattern

```mermaid
flowchart TD
    START([Define Python Function])
    
    ASYNC[async def UpstashWriterTool<br/>data: str -> str]
    
    DOC[Docstring describes<br/>what tool does<br/>for LLM to understand]
    
    LOGIC[Implement logic:<br/>await upstash_writer.write(data)]
    
    NAME[Set __name__ attribute:<br/>UpstashWriterTool.__name__ = 'write']
    
    WRAP[Wrap in FunctionTool:<br/>FunctionTool(func=UpstashWriterTool)]
    
    ATTACH[Attach to LlmAgent:<br/>tools=[FunctionTool(...)]]
    
    MODEL[LLM decides when to call tool]
    CALL[ADK framework calls<br/>Python function]
    RESULT[Return string result<br/>back to LLM]
    CONTINUE[LLM continues with result]
    
    START --> ASYNC
    ASYNC --> DOC
    DOC --> LOGIC
    LOGIC --> NAME
    NAME --> WRAP
    WRAP --> ATTACH
    
    ATTACH --> MODEL
    MODEL -->|Needs tool| CALL
    CALL --> RESULT
    RESULT --> CONTINUE
    
    style CALL fill:#c8e6c9
```

## Callback Mechanism - Dynamic Prompt Injection

```mermaid
sequenceDiagram
    participant Agent as LlmAgent<br/>chief_editor
    participant Callback as before_model_callback
    participant Context as CallbackContext
    participant Session as Session Events
    participant Request as LlmRequest
    participant Template as Jinja2 Template
    participant Model as Gemini Pro
    
    Note over Agent: Agent.execute() called
    
    Agent->>Callback: Invoke before model call
    Callback->>Context: Access callback_context
    Context->>Session: Get session.events
    Session-->>Callback: All previous events
    
    Callback->>Callback: Extract results from events:<br/>- Web search results<br/>- Security analysis<br/>- Best practices analysis
    
    Callback->>Template: Render chief_editor.jinja2<br/>with extracted data
    Template-->>Callback: Rendered prompt
    
    Callback->>Request: Modify llm_request.contents<br/>Replace with new prompt
    Request-->>Callback: Modified
    
    Callback-->>Agent: Return (modified request)
    
    Agent->>Model: Call with modified prompt
    Model-->>Agent: LLM response
    
    Note over Agent: Response includes<br/>synthesized knowledge<br/>from all sources
```

## run_standalone_agent Utility

```mermaid
flowchart TD
    START([run_standalone_agent<br/>agent, prompt, target_agent])
    
    SESSION[Create ADK Session]
    
    EXEC[agent.execute(<br/>user_prompt=prompt,<br/>session=session)]
    
    AWAIT[Await completion]
    
    TARGET{target_agent<br/>specified?}
    
    FIND[Find target agent's<br/>final response in<br/>session.events]
    
    DEFAULT[Get agent's final response<br/>from session]
    
    EXTRACT[Extract text from<br/>response.content.parts]
    
    CLEAN[Strip whitespace]
    
    RETURN([Return response string])
    
    START --> SESSION
    SESSION --> EXEC
    EXEC --> AWAIT
    AWAIT --> TARGET
    
    TARGET -->|Yes| FIND
    TARGET -->|No| DEFAULT
    
    FIND --> EXTRACT
    DEFAULT --> EXTRACT
    
    EXTRACT --> CLEAN
    CLEAN --> RETURN
    
    style SESSION fill:#e1f5fe
    style EXTRACT fill:#fff9c4
```

## Agent Best Practices

### 1. Always Instantiate Per-Request

```python
# ❌ WRONG
class MyProcessor:
    def __init__(self):
        self.agent = LlmAgent(...)  # Created once
    
    async def process(self, data, context):
        await run_standalone_agent(self.agent, prompt)

# ✅ CORRECT
class MyProcessor:
    def __init__(self):
        pass  # No agent here
    
    async def process(self, data, context):
        agent = LlmAgent(...)  # Created fresh
        await run_standalone_agent(agent, prompt)
```

### 2. Use Structured Output for Parsing

```python
# Define Pydantic schema
class MyDecision(BaseModel):
    should_proceed: bool
    confidence: float
    reasoning: str

# Agent with output schema
agent = LlmAgent(
    name="decision_maker",
    instruction="Evaluate and decide...",
    output_schema=MyDecision,  # Forces JSON output
    model="gemini-2.5-flash"
)

# Parse response
result = await run_standalone_agent(agent, prompt)
decision = MyDecision.model_validate_json(result)
```

### 3. Extract Multi-Agent Results via Session Events

```python
async def callback(callback_context: CallbackContext, llm_request: LlmRequest):
    results = {}
    
    for event in callback_context.session.events:
        # Check which agent produced this event
        if event.author == "web_searcher" and event.is_final_response():
            results["search"] = extract_text(event.content.parts)
        
        if event.author == "analyst" and event.is_final_response():
            results["analysis"] = extract_text(event.content.parts)
    
    # Use results to modify request
    prompt = template.render(**results)
    llm_request.contents = [types.Content(parts=[types.Part(text=prompt)])]
```

### 4. Prevent Duplicate Tool Calls

```python
class MyWriter:
    def __init__(self):
        self._has_written = False
    
    async def write(self, data: str) -> str:
        if self._has_written:
            return "Already written, terminating."
        
        await actual_write(data)
        self._has_written = True
        return "Success"
```

---

## Agent Execution Metrics

| Agent Type | Typical Latency | Model Used | Purpose |
|------------|----------------|------------|---------|
| **Web Search Agent** | 2-5s | Gemini Flash | Fast web searches |
| **Security Analyst** | 1-3s | Gemini Flash | Quick security checks |
| **Best Practices Analyst** | 1-3s | Gemini Flash | Quick pattern analysis |
| **Chief Editor** | 3-8s | Gemini Pro | Complex synthesis |
| **Knowledge Gateway** | 1-2s | Gemini Flash | Quality evaluation |

**Total Curation Pipeline**: ~8-20 seconds (sequential + parallel)
