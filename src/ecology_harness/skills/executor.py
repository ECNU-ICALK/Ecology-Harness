from __future__ import annotations

from ecology_harness.runtime.agent_loop import AgentRunResult
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.skills.loader import Skill


def execute_skill(
    app,
    skill: Skill,
    args: str,
    depth: int = 0,
    event_handler=None,
    conversation: list[ChatMessage] | None = None,
) -> AgentRunResult:
    rendered = app.skill_loader.render(skill, args)
    prompt = "[Skill: %s]\n\n%s" % (skill.name, rendered)
    allowed_tools = set(skill.tools) if skill.tools else None

    if skill.context == "fork":
        provider_name = app.settings.provider
        return app.subagent_manager.run(
            prompt=prompt,
            provider_name=provider_name,
            depth=depth,
            agent_type="",
            name="",
            wait=True,
            model_override=skill.model,
            allowed_tools=allowed_tools,
            extra_system_prompt="",
            event_handler=event_handler,
        )

    settings = app.settings
    if skill.model:
        from dataclasses import replace

        settings = replace(app.settings, model=skill.model)
    loop = app.create_agent_loop(
        provider_name=settings.provider,
        allowed_tools=allowed_tools,
        settings=settings,
    )
    return loop.run(
        prompt=prompt,
        settings=settings,
        system_prompt=app.build_system_prompt(
            settings=settings,
            prompt_text=prompt,
            conversation=conversation,
        ),
        depth=depth,
        event_handler=event_handler,
        conversation=conversation,
    )
