"""AgentCiv Simulation — MCP Server.

Model Context Protocol server for Claude Code integration.
Allows launching, configuring, monitoring, and intervening in
AI civilisation simulations directly from Claude Code.
"""

from src.mcp.server import mcp, run_server

__all__ = ["mcp", "run_server"]
