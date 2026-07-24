Our MudManager is written in Ruby. In our Bootcamp, Bootcampers want to ouse their own language eg. Java, Python, Rust, Go.

What is the solution?

We have to create wrapper per language
We make MudManager a command line tool, and other languages execute shell commands in their languages
We implement a communication protocol.
We implement MCP as a layer.
Consider that the MudManager is managing the sessions for the Mud.

---

## Technical Exploration Findings

### Current MudManager Architecture

The MudManager is a Ruby gem with two core components:

1. **Session** (`session.rb`) - A long-lived telnet connection manager that:
   - Connects to CircleMUD servers via TCP sockets
   - Runs a background thread to continuously drain the socket into a buffer
   - Strips telnet IAC negotiation bytes (WILL/WONT/DO/DONT sequences)
   - Provides `read_until_quiet`, `read_until`, and `read_until_prompt` for response collection
   - Handles login dance (username → password → menu navigation)
   - Manages thread-safe buffer access with mutex/condition variables

2. **Primitives** (`primitives.rb`) - Stateless command builders that:
   - Validate enum-typed arguments
   - Return `Command` structs with `raw` (the string to send) and metadata
   - Cover all player-facing MUD commands: movement, combat, communication, inventory, magic, shops, etc.

### Evaluation of Options

#### Option 1: Language-Specific Wrappers
**Approach:** Rewrite MudManager's telnet handling and primitives in each target language.

**Pros:**
- Native language idioms and performance
- No external dependencies or IPC overhead
- Type safety in statically-typed languages

**Cons:**
- Significant duplication (2 files × N languages)
- Bug fixes must be applied N times
- Session management is non-trivial (threading, IAC stripping, timeout handling)

**Verdict:** High effort, poor maintainability. Not recommended.

#### Option 2: CLI Tool with Shell Execution
**Approach:** Wrap MudManager as a CLI (`mudmanager connect`, `mudmanager send "look"`, etc.). Other languages spawn shell processes.

**Pros:**
- Single Ruby implementation
- Universal accessibility (anything that can exec processes)
- Simple to understand

**Cons:**
- **Stateful session problem**: The Session class maintains a persistent TCP connection with a background reader thread. CLI invocations are stateless—each call would require reconnecting and re-authenticating, which is impractical for a MUD session where you need to maintain presence.
- Process spawning overhead per command
- Complex state serialization if we try to persist sessions

**Verdict:** Fundamentally incompatible with the stateful session model. Would require a daemon architecture (see Option 3b).

#### Option 3a: Communication Protocol (TCP/Unix Socket Server)
**Approach:** Run MudManager as a persistent daemon that accepts commands over a local socket. Protocol: JSON-RPC, line-delimited JSON, or custom binary.

**Example flow:**
```
Client → Server: {"method": "login", "params": {"user": "bob", "pass": "secret"}}
Server → Client: {"result": "ok", "session_id": "abc123"}
Client → Server: {"method": "send", "session_id": "abc123", "command": "look"}
Server → Client: {"result": "You are in the Temple of Midgaard..."}
```

**Pros:**
- Single Ruby implementation
- Session state lives in the server (solves the stateful problem)
- Any language can connect via TCP/Unix sockets
- Efficient—no process spawning

**Cons:**
- Requires running a separate daemon process
- Custom protocol design and documentation
- Client libraries still needed for ergonomic use (but much simpler than full rewrites)

**Verdict:** Technically sound. Good fit for the problem.

#### Option 3b: CLI + Daemon Hybrid
**Approach:** `mudmanager daemon start` runs a background server. CLI commands talk to the daemon.

```bash
mudmanager daemon start
mudmanager session new --host localhost --port 4000  # returns session_id
mudmanager send --session abc123 "look"
```

Other languages can either:
- Shell out to the CLI
- Connect directly to the daemon socket

**Pros:** Best of both worlds—CLI for scripting, socket for programmatic use.
**Cons:** Additional complexity managing the daemon lifecycle.

#### Option 4: MCP (Model Context Protocol) Layer
**Approach:** Expose MudManager as an MCP server. AI agents can call tools like `mud_send_command`, `mud_read_output`, etc.

**Pros:**
- Native integration with LLM-based agents (Claude, etc.)
- Standardized protocol (JSON-RPC over stdio/HTTP)
- Built-in tool discovery and schema

**Cons:**
- MCP is designed for AI-to-tool communication, not general programmatic use
- Overkill if Bootcampers just want to write a Python/Go agent
- Additional dependency on MCP infrastructure

**Verdict:** Great for AI agent use cases, but may be too specific. Could be offered as an additional layer on top of Option 3.

### Recommendation

**Primary: MCP Server Binary (bundled with the existing gem)**

Since MudManager is already a Ruby gem, the simplest approach is to add an MCP server binary that ships with the gem. No custom protocol needed—MCP already defines JSON-RPC over stdio/SSE.

**Why this is the right answer:**
1. MCP is already JSON-RPC based — we don't need to invent a protocol
2. The gem already handles session management and primitives
3. MCP has client libraries for Python, TypeScript, and others (Bootcampers can use these or the raw protocol)
4. Works directly with LLM-based agents (Claude, etc.) out of the box
5. Single implementation: just a thin adapter exposing existing Ruby code as MCP tools

**Proposed Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    mud_manager gem                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  bin/mud_manager_mcp  (MCP server binary)              │ │
│  │                                                        │ │
│  │  Exposes tools:                                        │ │
│  │   - session_create(host, port)                         │ │
│  │   - session_login(session_id, username, password)      │ │
│  │   - session_send(session_id, command)                  │ │
│  │   - session_read(session_id, timeout)                  │ │
│  │   - session_close(session_id)                          │ │
│  │   - primitive_*(...)  — one tool per primitive         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                 │
│  ┌─────────────┐  ┌───────┴───────┐  ┌─────────────┐       │
│  │  Session 1  │  │   Primitives  │  │  Session N  │       │
│  │  (TCP→MUD)  │  │   (stateless) │  │  (TCP→MUD)  │       │
│  └─────────────┘  └───────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
        ▲ MCP (JSON-RPC over stdio)
        │
┌───────┴───────────────────────────────────────────────────┐
│  Any MCP Client                                           │
│  - Python (mcp library)                                   │
│  - TypeScript (mcp library)                               │
│  - Go/Java/Rust (raw JSON-RPC over stdio)                 │
│  - Claude Desktop / Kiro / other LLM agents               │
└───────────────────────────────────────────────────────────┘
```

**Usage:**

```bash
# Install the gem (already done)
gem install mud_manager

# Start the MCP server (Bootcampers configure their agent to spawn this)
mud_manager_mcp
```

**MCP Client Configuration (e.g., Claude Desktop / mcp_servers.json):**

```json
{
  "mcpServers": {
    "mud_manager": {
      "command": "mud_manager_mcp"
    }
  }
}
```

**Python Agent Example:**

```python
from mcp import Client

async with Client("mud_manager_mcp") as client:
    # Create session
    session = await client.call_tool("session_create", host="localhost", port=4000)
    session_id = session["session_id"]
    
    # Login
    await client.call_tool("session_login", session_id=session_id, username="bob", password="secret")
    
    # Send command using primitive
    await client.call_tool("session_send", session_id=session_id, command="look")
    
    # Read response
    output = await client.call_tool("session_read", session_id=session_id, timeout=2.0)
    print(output["text"])
```

**Implementation Effort:**
- MCP server adapter: ~150-200 lines of Ruby (using a Ruby MCP SDK or raw stdio JSON-RPC)
- Client code: minimal — use existing MCP libraries or raw JSON-RPC

**Ruby MCP Libraries:**
- `mcp-rb` gem exists for building MCP servers in Ruby
- Alternatively, raw implementation is straightforward: read JSON from stdin, write JSON to stdout

**Tool Design:**

| Tool | Parameters | Description |
|------|------------|-------------|
| `session_create` | `host`, `port`, `timeout?` | Connect to MUD, return `session_id` |
| `session_login` | `session_id`, `username`, `password` | Authenticate |
| `session_send` | `session_id`, `command` | Send raw command string |
| `session_send_primitive` | `session_id`, `primitive`, `args` | Build and send a Primitives command |
| `session_read` | `session_id`, `mode?`, `timeout?` | Read output (`quiet`, `prompt`, `drain`) |
| `session_close` | `session_id` | Disconnect |
| `primitives_list` | — | List all available primitives with their parameters |

This approach requires the least new code and gives Bootcampers the most flexibility—they can use any MCP-compatible client or roll their own with basic stdio JSON-RPC.