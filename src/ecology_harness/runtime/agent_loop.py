from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.attachments import build_user_message
from ecology_harness.runtime.compaction import CompactionResult, estimate_tokens, maybe_compact_messages
from ecology_harness.runtime.events import Event
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.runtime.providers import BaseProvider, effective_context_limit
from ecology_harness.tools import ToolError


@dataclass
class AgentRunResult:
    final_text: str
    messages: list[ChatMessage] = field(default_factory=list)
    steps: int = 0
    tool_invocations: list[dict[str, Any]] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    compactions: list[dict[str, Any]] = field(default_factory=list)


class AgentLoop:
    def __init__(
        self,
        app: Any,
        provider: BaseProvider,
        allowed_tools: set[str] | None = None,
    ) -> None:
        self.app = app
        self.provider = provider
        self.allowed_tools = allowed_tools

    def run(
        self,
        prompt: str,
        settings: HarnessSettings | None = None,
        system_prompt: str = "",
        conversation: list[ChatMessage] | None = None,
        attachment_paths: list[str] | None = None,
        depth: int = 0,
        event_handler: Callable[[Event], None] | None = None,
    ) -> AgentRunResult:
        active_settings = settings or self.app.settings
        messages = list(conversation or [])
        emitted_events: list[Event] = []
        if not messages or messages[0].role != "system":
            messages.insert(
                0,
                ChatMessage(
                    role="system",
                    content=system_prompt or self.app.build_system_prompt(),
                ),
            )
        messages.append(
            build_user_message(
                prompt,
                attachment_paths=attachment_paths,
                settings=active_settings,
                sandbox=getattr(self.app, "sandbox", None),
            )
        )

        tool_invocations: list[dict[str, Any]] = []
        compactions: list[dict[str, Any]] = []
        final_text = ""
        _emit_event(
            emitted_events,
            event_handler,
            "run_started",
            provider=getattr(self.provider, "name", "unknown"),
            model=active_settings.model,
            max_steps=(
                "unlimited" if active_settings.max_agent_loops <= 0 else active_settings.max_agent_loops
            ),
            depth=depth,
        )
        step = 0
        while active_settings.max_agent_loops <= 0 or step < active_settings.max_agent_loops:
            step += 1
            context_limit = effective_context_limit(active_settings)
            _emit_event(
                emitted_events,
                event_handler,
                "step_started",
                step=step,
            )
            checkpoint_manager = getattr(self.app, "checkpoint_manager", None)
            if checkpoint_manager is not None and active_settings.checkpoints_enabled:
                checkpoint_manager.create(
                    session_id=getattr(self.app, "_active_session_id", ""),
                    stage="pre_step",
                    messages=messages,
                    metadata={"step": step, "depth": depth},
                    summary="Before provider step %s" % step,
                )
            memory_provider_manager = getattr(self.app, "memory_provider_manager", None)
            if memory_provider_manager is not None:
                memory_provider_manager.on_pre_compact(messages)
            compaction_result: CompactionResult = maybe_compact_messages(
                messages,
                max_context_tokens=context_limit,
                preserve_last_n_turns=active_settings.preserve_last_n_turns,
                critical_fact_extractor=self.app.get_compaction_fact_extractor(active_settings),
            )
            messages = compaction_result.messages
            if compaction_result.compacted:
                compaction_payload = compaction_result.to_dict()
                compaction_payload["count"] = len(compactions) + 1
                compactions.append(compaction_payload)
                _emit_event(
                    emitted_events,
                    event_handler,
                    "messages_compacted",
                    step=step,
                    removed_message_count=compaction_result.removed_message_count,
                    token_estimate_before=compaction_result.token_estimate_before,
                    token_estimate_after=compaction_result.token_estimate_after,
                    compressed_summary=compaction_result.compressed_summary,
                )
                self.app.run_plugin_hooks(
                    "OnCompaction",
                    {
                        "step": step,
                        "depth": depth,
                        "session_id": getattr(self.app, "_active_session_id", ""),
                        "removed_message_count": compaction_result.removed_message_count,
                        "token_estimate_before": compaction_result.token_estimate_before,
                        "token_estimate_after": compaction_result.token_estimate_after,
                    },
                    settings=active_settings,
                )
            available_tools = self.app.select_available_tools(
                prompt_text=prompt,
                conversation=messages,
                allowed_tools=self.allowed_tools,
                settings=active_settings,
            )
            token_estimate = estimate_tokens(messages)
            pressure_ratio = (
                float(token_estimate) / float(context_limit)
                if context_limit
                else 0.0
            )
            if pressure_ratio >= active_settings.context_pressure_warn_ratio:
                _emit_event(
                    emitted_events,
                    event_handler,
                    "context_pressure",
                    step=step,
                    token_estimate=token_estimate,
                    max_context_tokens=context_limit,
                    pressure_ratio=round(pressure_ratio, 4),
                    level=(
                        "critical"
                        if pressure_ratio >= active_settings.context_pressure_critical_ratio
                        else "warn"
                    ),
                )
            try:
                response = self.provider.complete(
                    messages,
                    available_tools,
                    active_settings,
                )
            except Exception as exc:
                self.app.run_plugin_hooks(
                    "OnError",
                    {
                        "stage": "provider_complete",
                        "step": step,
                        "depth": depth,
                        "session_id": getattr(self.app, "_active_session_id", ""),
                        "error": str(exc),
                    },
                    settings=active_settings,
                )
                raise
            messages.append(
                ChatMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            _emit_event(
                emitted_events,
                event_handler,
                "assistant_message",
                step=step,
                content=response.content,
                tool_calls=[item.name for item in response.tool_calls],
                tool_call_count=len(response.tool_calls),
            )
            if not response.tool_calls:
                final_text = response.content
                _emit_event(
                    emitted_events,
                    event_handler,
                    "run_completed",
                    step=step,
                    final_text=final_text,
                )
                if checkpoint_manager is not None and active_settings.checkpoints_enabled:
                    checkpoint_manager.create(
                        session_id=getattr(self.app, "_active_session_id", ""),
                        stage="completed",
                        messages=messages,
                        metadata={"step": step, "depth": depth},
                        summary=final_text[:220],
                    )
                return AgentRunResult(
                    final_text=final_text,
                    messages=messages,
                    steps=step,
                    tool_invocations=tool_invocations,
                    events=emitted_events,
                    compactions=compactions,
                )

            for tool_call in response.tool_calls:
                _emit_event(
                    emitted_events,
                    event_handler,
                    "tool_call",
                    step=step,
                    tool=tool_call.name,
                    arguments=tool_call.arguments,
                )
                if checkpoint_manager is not None and active_settings.checkpoints_enabled:
                    checkpoint_manager.create(
                        session_id=getattr(self.app, "_active_session_id", ""),
                        stage="pre_tool",
                        messages=messages,
                        metadata={"step": step, "depth": depth, "tool": tool_call.name},
                        summary="Before tool %s" % tool_call.name,
                    )
                plugin_manager = getattr(self.app, "plugin_manager", None)
                if plugin_manager is not None:
                    plugin_manager.run_hooks(
                        "PreToolUse",
                        {
                            "tool": tool_call.name,
                            "arguments": tool_call.arguments,
                            "step": step,
                            "depth": depth,
                        },
                        workspace_root=active_settings.workspace_root,
                        timeout_sec=active_settings.command_timeout_sec,
                    )
                if self.allowed_tools and tool_call.name not in self.allowed_tools:
                    allowed = False
                    reason = "tool not allowed in this agent context"
                    tool_output = "Permission denied for %s: %s" % (
                        tool_call.name,
                        reason,
                    )
                    tool_invocations.append(
                        {
                            "tool": tool_call.name,
                            "arguments": tool_call.arguments,
                            "allowed": allowed,
                            "reason": reason,
                            "output": tool_output,
                        }
                    )
                    messages.append(
                        ChatMessage(
                            role="tool",
                            name=tool_call.name,
                            tool_call_id=tool_call.id,
                            content=tool_output,
                        )
                    )
                    _emit_event(
                        emitted_events,
                        event_handler,
                        "tool_result",
                        step=step,
                        tool=tool_call.name,
                        allowed=allowed,
                        reason=reason,
                        output=tool_output,
                    )
                    continue
                tool_arguments = dict(tool_call.arguments)
                if tool_call.name == "Bash":
                    tool_arguments["_sandbox"] = self.app.sandbox
                allowed, reason = self.app.authorize_tool_use(
                    tool_name=tool_call.name,
                    arguments=tool_arguments,
                    settings=active_settings,
                )
                if not allowed:
                    tool_output = "Permission denied for %s: %s" % (
                        tool_call.name,
                        reason,
                    )
                else:
                    try:
                        result = self.app.registry.execute(
                            tool_call.name,
                            tool_call.arguments,
                            active_settings,
                            services=self.app.get_services(
                                agent_loop=self,
                                depth=depth,
                                settings=active_settings,
                                conversation=messages,
                            ),
                        )
                        tool_output = result.content
                    except ToolError as exc:
                        self.app.run_plugin_hooks(
                            "OnError",
                            {
                                "stage": "tool_execute",
                                "tool": tool_call.name,
                                "arguments": tool_call.arguments,
                                "step": step,
                                "depth": depth,
                                "session_id": getattr(self.app, "_active_session_id", ""),
                                "error": str(exc),
                            },
                            settings=active_settings,
                        )
                        tool_output = "Tool error from %s: %s" % (tool_call.name, exc)

                tool_invocations.append(
                    {
                        "tool": tool_call.name,
                        "arguments": tool_call.arguments,
                        "allowed": allowed,
                        "reason": reason,
                        "output": tool_output,
                    }
                )
                self.app.audit(
                    "tool",
                    {
                        "tool": tool_call.name,
                        "allowed": allowed,
                        "reason": reason,
                    },
                )
                _emit_event(
                    emitted_events,
                    event_handler,
                    "tool_result",
                    step=step,
                    tool=tool_call.name,
                    allowed=allowed,
                    reason=reason,
                    output=tool_output,
                )
                if plugin_manager is not None:
                    plugin_manager.run_hooks(
                        "PostToolUse",
                        {
                            "tool": tool_call.name,
                            "arguments": tool_call.arguments,
                            "output": tool_output,
                            "allowed": allowed,
                            "reason": reason,
                            "step": step,
                            "depth": depth,
                        },
                        workspace_root=active_settings.workspace_root,
                        timeout_sec=active_settings.command_timeout_sec,
                    )
                messages.append(
                    ChatMessage(
                        role="tool",
                        name=tool_call.name,
                        tool_call_id=tool_call.id,
                        content=tool_output,
                    )
                )
                if checkpoint_manager is not None and active_settings.checkpoints_enabled:
                    checkpoint_manager.create(
                        session_id=getattr(self.app, "_active_session_id", ""),
                        stage="post_tool",
                        messages=messages,
                        metadata={"step": step, "depth": depth, "tool": tool_call.name},
                        summary="After tool %s" % tool_call.name,
                    )

        final_text = (
            "Agent reached max_agent_loops=%s before producing a final answer. "
            "Increase --max-steps or resume the session with a follow-up prompt such as "
            "`continue from the last step`."
        ) % (active_settings.max_agent_loops,)
        _emit_event(
            emitted_events,
            event_handler,
            "run_stopped",
            step=step,
            final_text=final_text,
        )
        return AgentRunResult(
            final_text=final_text,
            messages=messages,
            steps=step,
            tool_invocations=tool_invocations,
            events=emitted_events,
            compactions=compactions,
        )


def _emit_event(
    emitted_events: list[Event],
    event_handler: Callable[[Event], None] | None,
    kind: str,
    **payload: Any,
) -> None:
    event = Event(kind=kind, payload=payload)
    emitted_events.append(event)
    if event_handler is not None:
        event_handler(event)
