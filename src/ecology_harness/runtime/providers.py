from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from dataclasses import dataclass
import json
import os
import socket
from typing import Any
from urllib import error, request
import uuid

from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage, ModelResponse, ToolCall
from ecology_harness.tools import ToolDefinition, ToolError


class ProviderError(Exception):
    """Raised when a model provider request fails."""


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    protocol: str
    api_key_env: str = ""
    base_url: str = ""
    api_key: str = ""
    context_limit: int = 128_000
    model_examples: tuple[str, ...] = ()
    description: str = ""
    local: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["model_examples"] = list(self.model_examples)
        return payload


PROVIDERS: dict[str, ProviderSpec] = {
    "mock": ProviderSpec(
        name="mock",
        protocol="mock",
        context_limit=128_000,
        model_examples=("mock-agent",),
        description="Deterministic offline provider for local development and tests.",
        local=True,
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        protocol="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        context_limit=200_000,
        model_examples=("claude-sonnet-4-6", "claude-opus-4-6"),
        description="Native Anthropic Messages API for Claude models.",
    ),
    "openai": ProviderSpec(
        name="openai",
        protocol="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        context_limit=128_000,
        model_examples=("gpt-4o", "gpt-4o-mini", "o3-mini"),
        description="OpenAI Chat Completions compatible endpoint for GPT and o-series models.",
    ),
    "gemini": ProviderSpec(
        name="gemini",
        protocol="openai",
        api_key_env="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        context_limit=1_000_000,
        model_examples=("gemini-2.0-flash", "gemini-1.5-pro"),
        description="Google Gemini via the OpenAI-compatible endpoint.",
    ),
    "kimi": ProviderSpec(
        name="kimi",
        protocol="openai",
        api_key_env="MOONSHOT_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        context_limit=128_000,
        model_examples=("moonshot-v1-32k", "kimi-latest"),
        description="Moonshot AI / Kimi OpenAI-compatible endpoint.",
    ),
    "qwen": ProviderSpec(
        name="qwen",
        protocol="openai",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        context_limit=1_000_000,
        model_examples=("qwen-max", "qwen2.5-coder-32b-instruct"),
        description="Alibaba DashScope OpenAI-compatible endpoint for Qwen models.",
    ),
    "zhipu": ProviderSpec(
        name="zhipu",
        protocol="openai",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        context_limit=128_000,
        model_examples=("glm-4-plus", "glm-4-flash"),
        description="Zhipu GLM endpoint exposed through an OpenAI-compatible API.",
    ),
    "deepseek": ProviderSpec(
        name="deepseek",
        protocol="openai",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        context_limit=64_000,
        model_examples=("deepseek-chat", "deepseek-reasoner"),
        description="DeepSeek OpenAI-compatible endpoint.",
    ),
    "ollama": ProviderSpec(
        name="ollama",
        protocol="ollama",
        base_url="http://localhost:11434",
        api_key="ollama",
        context_limit=128_000,
        model_examples=("ollama/qwen2.5-coder", "ollama/llama3.3"),
        description="Local Ollama native chat API with function calling.",
        local=True,
    ),
    "lmstudio": ProviderSpec(
        name="lmstudio",
        protocol="openai",
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        context_limit=128_000,
        model_examples=("lmstudio/local-model",),
        description="Local LM Studio OpenAI-compatible API.",
        local=True,
    ),
    "custom": ProviderSpec(
        name="custom",
        protocol="openai",
        api_key_env="CUSTOM_API_KEY",
        base_url="",
        context_limit=128_000,
        model_examples=("custom/my-model",),
        description="Any custom OpenAI-compatible endpoint configured with --base-url or CUSTOM_BASE_URL.",
    ),
}


_PREFIXES = [
    ("mock", "mock"),
    ("claude-", "anthropic"),
    ("gpt-", "openai"),
    ("o1", "openai"),
    ("o3", "openai"),
    ("gemini-", "gemini"),
    ("moonshot-", "kimi"),
    ("kimi-", "kimi"),
    ("qwen", "qwen"),
    ("qwq-", "qwen"),
    ("glm-", "zhipu"),
    ("deepseek-", "deepseek"),
    ("llama", "ollama"),
    ("mistral", "ollama"),
    ("phi", "ollama"),
    ("gemma", "ollama"),
]


class BaseProvider(ABC):
    name = "base"

    @abstractmethod
    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        settings: HarnessSettings,
    ) -> ModelResponse:
        raise NotImplementedError


class MockProvider(BaseProvider):
    name = "mock"

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        settings: HarnessSettings,
    ) -> ModelResponse:
        del tools, settings
        if messages and messages[-1].role == "tool":
            recent_tools = []
            index = len(messages) - 1
            while index >= 0 and messages[index].role == "tool":
                recent_tools.append(messages[index])
                index -= 1
            recent_tools.reverse()
            lines = ["Tool execution complete."]
            for item in recent_tools:
                header = item.name or "tool"
                lines.append("%s:" % header)
                lines.append(item.content.strip())
            return ModelResponse(content="\n".join(lines))

        user_message = _last_message_by_role(messages, "user")
        if user_message is None:
            return ModelResponse(content="No user input received.")

        stripped = user_message.content.strip()
        tool_line = ""
        if stripped.startswith("/tool "):
            tool_line = stripped
        else:
            for line in stripped.splitlines():
                candidate = line.strip()
                if candidate.startswith("/tool "):
                    tool_line = candidate
                    break
        if tool_line:
            payload = tool_line[len("/tool ") :]
            parts = payload.split(" ", 1)
            if len(parts) != 2:
                return ModelResponse(content="Mock provider expected `/tool NAME {json}`.")
            tool_name, raw_args = parts
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError as exc:
                return ModelResponse(content="Invalid JSON for mock tool call: %s" % exc)
            return ModelResponse(
                content="Calling tool %s" % tool_name,
                tool_calls=[
                    ToolCall(
                        id="call_%s" % uuid.uuid4().hex[:8],
                        name=tool_name,
                        arguments=arguments,
                    )
                ],
            )

        return ModelResponse(
            content=(
                "Mock provider is active. Use `/tool NAME {json}` to simulate tool use, "
                "or configure a real provider such as anthropic, openai, gemini, kimi, qwen, "
                "zhipu, deepseek, ollama, lmstudio, or custom."
            )
        )


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        settings: HarnessSettings,
    ) -> ModelResponse:
        spec, provider_name, model_name = resolve_provider(settings)
        if provider_name != "anthropic":
            raise ProviderError("AnthropicProvider can only handle anthropic models.")
        api_key = resolve_api_key(settings, spec)
        if not api_key:
            raise ProviderError("No API key available. Set %s or pass --api-key." % spec.api_key_env)

        tool_payload = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        ]
        request_body = {
            "model": model_name,
            "max_tokens": 8_192,
            "system": _system_prompt(messages),
            "messages": messages_to_anthropic(messages),
            "tools": tool_payload,
        }
        url = resolve_base_url(settings, spec).rstrip("/") + "/messages"
        payload = json.dumps(request_body).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        raw = _perform_json_request(req, timeout=settings.provider_timeout_sec)
        content_blocks = raw.get("content", [])
        text_parts = []
        tool_calls = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", "call_%s" % uuid.uuid4().hex[:8]),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}) or {},
                    )
                )
        return ModelResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            raw=raw,
        )


class OpenAICompatibleProvider(BaseProvider):
    name = "openai"

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        settings: HarnessSettings,
    ) -> ModelResponse:
        spec, _provider_name, model_name = resolve_provider(settings)
        api_key = resolve_api_key(settings, spec)
        if not api_key:
            raise ProviderError(
                "No API key available. Set %s or pass --api-key."
                % (settings.api_key_env or spec.api_key_env or "an API key env var")
            )

        tool_payload = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]
        request_body = {
            "model": model_name,
            "messages": messages_to_openai(messages),
            "tools": tool_payload,
            "tool_choice": "auto",
        }
        url = resolve_base_url(settings, spec).rstrip("/") + "/chat/completions"
        payload = json.dumps(request_body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % api_key,
        }
        req = request.Request(url, data=payload, headers=headers, method="POST")
        raw = _perform_json_request(req, timeout=settings.provider_timeout_sec)
        return _parse_openai_like_response(raw)


class OllamaProvider(BaseProvider):
    name = "ollama"

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        settings: HarnessSettings,
    ) -> ModelResponse:
        spec, provider_name, model_name = resolve_provider(settings)
        if provider_name != "ollama":
            raise ProviderError("OllamaProvider can only handle ollama models.")

        request_body = {
            "model": model_name,
            "messages": messages_to_ollama(messages),
            "stream": False,
            "options": {"num_ctx": settings.max_context_tokens},
        }
        if tools:
            request_body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in tools
            ]
        url = resolve_base_url(settings, spec).rstrip("/") + "/api/chat"
        payload = json.dumps(request_body).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        raw = _perform_json_request(req, timeout=settings.provider_timeout_sec)
        message = raw.get("message", {})
        tool_calls = []
        for index, item in enumerate(message.get("tool_calls", [])):
            function_payload = item.get("function", {})
            tool_calls.append(
                ToolCall(
                    id="call_ollama_%s" % index,
                    name=function_payload.get("name", ""),
                    arguments=function_payload.get("arguments", {}) or {},
                )
            )
        return ModelResponse(
            content=message.get("content", "") or "",
            tool_calls=tool_calls,
            raw=raw,
        )


def detect_provider(model: str) -> str:
    if not model:
        return "openai"
    if "/" in model:
        prefix = model.split("/", 1)[0].strip().lower()
        if prefix in PROVIDERS:
            return prefix
    normalized = model.strip().lower()
    for prefix, provider_name in _PREFIXES:
        if normalized.startswith(prefix):
            return provider_name
    return "openai"


def bare_model(model: str) -> str:
    if "/" in model:
        prefix, rest = model.split("/", 1)
        if prefix.strip().lower() in PROVIDERS:
            return rest
    return model


def resolve_provider(settings: HarnessSettings, explicit: str = "") -> tuple[ProviderSpec, str, str]:
    requested = (explicit or settings.provider or "auto").strip().lower()
    if requested in {"", "auto"}:
        provider_name = detect_provider(settings.model)
    else:
        provider_name = requested
    if provider_name not in PROVIDERS:
        raise ToolError("Unsupported provider: %s" % provider_name)
    spec = PROVIDERS[provider_name]
    model_name = bare_model(settings.model)
    return spec, provider_name, model_name


def resolve_api_key(settings: HarnessSettings, spec: ProviderSpec) -> str:
    if settings.api_key:
        return settings.api_key
    if settings.api_key_env:
        return os.environ.get(settings.api_key_env, "")
    if spec.api_key_env:
        return os.environ.get(spec.api_key_env, "")
    return spec.api_key


def resolve_base_url(settings: HarnessSettings, spec: ProviderSpec) -> str:
    if settings.base_url:
        return settings.base_url
    if spec.name == "custom":
        base_url = os.environ.get("CUSTOM_BASE_URL", "")
        if not base_url:
            raise ProviderError(
                "custom provider requires --base-url or CUSTOM_BASE_URL."
            )
        return base_url
    if not spec.base_url:
        raise ProviderError("Provider %s has no default base URL configured." % spec.name)
    return spec.base_url


def create_provider(name: str, settings: HarnessSettings | None = None) -> BaseProvider:
    if settings is not None:
        spec, provider_name, _model_name = resolve_provider(settings, explicit=name)
    else:
        provider_name = (name or "mock").strip().lower()
        if provider_name in {"", "auto"}:
            provider_name = "openai"
        spec = PROVIDERS.get(provider_name)
        if spec is None:
            raise ToolError("Unsupported provider: %s" % provider_name)

    if spec.protocol == "mock":
        return MockProvider()
    if spec.protocol == "anthropic":
        return AnthropicProvider()
    if spec.protocol == "ollama":
        return OllamaProvider()
    return OpenAICompatibleProvider()


def list_provider_specs() -> list[ProviderSpec]:
    return list(PROVIDERS.values())


def messages_to_openai(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    result = []
    for message in messages:
        if message.role == "system":
            result.append({"role": "system", "content": message.content})
        elif message.role == "user":
            result.append({"role": "user", "content": message.content})
        elif message.role == "assistant":
            payload: dict[str, Any] = {
                "role": "assistant",
                "content": message.content or None,
            }
            if message.tool_calls:
                payload["tool_calls"] = [item.to_openai_dict() for item in message.tool_calls]
            result.append(payload)
        elif message.role == "tool":
            result.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )
    return result


def messages_to_anthropic(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    result = []
    index = 0
    while index < len(messages):
        message = messages[index]
        if message.role == "system":
            index += 1
            continue
        if message.role == "user":
            result.append({"role": "user", "content": message.content})
            index += 1
            continue
        if message.role == "assistant":
            blocks = []
            if message.content:
                blocks.append({"type": "text", "text": message.content})
            for tool_call in message.tool_calls:
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": tool_call.id,
                        "name": tool_call.name,
                        "input": tool_call.arguments,
                    }
                )
            result.append({"role": "assistant", "content": blocks})
            index += 1
            continue
        if message.role == "tool":
            tool_blocks = []
            while index < len(messages) and messages[index].role == "tool":
                tool_message = messages[index]
                tool_blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_message.tool_call_id,
                        "content": tool_message.content,
                    }
                )
                index += 1
            result.append({"role": "user", "content": tool_blocks})
            continue
        index += 1
    return result


def messages_to_ollama(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    payload = messages_to_openai(messages)
    for message in payload:
        if "tool_calls" not in message:
            continue
        for tool_call in message["tool_calls"]:
            function_payload = tool_call.get("function", {})
            raw_arguments = function_payload.get("arguments")
            if isinstance(raw_arguments, str):
                try:
                    function_payload["arguments"] = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    function_payload["arguments"] = {"_raw": raw_arguments}
    return payload


def _parse_openai_like_response(raw: dict[str, Any]) -> ModelResponse:
    choices = raw.get("choices", [])
    if not choices:
        raise ProviderError("Provider returned no choices.")
    message = choices[0].get("message", {})
    tool_calls = []
    for item in message.get("tool_calls", []):
        function_payload = item.get("function", {})
        raw_arguments = function_payload.get("arguments", "{}")
        try:
            arguments = json.loads(raw_arguments) if raw_arguments else {}
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "Provider returned invalid tool arguments for %s: %s"
                % (function_payload.get("name", "<unknown>"), exc)
            ) from exc
        tool_calls.append(
            ToolCall(
                id=item.get("id", "call_%s" % uuid.uuid4().hex[:8]),
                name=function_payload.get("name", ""),
                arguments=arguments,
            )
        )
    return ModelResponse(
        content=message.get("content") or "",
        tool_calls=tool_calls,
        raw=raw,
    )


def _perform_json_request(req: request.Request, timeout: int | None) -> dict[str, Any]:
    try:
        if timeout is None or timeout <= 0:
            response_context = request.urlopen(req)
        else:
            response_context = request.urlopen(req, timeout=timeout)
        with response_context as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProviderError("Provider HTTP error %s: %s" % (exc.code, body)) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise ProviderError(_provider_timeout_message(timeout)) from exc
    except error.URLError as exc:
        reason = getattr(exc, "reason", "")
        if isinstance(reason, socket.timeout):
            raise ProviderError(_provider_timeout_message(timeout)) from exc
        raise ProviderError("Provider connection error: %s" % exc) from exc


def _system_prompt(messages: list[ChatMessage]) -> str:
    for message in messages:
        if message.role == "system":
            return message.content
    return ""


def _last_message_by_role(messages: list[ChatMessage], role: str) -> ChatMessage | None:
    for message in reversed(messages):
        if message.role == role:
            return message
    return None


def _provider_timeout_message(timeout: int | None) -> str:
    if timeout is None or timeout <= 0:
        return "Provider request timed out. Set --provider-timeout to a positive value if you want an explicit timeout."
    return (
        "Provider request timed out after %ss. Increase --provider-timeout for long-running tasks."
        % timeout
    )
