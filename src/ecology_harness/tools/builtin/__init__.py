from ecology_harness.tools.builtin.agent_tools import register_agent_tools
from ecology_harness.tools.builtin.browser_tools import register_browser_tools
from ecology_harness.tools.builtin.claw_tools import register_claw_compat_tools
from ecology_harness.tools.builtin.document_tools import register_document_tools
from ecology_harness.tools.builtin.ecology_tools import register_ecology_tools
from ecology_harness.tools.builtin.evolution_tools import register_evolution_tools
from ecology_harness.tools.builtin.file_tools import register_file_tools
from ecology_harness.tools.builtin.integration_tools import register_integration_tools
from ecology_harness.tools.builtin.memory_tools import register_memory_tools
from ecology_harness.tools.builtin.mcp_tools import register_mcp_tools
from ecology_harness.tools.builtin.plugin_tools import register_plugin_tools
from ecology_harness.tools.builtin.runtime_tools import register_runtime_tools
from ecology_harness.tools.builtin.skill_tools import register_skill_tools
from ecology_harness.tools.builtin.system_tools import register_system_tools
from ecology_harness.tools.builtin.task_tools import register_task_tools
from ecology_harness.tools.builtin.search_tools import register_search_tools
from ecology_harness.tools.builtin.web_tools import register_web_tools
from ecology_harness.tools.builtin.workspace_tools import register_workspace_tools
from ecology_harness.tools.registry import ToolRegistry


def register_builtin_tools(registry: ToolRegistry) -> None:
    register_file_tools(registry)
    register_document_tools(registry)
    register_search_tools(registry)
    register_web_tools(registry)
    register_browser_tools(registry)
    register_ecology_tools(registry)
    register_evolution_tools(registry)
    register_integration_tools(registry)
    register_memory_tools(registry)
    register_skill_tools(registry)
    register_task_tools(registry)
    register_system_tools(registry)
    register_runtime_tools(registry)
    register_workspace_tools(registry)
    register_agent_tools(registry)
    register_plugin_tools(registry)
    register_mcp_tools(registry)
    register_claw_compat_tools(registry)
