---
name: mud-player
description: Connect to and play the local TBAMUD/DikuMUD-style MUD server running at localhost:4000. Use this when the user wants to log in, explore rooms, or issue in-game commands (look, move, inventory, score, say, etc.) on the local MUD.
---

# MUD Player

Helps you interact with the MUD (Multi-User Dungeon) game server running locally on `localhost:4000`. It uses the `mud_client.py` script in this same folder to connect over raw telnet/TCP, log in, run one or more in-game commands, and print the game's response.

## Connection details

- Host: `localhost`
- Port: `4000`
- Protocol: plain TCP/telnet (no TLS). The server sends some telnet IAC negotiation bytes and ANSI color codes; `mud_client.py` strips both by default for readability.

## Credentials

- Username: `dummy`
- Password: `helloworld`

These are already the defaults baked into `mud_client.py`, so you normally don't need to pass them explicitly.

## Login flow (handled automatically by the script)

1. Connect to `localhost:4000`.
2. Server prompts `By what name do you wish to be known?` -> send username.
3. Server prompts `Password:` -> send password.
4. Server shows a welcome banner and `*** PRESS RETURN:` -> send an empty line.
5. Server shows the main menu (`0) Exit`, `1) Enter the game`, etc.) -> send `1` to enter the game.
6. Server shows the current room description and the game prompt, e.g. `24H 100M 83V (news) (motd) > `, ready for commands.

Note: sending `quit` while in the game returns to the main menu, not a hard disconnect. `mud_client.py` sends `quit` by default at the end of a session to leave the character in a clean state, then closes the socket.

## Usage

Run the script directly to log in and issue commands:

```bash
python3 mud_client.py "look"
python3 mud_client.py "look" "inventory" "score"
```

Each positional argument is a separate in-game command sent in order. Output for the login sequence and each command is printed under clearly labeled sections (`=== LOGIN ===`, `=== > look ===`, etc.).

### Useful flags

- `--host`, `--port` - override connection target (defaults: `localhost`, `4000`).
- `--username`, `--password` - override credentials (defaults: `dummy`, `helloworld`).
- `--raw` - keep ANSI color escape codes in the output instead of stripping them.
- `--no-quit` - don't send `quit` before disconnecting (leaves the character in the game/menu state server-side; the TCP connection still closes).

### Examples

Log in and just look around:
```bash
python3 mud_client.py "look"
```

Move around and check status:
```bash
python3 mud_client.py "north" "look" "score"
```

Log in only, without sending any game command (still sends `quit` to return to the menu before disconnecting unless `--no-quit` is passed):
```bash
python3 mud_client.py
```

## Persistent Memory System

The skill maintains two markdown files in the `data/` folder to track long-term progress and goals:

### `data/player.md`

Tracks character state, experience, learned skills, and goals:

```markdown
# Player: Dummy

## Current Status
- **Level**: 1
- **Experience**: 1 / 1999 (need 1999 for level 2)
- **Health**: 24/24
- **Mana**: 100/100
- **Movement**: 61/83
- **Class**: Swordsman
- **Location**: Tournament And Practice Yard (Guild of Swordsmen)

## Skills Learned
- [ ] kick (practiced)
- [ ] slash
- [ ] parry

## Long-Term Goals
- [ ] Reach level 7
- [ ] Defeat [specific monster name/location]
- [ ] [other objectives]

## Session Log
- Session 1: Explored Midgaard, found Bakery menu, joined Swordsmen's guild, practiced kick
```

### `data/world.md`

Tracks discovered locations, NPCs, shops, and monsters:

```markdown
# World: Midgaard

## Known Locations
- Temple of Midgaard (starting point)
- Market Square (hub)
- The Bakery (north off west Main Street) - sells danish (7g), bread (15g), waybread (76g)
- Guild of Swordsmen - Tournament and Practice Yard (guildmaster here)
- Armory
- Weapon Shop
- General Store
- Pet Shop
- Magic Users' Guild

## Monsters Encountered
- Fido (beastly, garbage areas)
- [specific monster target]

## NPCs
- Guildmaster (Swordsmen's guild)
- The baker (bakery)
- Mayor
- Armorer
- Various cityguards and peacekeepers

## Items/Resources Found
- Gold coins: 0
- Quest points: 0
```

### How Memory Works

1. **Before logging in**: Read `data/player.md` and `data/world.md` to understand current goals and known world state
2. **During play**: Use the knowledge to guide decisions (e.g., "we're trying to reach level 7, so fight enemies for exp")
3. **After play session**: Update both files with new discoveries, exp gained, skills learned, progress toward goals

### Usage with Long-Term Goals

To pursue a multi-session goal like "reach level 7 and defeat a specific monster":

```bash
# See current goal state
cat data/player.md

# Run a session focused on leveling
python3 mud_client.py "say I seek experience to grow stronger" "kill goblin"

# After session, update memory files with progress
# (agent does this automatically)
```

## When issuing commands on the user's behalf

- Chain related commands in a single invocation (one process = one login session) rather than reconnecting for every command, since each connection re-runs the full login handshake.
- If a command's output suggests further action is needed (e.g., combat, a locked door, a prompt for confirmation), pass the appropriate follow-up command in the same invocation when it's predictable, or ask the user before guessing at destructive/irreversible in-game actions (e.g., deleting the character, giving away items).
- If the server output doesn't look like a normal MUD response (e.g., connection refused), report that the MUD server may not be running on `localhost:4000` rather than retrying blindly.
- **Reference persistent memory files** before each session to understand prior progress and current goals, using them to guide strategy and combat decisions toward long-term objectives.
- **Update memory files** after each significant session to record exp gains, new skills learned, monster defeats, and location discoveries.
