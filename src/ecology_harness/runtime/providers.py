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
from ecology_harness.runtime.attachments import audio_format_for_openai, encode_file_base64
from ecology_harness.runtime.messages import ChatMessage, MessagePart, ModelResponse, ToolCall
from ecology_harness.runtime.provider_schema import tool_parameters_schema
from ecology_harness.runtime.provider_router import RoutedProvider
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
    "openrouter": ProviderSpec(
        name="openrouter",
        protocol="openai",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        context_limit=1_000_000,
        model_examples=("openai/gpt-4.1-mini", "anthropic/claude-3.7-sonnet", "google/gemini-2.5-pro"),
        description="OpenRouter OpenAI-compatible endpoint for routed multi-provider model access.",
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
                lines.append(item.content_text().strip())
            return ModelResponse(content="\n".join(lines))

        user_message = _last_message_by_role(messages, "user")
        if user_message is None:
            return ModelResponse(content="No user input received.")

        stripped = user_message.content_text().strip()
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
                "input_schema": tool_parameters_schema(tool),
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
                    "parameters": tool_parameters_schema(tool),
                },
            }
            for tool in tools
        ]
        request_body = {
            "model": model_name,
            "messages": messages_to_openai(messages, provider_name=spec.name),
            "tools": tool_payload,
            "tool_choice": "auto",
        }
        url = resolve_base_url(settings, spec).rstrip("/") + "/chat/completions"
        payload = json.dumps(request_body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % api_key,
        }
        if spec.name == "openrouter":
            referer = os.environ.get("OPENROUTER_HTTP_REFERER", "")
            title = os.environ.get("OPENROUTER_TITLE", "")
            if referer:
                headers["HTTP-Referer"] = referer
            if title:
                headers["X-OpenRouter-Title"] = title
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
                        "parameters": tool_parameters_schema(tool),
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
    if provider_name == "openrouter":
        model_name = settings.model
        if model_name.startswith("openrouter/"):
            model_name = model_name.split("/", 1)[1]
    else:
        model_name = bare_model(settings.model)
    return spec, provider_name, model_name


def resolve_api_key(settings: HarnessSettings, spec: ProviderSpec) -> str:
    if settings.api_key:
        return settings.api_key
    if settings.api_key_env:
        if _looks_like_literal_api_key(settings.api_key_env):
            return settings.api_key_env.strip()
        return os.environ.get(settings.api_key_env, "")
    if spec.api_key_env:
        return os.environ.get(spec.api_key_env, "")
    return spec.api_key


def _looks_like_literal_api_key(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if text.startswith("$") or "=" in text:
        return False
    if text.upper() == text and all(ch.isalnum() or ch == "_" for ch in text):
        return False
    known_prefixes = (
        "sk-",
        "sk_",
        "sk-or-",
        "gsk_",
        "gsk-",
        "AIza",
        "dashscope-",
    )
    if any(text.startswith(prefix) for prefix in known_prefixes):
        return True
    return len(text) >= 32 and not all(ch.isupper() or ch.isdigit() or ch == "_" for ch in text)


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
        if _routing_needed(settings):
            return RoutedProvider(settings=settings, factory=_create_direct_provider, explicit=name)
        return _create_direct_provider(name, settings)
    return _create_direct_provider(name, settings)


def _create_direct_provider(name: str, settings: HarnessSettings | None = None) -> BaseProvider:
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


def _routing_needed(settings: HarnessSettings) -> bool:
    if getattr(settings, "provider_fallbacks", ()):
        return True
    if int(getattr(settings, "provider_retry_attempts", 1) or 1) > 1:
        return True
    if settings.api_key and "," in settings.api_key:
        return True
    api_key_env = (settings.api_key_env or "").strip()
    if api_key_env:
        for candidate in (
            api_key_env,
            api_key_env + "S" if not api_key_env.endswith("S") else api_key_env,
            api_key_env.replace("_KEY", "_KEYS") if api_key_env.endswith("_KEY") else api_key_env,
        ):
            raw = os.environ.get(candidate, "")
            if raw and ("," in raw or "\n" in raw):
                return True
    return False


def list_provider_specs() -> list[ProviderSpec]:
    return list(PROVIDERS.values())


def effective_context_limit(settings: HarnessSettings) -> int:
    requested = max(int(getattr(settings, "max_context_tokens", 0) or 0), 1)
    provider_names: list[str] = []
    requested_provider = (getattr(settings, "provider", "") or "auto").strip().lower()
    if requested_provider in {"", "auto"}:
        provider_names.append(detect_provider(getattr(settings, "model", "")))
    else:
        provider_names.append(requested_provider)
    for fallback in getattr(settings, "provider_fallbacks", ()) or ():
        normalized = str(fallback).strip().lower()
        if normalized and normalized not in provider_names:
            provider_names.append(normalized)
    limits = [
        int(spec.context_limit)
        for name in provider_names
        for spec in [PROVIDERS.get(name)]
        if spec is not None and int(spec.context_limit or 0) > 0
    ]
    if not limits:
        return requested
    return min(requested, min(limits))


def messages_to_openai(
    messages: list[ChatMessage],
    provider_name: str = "openai",
) -> list[dict[str, Any]]:
    result = []
    for message in messages:
        if message.role == "system":
            result.append({"role": "system", "content": message.content_text()})
        elif message.role == "user":
            result.append(
                {
                    "role": "user",
                    "content": _openai_user_content(message, provider_name=provider_name),
                }
            )
        elif message.role == "assistant":
            payload: dict[str, Any] = {
                "role": "assistant",
                "content": message.content_text() or None,
            }
            if message.tool_calls:
                payload["tool_calls"] = [item.to_openai_dict() for item in message.tool_calls]
            result.append(payload)
        elif message.role == "tool":
            result.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content_text(),
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
            result.append({"role": "user", "content": _anthropic_user_content(message)})
            index += 1
            continue
        if message.role == "assistant":
            blocks = []
            if message.content_text():
                blocks.append({"type": "text", "text": message.content_text()})
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
                        "content": tool_message.content_text(),
                    }
                )
                index += 1
            result.append({"role": "user", "content": tool_blocks})
            continue
        index += 1
    return result


def messages_to_ollama(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    payload = []
    for message in messages:
        if message.role == "system":
            payload.append({"role": "system", "content": message.content_text()})
            continue
        if message.role == "user":
            item: dict[str, Any] = {
                "role": "user",
                "content": _ollama_user_text(message),
            }
            images = _ollama_user_images(message)
            if images:
                item["images"] = images
            payload.append(item)
            continue
        if message.role == "assistant":
            item = {
                "role": "assistant",
                "content": message.content_text() or None,
            }
            if message.tool_calls:
                item["tool_calls"] = [tool_call.to_openai_dict() for tool_call in message.tool_calls]
                for tool_call in item["tool_calls"]:
                    function_payload = tool_call.get("function", {})
                    raw_arguments = function_payload.get("arguments")
                    if isinstance(raw_arguments, str):
                        try:
                            function_payload["arguments"] = json.loads(raw_arguments)
                        except json.JSONDecodeError:
                            function_payload["arguments"] = {"_raw": raw_arguments}
            payload.append(item)
            continue
        if message.role == "tool":
            payload.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content_text(),
                }
            )
    return payload


def _parse_openai_like_response(raw: dict[str, Any]) -> ModelResponse:
    choices = raw.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise ProviderError("Provider returned no choices.")
    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message") or {}
    if not isinstance(message, dict):
        message = {}
    raw_tool_calls = message.get("tool_calls") or []
    if not isinstance(raw_tool_calls, list):
        raw_tool_calls = []
    tool_calls = []
    for item in raw_tool_calls:
        if not isinstance(item, dict):
            continue
        function_payload = item.get("function") or {}
        if not isinstance(function_payload, dict):
            continue
        tool_name = str(function_payload.get("name", "") or "")
        if not tool_name:
            continue
        arguments = _parse_openai_tool_arguments(function_payload.get("arguments"), tool_name)
        tool_calls.append(
            ToolCall(
                id=item.get("id", "call_%s" % uuid.uuid4().hex[:8]),
                name=tool_name,
                arguments=arguments,
            )
        )
    return ModelResponse(
        content=_flatten_openai_response_content(message.get("content")),
        tool_calls=tool_calls,
        raw=raw,
    )


def _parse_openai_tool_arguments(raw_arguments: Any, tool_name: str) -> dict[str, Any]:
    if raw_arguments in (None, ""):
        return {}
    if isinstance(raw_arguments, dict):
        return dict(raw_arguments)
    if not isinstance(raw_arguments, str):
        raise ProviderError(
            "Provider returned invalid tool arguments for %s: expected object or JSON string."
            % tool_name
        )
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ProviderError(
            "Provider returned invalid tool arguments for %s: %s" % (tool_name, exc)
        ) from exc
    if not isinstance(parsed, dict):
        raise ProviderError(
            "Provider returned invalid tool arguments for %s: expected JSON object." % tool_name
        )
    return parsed


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
        raise ProviderError(_provider_http_error_message(exc.code, body)) from exc
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
            return message.content_text()
    return ""


def _last_message_by_role(messages: list[ChatMessage], role: str) -> ChatMessage | None:
    for message in reversed(messages):
        if message.role == role:
            return message
    return None


def _flatten_openai_response_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and item.get("text"):
                chunks.append(str(item.get("text", "")))
            elif item.get("type") == "output_text" and item.get("text"):
                chunks.append(str(item.get("text", "")))
        return "".join(chunks)
    return ""


def _openai_user_content(message: ChatMessage, provider_name: str) -> str | list[dict[str, Any]]:
    if not message.content_parts:
        return message.content
    if not _has_non_text_parts(message):
        return message.content_text()

    blocks: list[dict[str, Any]] = []
    for part in message.content_parts:
        if part.type == "text":
            if part.text:
                blocks.append({"type": "text", "text": part.text})
            continue
        if part.type == "image":
            blocks.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _data_url(part),
                    },
                }
            )
            continue
        if part.type == "document":
            if provider_name == "openai":
                blocks.append(
                    {
                        "type": "file",
                        "file": {
                            "filename": part.label(),
                            "file_data": encode_file_base64(part.path),
                        },
                    }
                )
            else:
                text = part.plain_text()
                if text:
                    blocks.append({"type": "text", "text": text})
            continue
        if part.type == "audio":
            if provider_name == "openai":
                blocks.append(
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encode_file_base64(part.path),
                            "format": audio_format_for_openai(part.path),
                        },
                    }
                )
            else:
                text = part.plain_text()
                if text:
                    blocks.append({"type": "text", "text": text})
            continue
        if part.type == "video":
            text = part.plain_text()
            if text:
                blocks.append({"type": "text", "text": text})
    return blocks or message.content_text()


def _anthropic_user_content(message: ChatMessage) -> str | list[dict[str, Any]]:
    if not message.content_parts:
        return message.content
    blocks: list[dict[str, Any]] = []
    for part in message.content_parts:
        if part.type == "text":
            if part.text:
                blocks.append({"type": "text", "text": part.text})
            continue
        if part.type == "image":
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": part.mime_type or "image/png",
                        "data": encode_file_base64(part.path),
                    },
                }
            )
            continue
        if part.type == "document" and (part.mime_type or "").lower() == "application/pdf":
            blocks.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": encode_file_base64(part.path),
                    },
                }
            )
            continue
        if part.type in {"audio", "video"}:
            text = part.plain_text()
            if text:
                blocks.append({"type": "text", "text": text})
            continue
        text = part.plain_text()
        if text:
            blocks.append({"type": "text", "text": text})
    return blocks or message.content_text()


def _ollama_user_text(message: ChatMessage) -> str:
    if not message.content_parts:
        return message.content
    chunks = []
    for part in message.content_parts:
        if part.type == "text" and part.text:
            chunks.append(part.text)
        elif part.type in {"document", "audio", "video"}:
            chunks.append(part.plain_text())
    return "\n\n".join(item for item in chunks if item).strip()


def _ollama_user_images(message: ChatMessage) -> list[str]:
    images = []
    for part in message.content_parts:
        if part.type != "image":
            continue
        images.append(encode_file_base64(part.path))
    return images


def _data_url(part: MessagePart) -> str:
    mime_type = part.mime_type or "application/octet-stream"
    return "data:%s;base64,%s" % (mime_type, encode_file_base64(part.path))


def _has_non_text_parts(message: ChatMessage) -> bool:
    return any(part.type != "text" for part in message.content_parts)


def _provider_timeout_message(timeout: int | None) -> str:
    if timeout is None or timeout <= 0:
        return "Provider request timed out. Set --provider-timeout to a positive value if you want an explicit timeout."
    return (
        "Provider request timed out after %ss. Increase --provider-timeout for long-running tasks."
        % timeout
    )


def _provider_http_error_message(status_code: int, body: str) -> str:
    message = "Provider HTTP error %s: %s" % (status_code, body)
    normalized = (body or "").lower()
    if status_code == 429 and ("rate-limit" in normalized or "rate limit" in normalized):
        message += (
            " Shared free-tier or upstream capacity limits are likely active. "
            "Retry shortly, remove `:free`, or configure `--provider-fallback` "
            "and `--provider-retry-attempts`."
        )
    return message
