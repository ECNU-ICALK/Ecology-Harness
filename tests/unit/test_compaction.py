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


if __name__ == "__main__":
    unittest.main()
