import json
import io
import os
import socket
import unittest
from urllib import error
from unittest.mock import patch

from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage, ModelResponse
from ecology_harness.runtime.providers import (
    PROVIDERS,
    AnthropicProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    ProviderError,
    bare_model,
    create_provider,
    detect_provider,
    effective_context_limit,
    list_provider_specs,
    resolve_api_key,
    resolve_base_url,
    resolve_provider,
)
from ecology_harness.tools.registry import ToolRegistry
from ecology_harness.tools import ToolDefinition, ToolResult
from ecology_harness.tools.builtin.claw_tools import register_claw_compat_tools
from ecology_harness.tools.builtin.task_tools import register_task_tools


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        return False


class _CaptureUrlopen:
    def __init__(self, payload):
        self.payload = payload
        self.seen_timeout = None
        self.request_body = None

    def __call__(self, req, timeout=None):
        self.seen_timeout = timeout
        if getattr(req, "data", None):
            self.request_body = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(self.payload)


class _KeyEchoProvider:
    def __init__(self, provider_name: str, api_key: str) -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.name = provider_name

    def complete(self, messages, tools, settings):
        del messages, tools
        return ModelResponse(content=self.api_key, raw={"provider": settings.provider})


class ProviderTests(unittest.TestCase):
    def _dummy_tools(self):
        return [
            ToolDefinition(
                name="Read",
                description="Read file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                handler=lambda params, _: ToolResult(content=params["path"]),
            )
        ]

    def test_detect_provider_supports_supported_sources(self) -> None:
        cases = {
            "claude-sonnet-4-6": "anthropic",
            "gpt-4o": "openai",
            "gemini-2.0-flash": "gemini",
            "moonshot-v1-32k": "kimi",
            "qwen-max": "qwen",
            "glm-4-plus": "zhipu",
            "deepseek-chat": "deepseek",
            "ollama/qwen2.5-coder": "ollama",
            "lmstudio/local-model": "lmstudio",
            "custom/my-model": "custom",
            "mock-agent": "mock",
        }
        for model, expected in cases.items():
            self.assertEqual(detect_provider(model), expected)

    def test_create_provider_auto_uses_model_source(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.model = "claude-sonnet-4-6"
        settings.provider = "auto"
        provider = create_provider(settings.provider, settings=settings)
        self.assertIsInstance(provider, AnthropicProvider)

        settings.model = "ollama/qwen2.5-coder"
        provider = create_provider(settings.provider, settings=settings)
        self.assertIsInstance(provider, OllamaProvider)

    def test_bare_model_strips_supported_prefixes(self) -> None:
        self.assertEqual(bare_model("ollama/qwen2.5-coder"), "qwen2.5-coder")
        self.assertEqual(bare_model("custom/my-model"), "my-model")
        self.assertEqual(bare_model("gpt-4o"), "gpt-4o")

    def test_resolve_provider_supports_explicit_prefix(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.provider = "auto"
        settings.model = "gemini/gemini-2.0-flash"
        spec, provider_name, model_name = resolve_provider(settings)
        self.assertEqual(spec.name, "gemini")
        self.assertEqual(provider_name, "gemini")
        self.assertEqual(model_name, "gemini-2.0-flash")

    def test_resolve_api_key_uses_provider_defaults_for_local_backends(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        self.assertEqual(resolve_api_key(settings, PROVIDERS["ollama"]), "ollama")
        self.assertEqual(resolve_api_key(settings, PROVIDERS["lmstudio"]), "lm-studio")

    def test_resolve_base_url_supports_custom_env_override(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        with patch.dict(os.environ, {"CUSTOM_BASE_URL": "https://example.com/v1"}, clear=False):
            self.assertEqual(
                resolve_base_url(settings, PROVIDERS["custom"]),
                "https://example.com/v1",
            )

    def test_list_provider_specs_includes_all_supported_sources(self) -> None:
        names = [item.name for item in list_provider_specs()]
        self.assertEqual(
            names,
            [
                "mock",
                "anthropic",
                "openai",
                "openrouter",
                "gemini",
                "kimi",
                "qwen",
                "zhipu",
                "deepseek",
                "ollama",
                "lmstudio",
                "custom",
            ],
        )

    def test_openrouter_provider_preserves_routed_model_name(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.provider = "openrouter"
        settings.model = "openai/gpt-4.1-mini"
        spec, provider_name, model_name = resolve_provider(settings)

        self.assertEqual(spec.name, "openrouter")
        self.assertEqual(provider_name, "openrouter")
        self.assertEqual(model_name, "openai/gpt-4.1-mini")

    def test_effective_context_limit_respects_provider_caps(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        self.assertEqual(settings.max_context_tokens, 258_000)

        settings.provider = "openai"
        settings.model = "gpt-4o"
        self.assertEqual(effective_context_limit(settings), 128_000)

        settings.provider = "openrouter"
        settings.model = "google/gemma-4-26b-a4b-it"
        self.assertEqual(effective_context_limit(settings), 258_000)

    def test_provider_router_round_robin_reports_actual_key_slot(self) -> None:
        from ecology_harness.runtime.provider_router import RoutedProvider

        settings = HarnessSettings.from_workspace(".")
        settings.provider = "openai"
        settings.api_key = "alpha,beta"
        settings.provider_pool_strategy = "round-robin"
        router = RoutedProvider(
            settings=settings,
            factory=lambda name, current: _KeyEchoProvider(name, current.api_key),
        )

        first = router.complete([ChatMessage(role="user", content="hello")], [], settings)
        second = router.complete([ChatMessage(role="user", content="hello again")], [], settings)

        self.assertEqual(first.content, "alpha")
        self.assertEqual(second.content, "beta")
        self.assertEqual(router.last_attempts[0].key_slot, 1)

    def test_openai_compatible_provider_parses_tool_calls(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.user_state_dir = settings.workspace_root / ".user_state_test"
        settings.api_key = "test-key"
        settings.provider = "openai"
        settings.model = "gpt-4o-mini"
        provider = OpenAICompatibleProvider()
        fake_payload = {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {
                                    "name": "Read",
                                    "arguments": '{"path":"README.md"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        with patch("ecology_harness.runtime.providers.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = provider.complete(
                [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="read the readme")],
                self._dummy_tools(),
                settings,
            )

        self.assertEqual(result.tool_calls[0].name, "Read")
        self.assertEqual(result.tool_calls[0].arguments["path"], "README.md")

    def test_provider_uses_provider_timeout_instead_of_command_timeout(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.api_key = "test-key"
        settings.provider = "openai"
        settings.model = "gpt-4o-mini"
        settings.command_timeout_sec = 5
        settings.provider_timeout_sec = 240
        provider = OpenAICompatibleProvider()
        fake_payload = {"choices": [{"message": {"content": "done"}}]}
        capture = _CaptureUrlopen(fake_payload)

        with patch("ecology_harness.runtime.providers.request.urlopen", side_effect=capture):
            result = provider.complete(
                [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="hello")],
                self._dummy_tools(),
                settings,
            )

        self.assertEqual(result.content, "done")
        self.assertEqual(capture.seen_timeout, 240)

    def test_provider_timeout_is_disabled_by_default(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.api_key = "test-key"
        settings.provider = "openai"
        settings.model = "gpt-4o-mini"
        provider = OpenAICompatibleProvider()
        fake_payload = {"choices": [{"message": {"content": "done"}}]}
        capture = _CaptureUrlopen(fake_payload)

        with patch("ecology_harness.runtime.providers.request.urlopen", side_effect=capture):
            result = provider.complete(
                [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="hello")],
                self._dummy_tools(),
                settings,
            )

        self.assertEqual(result.content, "done")
        self.assertIsNone(capture.seen_timeout)

    def test_openai_compatible_provider_normalizes_missing_array_items(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.api_key = "test-key"
        settings.provider = "gemini"
        settings.model = "gemini-2.0-flash"
        provider = OpenAICompatibleProvider()
        tool = ToolDefinition(
            name="BrokenArrayTool",
            description="Tool with underspecified arrays.",
            input_schema={
                "type": "object",
                "properties": {
                    "files": {"type": "array"},
                    "constraints": {"type": "array"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "tags": {"type": "array"},
                            },
                        },
                    },
                },
            },
            handler=lambda params, _: ToolResult(content=json.dumps(params)),
        )
        capture = _CaptureUrlopen({"choices": [{"message": {"content": "done"}}]})

        with patch("ecology_harness.runtime.providers.request.urlopen", side_effect=capture):
            result = provider.complete(
                [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="hello")],
                [tool],
                settings,
            )

        self.assertEqual(result.content, "done")
        parameters = capture.request_body["tools"][0]["function"]["parameters"]
        self.assertEqual(parameters["properties"]["files"]["items"]["type"], "string")
        self.assertEqual(parameters["properties"]["constraints"]["items"]["type"], "string")
        self.assertEqual(
            parameters["properties"]["items"]["items"]["properties"]["tags"]["items"]["type"],
            "string",
        )

    def test_curated_builtin_tools_define_array_item_schemas(self) -> None:
        registry = ToolRegistry()
        register_claw_compat_tools(registry)
        register_task_tools(registry)

        brief_schema = registry.get("BriefTool").input_schema
        task_update_schema = registry.get("TaskUpdate").input_schema
        todo_schema = registry.get("TodoWriteTool").input_schema

        self.assertEqual(brief_schema["properties"]["files"]["items"]["type"], "string")
        self.assertEqual(brief_schema["properties"]["constraints"]["items"]["type"], "string")
        self.assertEqual(task_update_schema["properties"]["add_blocks"]["items"]["type"], "string")
        self.assertEqual(task_update_schema["properties"]["add_blocked_by"]["items"]["type"], "string")
        self.assertEqual(todo_schema["properties"]["items"]["items"]["type"], "object")

    def test_provider_timeout_error_mentions_provider_timeout_flag(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.api_key = "test-key"
        settings.provider = "openai"
        settings.model = "gpt-4o-mini"
        settings.provider_timeout_sec = 321
        provider = OpenAICompatibleProvider()

        with patch(
            "ecology_harness.runtime.providers.request.urlopen",
            side_effect=socket.timeout("timed out"),
        ):
            with self.assertRaises(ProviderError) as exc:
                provider.complete(
                    [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="hello")],
                    self._dummy_tools(),
                    settings,
                )

        self.assertIn("--provider-timeout", str(exc.exception))
        self.assertIn("321", str(exc.exception))

    def test_provider_http_429_error_mentions_fallback_options(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.api_key = "test-key"
        settings.provider = "openrouter"
        settings.model = "google/gemma-4-26b-a4b-it:free"
        provider = OpenAICompatibleProvider()
        http_error = error.HTTPError(
            url="https://example.com",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=io.BytesIO(
                b'{"error":{"message":"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstream"}}'
            ),
        )

        with patch(
            "ecology_harness.runtime.providers.request.urlopen",
            side_effect=http_error,
        ):
            with self.assertRaises(ProviderError) as exc:
                provider.complete(
                    [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="hello")],
                    self._dummy_tools(),
                    settings,
                )

        self.assertIn("--provider-fallback", str(exc.exception))
        self.assertIn("--provider-retry-attempts", str(exc.exception))

    def test_anthropic_provider_parses_tool_calls(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.api_key = "anthropic-key"
        settings.provider = "anthropic"
        settings.model = "claude-sonnet-4-6"
        provider = AnthropicProvider()
        fake_payload = {
            "content": [
                {"type": "text", "text": "Working on it."},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "Read",
                    "input": {"path": "README.md"},
                },
            ]
        }

        with patch("ecology_harness.runtime.providers.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = provider.complete(
                [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="read the readme")],
                self._dummy_tools(),
                settings,
            )

        self.assertEqual(result.content, "Working on it.")
        self.assertEqual(result.tool_calls[0].name, "Read")
        self.assertEqual(result.tool_calls[0].arguments["path"], "README.md")

    def test_ollama_provider_parses_native_response(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.provider = "ollama"
        settings.model = "ollama/qwen2.5-coder"
        provider = OllamaProvider()
        fake_payload = {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "Read",
                            "arguments": {"path": "README.md"},
                        }
                    }
                ],
            }
        }

        with patch("ecology_harness.runtime.providers.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = provider.complete(
                [ChatMessage(role="system", content="system"), ChatMessage(role="user", content="read the readme")],
                self._dummy_tools(),
                settings,
            )

        self.assertEqual(result.tool_calls[0].name, "Read")
        self.assertEqual(result.tool_calls[0].arguments["path"], "README.md")


if __name__ == "__main__":
    unittest.main()
