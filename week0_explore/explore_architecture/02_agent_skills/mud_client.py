#!/usr/bin/env python3
"""
mud_client.py - Minimal telnet client for the local TBAMUD/DikuMUD server.

Handles the full login sequence (character name -> password -> press-return
-> main menu -> enter game) and then sends one or more game commands,
printing whatever the server responds with.

Usage:
    python3 mud_client.py <command> [<command> ...]
    python3 mud_client.py "look" "inventory" "score"

    # Custom connection / credentials (defaults shown):
    python3 mud_client.py --host localhost --port 4000 \\
        --username dummy --password helloworld "look"

    # Keep raw ANSI color codes in the output instead of stripping them:
    python3 mud_client.py --raw "look"

Exit codes:
    0 on success, 1 on connection/login failure.
"""

import argparse
import os
import re
import socket
import sys
import time
from pathlib import Path

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 4000
DEFAULT_USERNAME = "dummy"
DEFAULT_PASSWORD = "helloworld"

# Memory system paths
DATA_DIR = Path("data")
PLAYER_MEMORY = DATA_DIR / "player.md"
WORLD_MEMORY = DATA_DIR / "world.md"

# Strip ANSI escape sequences (color codes) for cleaner plain-text output.
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Telnet IAC (0xFF) negotiation sequences the server sends. We don't need to
# respond to them for this server to function; we just strip them from
# output so they don't clutter the text.
TELNET_IAC_RE = re.compile(rb"\xff[\xfb\xfc\xfd\xfe]?.", re.DOTALL)


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def read_player_memory():
    """Read player memory file and return its contents."""
    if PLAYER_MEMORY.exists():
        return PLAYER_MEMORY.read_text()
    return None


def read_world_memory():
    """Read world memory file and return its contents."""
    if WORLD_MEMORY.exists():
        return WORLD_MEMORY.read_text()
    return None


def write_player_memory(content):
    """Write to player memory file."""
    ensure_data_dir()
    PLAYER_MEMORY.write_text(content)


def write_world_memory(content):
    """Write to world memory file."""
    ensure_data_dir()
    WORLD_MEMORY.write_text(content)


def strip_telnet_and_ansi(raw: bytes, keep_ansi: bool = False) -> str:
    """Remove telnet IAC negotiation bytes, decode, optionally strip ANSI."""
    # Remove IAC (0xFF) + option negotiation bytes (typically IAC CMD OPT = 3 bytes,
    # but be defensive and just drop the IAC byte and the following byte(s)).
    cleaned = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b == 0xFF:  # IAC
            # IAC WILL/WONT/DO/DONT <option> = 3 bytes total; IAC alone (rare) = 1
            if i + 2 < len(raw) and raw[i + 1] in (0xFB, 0xFC, 0xFD, 0xFE):
                i += 3
            else:
                i += 1
            continue
        cleaned.append(b)
        i += 1

    text = cleaned.decode("utf-8", errors="replace")
    if not keep_ansi:
        text = ANSI_ESCAPE_RE.sub("", text)
    return text


class MudClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=8.0, idle_wait=0.5):
        self.host = host
        self.port = port
        self.timeout = timeout  # overall max seconds to wait for a response
        self.idle_wait = idle_wait  # seconds of silence that means "server is done talking"
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _read_until(self, markers=None) -> bytes:
        """Read from the socket until one of the given byte markers is seen,
        or until the connection goes idle (no new bytes for `idle_wait`
        seconds) when no markers are required, or until the overall
        `timeout` is exceeded.

        The MUD's client-detection negotiation can pause for over a second
        between bursts, so when we're waiting for a specific prompt marker
        we keep reading (ignoring idle timeouts) until it appears or the
        overall deadline passes. When no marker is given (plain command
        output), going idle after receiving data is treated as "done".
        """
        data = b""
        deadline = time.time() + self.timeout
        self.sock.settimeout(self.idle_wait)
        while time.time() < deadline:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                if markers and any(m in data for m in markers):
                    break
            except socket.timeout:
                if not markers and data:
                    break  # no specific marker expected; idle means done
                continue  # still waiting for our marker (or for any data)
        return data

    def send_line(self, line: str):
        self.sock.sendall((line + "\r\n").encode("utf-8"))

    def login(self, username: str, password: str, keep_ansi: bool = False) -> str:
        """Perform the login handshake and return all output up to the game prompt.

        Handles two server paths after the password is accepted:
        - Fresh login: welcome banner -> "*** PRESS RETURN:" -> main menu ->
          send "1" to enter the game.
        - Reconnect (character was already connected, e.g. a previous
          session didn't cleanly quit): server drops straight back into the
          game with a "Reconnecting." message, skipping press-return/menu.
        """
        transcript = []
        game_prompt = b"(motd) >"

        transcript.append(self._read_until(markers=[b"name do you wish"]))
        self.send_line(username)
        transcript.append(self._read_until(markers=[b"Password:"]))

        self.send_line(password)
        after_password = self._read_until(markers=[b"PRESS RETURN", game_prompt])
        transcript.append(after_password)

        if game_prompt in after_password:
            # Reconnected straight into the game; no menu step needed.
            raw = b"".join(transcript)
            return strip_telnet_and_ansi(raw, keep_ansi=keep_ansi)

        self.send_line("")  # press return
        after_return = self._read_until(markers=[b"Make your choice", game_prompt])
        transcript.append(after_return)

        if game_prompt not in after_return:
            self.send_line("1")  # enter the game
            transcript.append(self._read_until(markers=[game_prompt]))

        raw = b"".join(transcript)
        return strip_telnet_and_ansi(raw, keep_ansi=keep_ansi)

    def send_command(self, command: str, keep_ansi: bool = False) -> str:
        self.send_line(command)
        raw = self._read_until(markers=[b"(motd) >"])
        return strip_telnet_and_ansi(raw, keep_ansi=keep_ansi)

    def sleep_and_recover(self, seconds: int = 120, keep_ansi: bool = False) -> str:
        """Send 'sleep', stay connected for `seconds` so server ticks regenerate
        HP/MV/MP, then wake and stand. Returns all output received."""
        transcript = []
        transcript.append(strip_telnet_and_ansi(
            self._read_until(markers=[b"(motd) >"]), keep_ansi=keep_ansi
        ))

        # Go to sleep
        self.send_line("sleep")
        transcript.append(strip_telnet_and_ansi(
            self._read_until(markers=[b"(motd) >"]), keep_ansi=keep_ansi
        ))

        # Stay connected while the server ticks regeneration
        print(f"Sleeping in-game for {seconds} seconds while movement regenerates...")
        start = time.time()
        raw_regen = b""
        self.sock.settimeout(self.idle_wait)
        while time.time() - start < seconds:
            try:
                chunk = self.sock.recv(4096)
                if chunk:
                    raw_regen += chunk
            except socket.timeout:
                pass
        transcript.append(strip_telnet_and_ansi(raw_regen, keep_ansi=keep_ansi))

        # Wake up
        self.send_line("wake")
        transcript.append(strip_telnet_and_ansi(
            self._read_until(markers=[b"(motd) >"]), keep_ansi=keep_ansi
        ))

        # Stand up
        self.send_line("stand")
        transcript.append(strip_telnet_and_ansi(
            self._read_until(markers=[b"(motd) >"]), keep_ansi=keep_ansi
        ))

        return "\n".join(transcript)


def main():
    parser = argparse.ArgumentParser(
        description="Connect to the local MUD, log in, run commands, print output."
    )
    parser.add_argument("commands", nargs="*", help="Game commands to send in sequence, e.g. look, inventory")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--raw", action="store_true", help="Keep ANSI color escape codes in output")
    parser.add_argument("--no-quit", action="store_true", help="Do not send 'quit' before disconnecting")
    parser.add_argument("--show-memory", action="store_true", help="Display current player and world memory and exit")
    parser.add_argument("--recover", action="store_true", help="Sleep in-game for 2 minutes to regenerate HP/MP/MV, then wake and stand")
    args = parser.parse_args()

    # Show memory if requested
    if args.show_memory:
        player_mem = read_player_memory()
        world_mem = read_world_memory()
        
        if player_mem:
            print("=== PLAYER MEMORY ===")
            print(player_mem)
        else:
            print("No player memory yet. Start a session to create it.")
        
        if world_mem:
            print("\n=== WORLD MEMORY ===")
            print(world_mem)
        else:
            print("No world memory yet. Start a session to create it.")
        
        sys.exit(0)

    client = MudClient(host=args.host, port=args.port)
    try:
        client.connect()
    except OSError as e:
        print(f"Failed to connect to {args.host}:{args.port}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        login_output = client.login(args.username, args.password, keep_ansi=args.raw)
        print("=== LOGIN ===")
        print(login_output)

        if args.recover:
            print("\n=== RECOVERING (sleep 2 min) ===")
            print(client.sleep_and_recover(seconds=120, keep_ansi=args.raw))
            print("\n=== SCORE AFTER RECOVERY ===")
            print(client.send_command("score", keep_ansi=args.raw))

        for cmd in args.commands:
            print(f"\n=== > {cmd} ===")
            output = client.send_command(cmd, keep_ansi=args.raw)
            print(output)

        if not args.no_quit:
            print("\n=== > quit ===")
            print(client.send_command("quit", keep_ansi=args.raw))
    finally:
        client.close()


if __name__ == "__main__":
    main()
