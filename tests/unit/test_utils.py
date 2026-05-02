from __future__ import annotations

import unittest

from ecology_harness.utils import dump_frontmatter, parse_frontmatter


class FrontmatterUtilsTests(unittest.TestCase):
    def test_frontmatter_round_trips_multiline_metadata(self) -> None:
        payload = dump_frontmatter(
            {
                "name": "Example",
                "description": "line one\nline two",
            },
            "body",
        )

        metadata, body = parse_frontmatter(payload)

        self.assertIn("description: |", payload)
        self.assertEqual(metadata["description"], "line one\nline two")
        self.assertEqual(body, "body")

    def test_frontmatter_keeps_single_line_metadata_compact(self) -> None:
        payload = dump_frontmatter({"name": "Example"}, "body")

        metadata, body = parse_frontmatter(payload)

        self.assertIn("name: Example", payload)
        self.assertEqual(metadata, {"name": "Example"})
        self.assertEqual(body, "body")


if __name__ == "__main__":
    unittest.main()
