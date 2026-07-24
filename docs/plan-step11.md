# Plan: Port Step 10 Changes to Step 11 TUI

## Summary

Step 10 introduced a major architectural change: **MCP (Model Context Protocol) host support**. Instead of bundling tools directly (FileSystem, Shell, Mud), step 10 connects to external MCP servers that provide tools. Step 11 still uses the old direct-tool model and needs these changes ported forward — but carefully, because step 11 has TUI-specific code that step 10 doesn't have.

---

## What Step 10 Has That Step 11 Is Missing

### 1. MCP Host Implementation (NEW FILES)

**Step 10 has these files that step 11 doesn't:**
- `lib/boukensha/mcp/client.rb` — MCP stdio client (spawn server, handshake, call tools)
- `lib/boukensha/tools/mcp.rb` — Registers MCP server tools into the boukensha registry

**Step 11 has these tool files that step 10 removed:**
- `lib/boukensha/tools/mud.rb` — Direct MUD tool implementation (20KB!)
- `lib/boukensha/tools/shell.rb` — Direct shell tool
- `lib/boukensha/tools/file_system.rb` — Direct filesystem tool

### 2. Config Changes (`lib/boukensha/config.rb`)

| Step 10 (new) | Step 11 (old) |
|---------------|---------------|
| `mcp_servers` method (lines 36-60) | `mud_host`, `mud_port`, `mud_username`, `mud_password` methods |

Step 10 replaces the MUD-specific config with a generic `mcp_servers:` block that can configure *any* MCP server.

### 3. Main Module Changes (`lib/boukensha.rb`)

| Aspect | Step 10 | Step 11 |
|--------|---------|---------|
| Lines | 165 | 208 |
| `@quiet` flag | ✅ Has `quiet!`, `loud!`, `quiet?` | ❌ Missing |
| `run()` params | Removed `allowed_commands`, `shell_timeout`, `mud` | Still has them |
| `repl()` params | Removed `allowed_commands`, `shell_timeout`, `mud`, `tui` | Still has them |
| Tool registration | Calls `register_mcp_servers()` | Calls `Tools::FileSystem.register`, `Tools::Shell.register`, `Tools::Mud.register` |
| `repl()` return | Creates `Repl` and calls `.start` directly | Wraps in `Tui.new(repl)` if `tui: true` |
| Requires | `boukensha/tools/mcp` only | `boukensha/tools/file_system`, `shell`, `mud`, `tui` |

### 4. REPL Changes (`lib/boukensha/repl.rb`) — ⚠️ HIGH RISK

This is the tricky part. Both steps modified `repl.rb` for different reasons:

| Feature | Step 10 | Step 11 |
|---------|---------|---------|
| Lines | 127 | 172 |
| `/quiet`, `/loud` commands | ✅ Yes | ❌ No |
| `on_output(&block)` method | ❌ Removed | ✅ Required for TUI |
| `handle_command(input)` public method | ❌ Inlined into `start` | ✅ Required for TUI |
| `banner` method | Private | Public (TUI reads it) |
| `run_turn` method | Private | Public (TUI calls it) |
| `attr_reader :logger, :context, :model, :version` | ❌ No | ✅ Required for TUI |
| Constructor `mud:` param | ❌ Replaced with `servers:` | ✅ Has `mud:` |
| Banner shows | `servers:` status | `mud:` status |

**Risk:** If you copy step 10's `repl.rb` over step 11's, the TUI will break:
- `Tui` calls `repl.on_output { }` — would raise `NoMethodError`
- `Tui` calls `repl.handle_command(input)` — would raise `NoMethodError`
- `Tui` reads `repl.banner`, `repl.logger`, `repl.context` — would fail

### 5. Loader Changes (`lib/boukensha_loader.rb`)

| Step 10 | Step 11 |
|---------|---------|
| Parses `~/.boukensharc` as YAML with `boukensha_path` and `boukensha_dir` keys | Only reads single-line path |
| Sets `BOUKENSHA_DIR` from rc file if not in env | Doesn't support `boukensha_dir` in rc |
| No `--no-tui` handling (no TUI to disable) | Handles `--no-tui` flag |
| No MUD env var handling | Handles `MUD_NAME`, `MUD_HOST`, etc. |

### 6. Gemspec Dependency Changes

| Step 10 | Step 11 |
|---------|---------|
| No `mud_manager` dependency | `spec.add_dependency "mud_manager", "~> 0.1"` |
| No `charm` dependency | `spec.add_dependency "charm"` |

**For step 11 with MCP:** Keep `charm` (needed for TUI), drop `mud_manager` (MUD is now an external MCP server).

---

## Recommended Approach

### ⚠️ DO NOT just copy files from step 10 to step 11

The changes need to be **merged**, not replaced. Here's the safe approach:

### Files to Add (copy directly)
1. `lib/boukensha/mcp/client.rb` — new directory and file
2. `lib/boukensha/tools/mcp.rb` — new file

### Files to Delete
1. `lib/boukensha/tools/mud.rb`
2. `lib/boukensha/tools/shell.rb`
3. `lib/boukensha/tools/file_system.rb`

### Files to Carefully Merge

#### `lib/boukensha/config.rb`
- Add `mcp_servers` method from step 10
- Remove `mud_host`, `mud_port`, `mud_username`, `mud_password` methods

#### `lib/boukensha.rb`
- Add `@quiet`, `quiet!`, `loud!`, `quiet?`
- Remove tool-specific params from `run()` and `repl()`
- Replace direct tool registration with `register_mcp_servers()`
- **Keep** `tui:` parameter and `Tui.new(repl)` wrapping in `repl()`
- Update requires: remove old tools, add `tools/mcp`, **keep** `tui`

#### `lib/boukensha/repl.rb` — MOST CAREFUL
- Add `/quiet` and `/loud` commands
- **Keep** `on_output`, `handle_command`, public `banner`, `run_turn`
- **Keep** `attr_reader :logger, :context, :model, :version`
- Change `mud:` param to `servers:` param
- Update `banner` to show servers instead of MUD status
- Remove `mud_status_string` and `probe_mud` methods

#### `lib/boukensha_loader.rb`
- Add YAML parsing for `boukensha_path`/`boukensha_dir` keys
- Add `BOUKENSHA_DIR` environment variable support from rc
- **Keep** `--no-tui` handling
- Remove MUD env var handling (now handled by MCP server's own env)

#### `boukensha.gemspec`
- Remove `mud_manager` dependency
- **Keep** `charm` dependency

---

## Verification Steps

After merging:

1. **TUI still works:** `bundle exec bin/boukensha` should launch the charm TUI
2. **Plain REPL works:** `bundle exec bin/boukensha --no-tui` should work
3. **MCP servers load:** Configure an MCP server in settings.yaml, verify tools appear
4. **`/quiet` and `/loud` work:** Test in plain REPL mode
5. **No old tool references:** `grep -r "Tools::Mud\|Tools::Shell\|Tools::FileSystem" lib/` returns nothing

---

## Open Questions

1. Does the TUI need to display MCP server status instead of MUD status?
2. Should the TUI's progress line show which MCP server a tool came from?
3. Is there a `docs/plans/floating_artifacts/boukensharc.md` documenting the loader regression? (The other person's plan mentioned this)
