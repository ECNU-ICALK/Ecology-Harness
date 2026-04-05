from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClawCompatTool:
    name: str
    description: str
    source_hint: str
    availability: str
    mapped_tool: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "source_hint": self.source_hint,
            "availability": self.availability,
            "mapped_tool": self.mapped_tool,
        }


CLAW_COMPAT_TOOLS: tuple[ClawCompatTool, ...] = (
    ClawCompatTool(
        name="AgentTool",
        description="Compatibility wrapper for delegated subagent work.",
        source_hint="tools/AgentTool/AgentTool.tsx",
        availability="native_alias",
        mapped_tool="Agent",
    ),
    ClawCompatTool(
        name="AskUserQuestionTool",
        description="Collect a user-facing clarification prompt when the model is blocked.",
        source_hint="tools/AskUserQuestionTool/AskUserQuestionTool.tsx",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="BashTool",
        description="Compatibility alias for shell execution.",
        source_hint="tools/BashTool/BashTool.tsx",
        availability="native_alias",
        mapped_tool="Bash",
    ),
    ClawCompatTool(
        name="BriefTool",
        description="Compose a compact brief from objective, context, and constraints.",
        source_hint="tools/BriefTool/BriefTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="ConfigTool",
        description="Inspect or update selected runtime settings.",
        source_hint="tools/ConfigTool/ConfigTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="EnterPlanModeTool",
        description="Switch the harness into plan mode guidance.",
        source_hint="tools/EnterPlanModeTool/EnterPlanModeTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="ExitPlanModeV2Tool",
        description="Exit plan mode and return to default execution guidance.",
        source_hint="tools/ExitPlanModeTool/ExitPlanModeV2Tool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="FileEditTool",
        description="Compatibility wrapper for file edits.",
        source_hint="tools/FileEditTool/FileEditTool.ts",
        availability="native_alias",
        mapped_tool="Edit",
    ),
    ClawCompatTool(
        name="FileReadTool",
        description="Compatibility wrapper for reading text files.",
        source_hint="tools/FileReadTool/FileReadTool.ts",
        availability="native_alias",
        mapped_tool="Read",
    ),
    ClawCompatTool(
        name="GlobTool",
        description="Compatibility alias for workspace globbing.",
        source_hint="tools/GlobTool/GlobTool.ts",
        availability="native_alias",
        mapped_tool="Glob",
    ),
    ClawCompatTool(
        name="GrepTool",
        description="Compatibility alias for workspace regex search.",
        source_hint="tools/GrepTool/GrepTool.ts",
        availability="native_alias",
        mapped_tool="Grep",
    ),
    ClawCompatTool(
        name="ListDirectoryTool",
        description="List directory entries with optional recursion.",
        source_hint="tools/ListDirectoryTool/ListDirectoryTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="ListMcpResourcesTool",
        description="List resources published by an MCP server.",
        source_hint="tools/ListMcpResourcesTool/ListMcpResourcesTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="MCPTool",
        description="Call a specific tool exposed by an MCP server.",
        source_hint="tools/MCPTool/MCPTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="McpAuthTool",
        description="Inspect whether an MCP server needs user authentication.",
        source_hint="tools/McpAuthTool/McpAuthTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="MemoryReadTool",
        description="Compatibility alias for durable memory reads.",
        source_hint="tools/MemoryReadTool/MemoryReadTool.ts",
        availability="native_alias",
        mapped_tool="MemoryRead",
    ),
    ClawCompatTool(
        name="MemoryWriteTool",
        description="Compatibility alias for durable memory writes.",
        source_hint="tools/MemoryWriteTool/MemoryWriteTool.ts",
        availability="native_alias",
        mapped_tool="MemorySave",
    ),
    ClawCompatTool(
        name="ReadMcpResourceTool",
        description="Read one MCP resource by URI.",
        source_hint="tools/ReadMcpResourceTool/ReadMcpResourceTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="SkillTool",
        description="Compatibility alias for running a named skill.",
        source_hint="tools/SkillTool/SkillTool.ts",
        availability="native_alias",
        mapped_tool="Skill",
    ),
    ClawCompatTool(
        name="TodoWriteTool",
        description="Create or update tracked tasks from a compact todo list.",
        source_hint="tools/TodoWriteTool/TodoWriteTool.ts",
        availability="native_impl",
    ),
    ClawCompatTool(
        name="WebFetchTool",
        description="Compatibility alias for fetching a URL.",
        source_hint="tools/WebFetchTool/WebFetchTool.ts",
        availability="native_alias",
        mapped_tool="WebFetch",
    ),
    ClawCompatTool(
        name="WebSearchTool",
        description="Compatibility alias for lightweight web search.",
        source_hint="tools/WebSearchTool/WebSearchTool.ts",
        availability="native_alias",
        mapped_tool="WebSearch",
    ),
)


CLAW_SKILL_SPECS: tuple[dict[str, str], ...] = (
    {
        "slug": "remember",
        "name": "remember",
        "description": "Capture durable user or project context in memory only when it will matter later.",
    },
    {
        "slug": "verify",
        "name": "verify",
        "description": "Run the smallest high-signal verification steps before concluding work.",
    },
    {
        "slug": "stuck",
        "name": "stuck",
        "description": "Recover from blockers by restating the obstacle and shrinking the next action.",
    },
    {
        "slug": "batch",
        "name": "batch",
        "description": "Group read-only discovery into compact batches before acting.",
    },
    {
        "slug": "loop",
        "name": "loop",
        "description": "Keep executing the current plan until the visible stop condition is met.",
    },
    {
        "slug": "update-config",
        "name": "update-config",
        "description": "Inspect and safely adjust runtime configuration.",
    },
)


def list_claw_tools() -> list[ClawCompatTool]:
    return list(CLAW_COMPAT_TOOLS)


def get_claw_tool(name: str) -> ClawCompatTool | None:
    needle = (name or "").strip().lower()
    for item in CLAW_COMPAT_TOOLS:
        if item.name.lower() == needle:
            return item
    return None


def search_claw_tools(query: str, limit: int = 20) -> list[ClawCompatTool]:
    needle = (query or "").strip().lower()
    if not needle:
        return list(CLAW_COMPAT_TOOLS[:limit])
    matches = []
    for item in CLAW_COMPAT_TOOLS:
        if needle in item.name.lower() or needle in item.source_hint.lower():
            matches.append(item)
    return matches[:limit]
