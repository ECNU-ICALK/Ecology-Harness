import unittest

from ecology_harness.runtime.compaction import maybe_compact_messages
from ecology_harness.runtime.messages import ChatMessage


class CompactionTests(unittest.TestCase):
    def test_maybe_compact_messages_builds_continuation_summary(self) -> None:
        messages = [ChatMessage(role="system", content="System prompt")]
        for index in range(18):
            messages.append(
                ChatMessage(
                    role="user",
                    content=(
                        "Please continue the ecological workflow planning conversation and keep "
                        "track of dataset dependencies number %s. " % index
                    )
                    + ("detail " * 80),
                )
            )
            messages.append(
                ChatMessage(
                    role="assistant",
                    content=(
                        "I reviewed the repository context, the task tracker, and the datasets. "
                        "Next I will summarize the current work and coordinate subagents. "
                    )
                    + ("analysis " * 80),
                )
            )

        result = maybe_compact_messages(
            messages,
            max_context_tokens=400,
            preserve_last_n_turns=4,
        )

        self.assertTrue(result.compacted)
        self.assertGreater(result.removed_message_count, 0)
        self.assertEqual(result.messages[0].role, "system")
        self.assertEqual(result.messages[1].role, "system")
        self.assertIn("continued from an earlier context window", result.messages[1].content)
        self.assertIn("Conversation summary:", result.messages[1].content)
        self.assertLess(result.token_estimate_after, result.token_estimate_before)

    def test_compaction_shrinks_recent_window_until_under_threshold(self) -> None:
        messages = [ChatMessage(role="system", content="System prompt")]
        for index in range(10):
            messages.append(
                ChatMessage(
                    role="user",
                    content=("wetland methane request %s " % index) + ("detail " * 220),
                )
            )
            messages.append(
                ChatMessage(
                    role="assistant",
                    content=("analysis reply %s " % index) + ("analysis " * 220),
                )
            )

        result = maybe_compact_messages(
            messages,
            max_context_tokens=800,
            preserve_last_n_turns=6,
        )

        self.assertTrue(result.compacted)
        self.assertLessEqual(result.token_estimate_after, int(800 * 0.7))
        self.assertGreater(result.removed_message_count, 0)

    def test_compaction_preserves_must_keep_facts_in_summary(self) -> None:
        messages = [ChatMessage(role="system", content="System prompt")]
        messages.append(
            ChatMessage(
                role="user",
                content=(
                    "Please inspect the read-only route.\n"
                    "## Critical facts\n"
                    "- MUST: summary mode stayed read-only\n"
                    "- MUST: blocked command stayed node --version\n"
                    "- MUST: next command is eh team status <team-name>\n"
                )
                + ("noise " * 300),
            )
        )
        for index in range(8):
            messages.append(
                ChatMessage(
                    role="assistant",
                    content=("analysis reply %s " % index) + ("analysis " * 180),
                )
            )
            messages.append(
                ChatMessage(
                    role="user",
                    content=("follow-up request %s " % index) + ("detail " * 180),
                )
            )

        result = maybe_compact_messages(
            messages,
            max_context_tokens=700,
            preserve_last_n_turns=4,
        )

        self.assertTrue(result.compacted)
        summary = result.messages[1].content
        self.assertIn("Critical facts to preserve", summary)
        self.assertIn("MUST: summary mode stayed read-only", summary)
        self.assertIn("MUST: blocked command stayed node --version", summary)

    def test_compaction_prefers_semantic_fact_extractor_when_available(self) -> None:
        messages = [ChatMessage(role="system", content="System prompt")]
        for index in range(8):
            messages.append(
                ChatMessage(
                    role="user",
                    content=("request %s " % index) + ("detail " * 220),
                )
            )
            messages.append(
                ChatMessage(
                    role="assistant",
                    content=("reply %s " % index) + ("analysis " * 220),
                )
            )

        result = maybe_compact_messages(
            messages,
            max_context_tokens=700,
            preserve_last_n_turns=4,
            critical_fact_extractor=lambda removed, limit: [
                "Use semantic preservation for the active biodiversity workflow",
                "Do not switch away from the current provider",
            ][:limit],
        )

        self.assertTrue(result.compacted)
        summary = result.messages[1].content
        self.assertIn("Critical facts to preserve", summary)
        self.assertIn("Use semantic preservation for the active biodiversity workflow", summary)

    def test_compaction_falls_back_to_rules_when_semantic_extractor_errors(self) -> None:
        messages = [ChatMessage(role="system", content="System prompt")]
        messages.append(
            ChatMessage(
                role="user",
                content="MUST: preserve the wetland methane threshold." + ("detail " * 250),
            )
        )
        for index in range(6):
            messages.append(
                ChatMessage(role="assistant", content=("reply %s " % index) + ("analysis " * 150))
            )
            messages.append(
                ChatMessage(role="user", content=("request %s " % index) + ("detail " * 150))
            )

        result = maybe_compact_messages(
            messages,
            max_context_tokens=650,
            preserve_last_n_turns=4,
            critical_fact_extractor=lambda _removed, _limit: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        self.assertTrue(result.compacted)
        self.assertIn("MUST: preserve the wetland methane threshold", result.messages[1].content)


if __name__ == "__main__":
    unittest.main()
