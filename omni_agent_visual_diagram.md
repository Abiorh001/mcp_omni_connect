# OmniAgent System Architecture & Flow

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OmniAgent System                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │   User Input    │    │  OmniAgent      │    │   Response Output       │  │
│  │                 │    │  (Orchestrator) │    │                         │  │
│  │ "Calculate area │───▶│                 │───▶│ "The area is 24 sq ft"  │  │
│  │  of 6x4 rect"   │    │                 │    │                         │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
│           │                       │                       │                  │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  Session Store  │    │  Tool Registry  │    │   Memory Router         │  │
│  │  (Chat History) │    │                 │    │                         │  │
│  │                 │    │  ┌─────────────┐│    │  ┌─────────────────────┐│  │
│  │ • Chat ID       │    │  │ Local Tools ││    │  │ In-Memory Store     ││  │
│  │ • Messages      │    │  │             ││    │  │                     ││  │
│  │ • Context       │    │  │ • calculate_││    │  │ • Episodic Memory   ││  │
│  │                 │    │  │   area      ││    │  │ • Working Memory    ││  │
│  └─────────────────┘    │  │ • get_weather││    │  │ • Token Budget      ││  │
│                         │  │ • format_text││    │  │                     ││  │
│                         │  └─────────────┘│    │  └─────────────────────┘│  │
│                         │                 │    │                         │  │
│                         │  ┌─────────────┐│    │  ┌─────────────────────┐│  │
│                         │  │ MCP Tools   ││    │  │ File System MCP     ││  │
│                         │  │             ││    │  │                     ││  │
│                         │  │ • filesystem││    │  │ • Read/Write Files  ││  │
│                         │  │ • webcam    ││    │  │ • Directory Listing ││  │
│                         │  │ • etc.      ││    │  │ • File Operations   ││  │
│                         │  └─────────────┘│    │  └─────────────────────┘│  │
│                         └─────────────────┘    └─────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Detailed Flow Process

### 1. **Initialization Phase**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INITIALIZATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Create Local Tools Registry                                            │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │ @local_tools.register_tool(                                         │ │
│     │     name="calculate_area",                                          │ │
│     │     description="Calculate area of rectangle",                      │ │
│     │     inputSchema={...}                                               │ │
│     │ )                                                                   │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  2. Configure OmniAgent                                                    │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │ agent = OmniAgent(                                                  │ │
│     │     name="session_agent",                                           │ │
│     │     system_instruction="You are a helpful assistant...",            │ │
│     │     agent_config={...},                                             │ │
│     │     model_config={...},                                             │ │
│     │     mcp_tools=[...],                                                │ │
│     │     local_tools=local_tools,                                        │ │
│     │     memory_store=custom_memory                                      │ │
│     │ )                                                                   │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. **Request Processing Flow**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REQUEST PROCESSING FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User: "Calculate area of 6x4 rectangle"                                   │
│                                                                             │
│  ┌─────────────────┐                                                       │
│  │   1. PARSING    │                                                       │
│  │                 │                                                       │
│  │ • Extract intent│                                                       │
│  │ • Identify tools│                                                       │
│  │ • Check context │                                                       │
│  └─────────────────┘                                                       │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                       │
│  │  2. TOOL CALL   │                                                       │
│  │                 │                                                       │
│  │ <tool_call>     │                                                       │
│  │   <tool_name>   │                                                       │
│  │     calculate_  │                                                       │
│  │     area        │                                                       │
│  │   </tool_name>  │                                                       │
│  │   <parameters>  │                                                       │
│  │     <length>6   │                                                       │
│  │     </length>   │                                                       │
│  │     <width>4    │                                                       │
│  │     </width>    │                                                       │
│  │   </parameters> │                                                       │
│  │ </tool_call>    │                                                       │
│  └─────────────────┘                                                       │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                       │
│  │ 3. EXECUTION    │                                                       │
│  │                 │                                                       │
│  │ • Validate args │                                                       │
│  │ • Execute func  │                                                       │
│  │ • Return result │                                                       │
│  │   (24.0)        │                                                       │
│  └─────────────────┘                                                       │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                       │
│  │  4. RESPONSE    │                                                       │
│  │                 │                                                       │
│  │ <final_answer>  │                                                       │
│  │ The area of a   │                                                       │
│  │ 6x4 rectangle   │                                                       │
│  │ is 24 square    │                                                       │
│  │ feet.           │                                                       │
│  │ </final_answer> │                                                       │
│  └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. **Memory Management**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEMORY MANAGEMENT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Memory Router                                        │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │ │
│  │  │ Working Memory  │  │ Episodic Memory │  │   Token Budget          │ │ │
│  │  │                 │  │                 │  │                         │ │ │
│  │  │ • Current       │  │ • Past          │  │ • Track token usage     │ │ │
│  │  │   conversation  │  │   interactions  │  │ • Enforce limits        │ │ │
│  │  │ • Tool calls    │  │ • User          │  │ • Optimize context      │ │ │
│  │  │ • Results       │  │   preferences   │  │                         │ │ │
│  │  │ • Context       │  │ • Effective     │  │                         │ │ │
│  │  │                 │  │   strategies    │  │                         │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tool Integration Examples

### Local Tools
```python
# Example: calculate_area tool
@local_tools.register_tool(
    name="calculate_area",
    description="Calculate the area of a rectangle",
    inputSchema={
        "type": "object",
        "properties": {
            "length": {"type": "number"}, 
            "width": {"type": "number"}
        },
        "required": ["length", "width"],
    },
)
def calculate_area(length: float, width: float) -> float:
    return length * width

# Usage in conversation:
# User: "Calculate area of 6x4 rectangle"
# Agent: <tool_call><tool_name>calculate_area</tool_name><parameters><length>6</length><width>4</width></parameters></tool_call>
# Result: 24.0
# Agent: <final_answer>The area is 24 square feet.</final_answer>
```

### MCP Tools
```python
# Example: filesystem MCP tool
mcp_tools=[
    {
        "name": "filesystem",
        "transport_type": "stdio",
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/home/abiorh/Desktop",
            "/home/abiorh/ai/",
        ],
    }
]

# Usage in conversation:
# User: "List files in my Desktop"
# Agent: <tool_call><tool_name>filesystem_list_directory</tool_name><parameters><path>/home/abiorh/Desktop</path></parameters></tool_call>
# Result: ["file1.txt", "document.pdf", "image.jpg"]
# Agent: <final_answer>Your Desktop contains: file1.txt, document.pdf, and image.jpg</final_answer>
```

## 🔧 Configuration Components

### Agent Configuration
```python
agent_config = {
    "max_steps": 20,              # Maximum tool calls per conversation
    "tool_call_timeout": 60,      # Timeout for tool execution
    "request_limit": 1000,        # Maximum requests per session
    "memory_config": {
        "mode": "token_budget",   # Memory management mode
        "value": 10000           # Token budget limit
    },
}
```

### Model Configuration
```python
model_config = {
    "provider": "gemini",         # LLM provider
    "model": "gemini-2.0-flash",  # Specific model
    "max_context_length": 50000,  # Context window size
}
```

## 🎯 Key Features

1. **Unified Tool Interface**: Seamlessly combines local Python functions and MCP tools
2. **XML-Based Communication**: Structured format for tool calls and responses
3. **Session Management**: Persistent conversation history with chat IDs
4. **Memory Management**: Intelligent context management with token budgeting
5. **Error Handling**: Robust error reporting and recovery
6. **Extensible Architecture**: Easy to add new tools and capabilities

## 🔄 Complete Example Flow

```
User Input: "Calculate area of 6x4 rectangle and save result to a file"

1. Parse Request
   ├── Identify tools needed: calculate_area, filesystem_write
   ├── Extract parameters: length=6, width=4
   └── Plan execution order

2. Execute calculate_area
   ├── Tool Call: <tool_call><tool_name>calculate_area</tool_name><parameters><length>6</length><width>4</width></parameters></tool_call>
   ├── Execution: 6 * 4 = 24
   └── Result: 24.0

3. Execute filesystem_write
   ├── Tool Call: <tool_call><tool_name>filesystem_write_file</tool_name><parameters><path>/home/abiorh/Desktop/area_result.txt</path><contents>Area: 24 square feet</contents></tool_call>
   ├── Execution: Write file to Desktop
   └── Result: File created successfully

4. Generate Response
   └── <final_answer>I calculated the area of a 6x4 rectangle, which is 24 square feet. I've also saved this result to a file called 'area_result.txt' on your Desktop.</final_answer>
```

This visual representation shows how OmniAgent seamlessly integrates multiple tool types, manages memory, and provides a unified interface for complex multi-step tasks. 