import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.cli import main
from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.attachments import build_user_message, extract_document
from ecology_harness.runtime.messages import ChatMessage, MessagePart
from ecology_harness.runtime.providers import messages_to_anthropic, messages_to_openai


def _write_dummy_png(path: Path) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _write_minimal_docx(path: Path, text: str) -> None:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>%s</w:t></w:r></w:p>"
        "</w:body>"
        "</w:document>"
    ) % text
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document_xml)


class MultimodalTests(unittest.TestCase):
    def test_build_user_message_preserves_image_and_document_parts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image_path = root / "leaf.png"
            doc_path = root / "notes.md"
            _write_dummy_png(image_path)
            doc_path.write_text("# Wetland notes\nmethane flux is high\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            message = build_user_message(
                "analyze these attachments",
                [str(image_path), str(doc_path)],
                settings=settings,
            )

            self.assertEqual(message.role, "user")
            self.assertEqual(len(message.content_parts), 3)
            self.assertEqual(message.content_parts[1].type, "image")
            self.assertEqual(message.content_parts[2].type, "document")
            self.assertIn("Wetland notes", message.content_text())

            payload = message.to_dict()
            restored = ChatMessage.from_dict(payload)
            self.assertEqual(restored.content_parts[1].type, "image")
            self.assertEqual(restored.attachment_labels(), ["leaf.png", "notes.md"])

    def test_chat_message_from_dict_tolerates_legacy_null_fields(self) -> None:
        restored = ChatMessage.from_dict(
            {
                "role": "assistant",
                "content": "done",
                "tool_calls": None,
                "content_parts": None,
            }
        )

        self.assertEqual(restored.role, "assistant")
        self.assertEqual(restored.tool_calls, [])
        self.assertEqual(restored.content_parts, [])

    def test_chat_message_from_dict_accepts_string_tool_arguments(self) -> None:
        restored = ChatMessage.from_dict(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "Read",
                        "arguments": '{"path":"README.md"}',
                    }
                ],
            }
        )

        self.assertEqual(restored.tool_calls[0].arguments, {"path": "README.md"})

    def test_messages_to_openai_supports_image_and_file_parts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image_path = root / "leaf.png"
            doc_path = root / "paper.md"
            _write_dummy_png(image_path)
            doc_path.write_text("ecosystem respiration\n", encoding="utf-8")
            settings = HarnessSettings.from_workspace(root)
            user_message = build_user_message(
                "summarize these",
                [str(image_path), str(doc_path)],
                settings=settings,
            )

            payload = messages_to_openai(
                [ChatMessage(role="system", content="system"), user_message],
                provider_name="openai",
            )

            user_payload = payload[1]
            self.assertEqual(user_payload["role"], "user")
            self.assertIsInstance(user_payload["content"], list)
            part_types = [item["type"] for item in user_payload["content"]]
            self.assertEqual(part_types, ["text", "image_url", "file"])
            self.assertIn("data:image/png;base64,", user_payload["content"][1]["image_url"]["url"])
            self.assertIn("filename", user_payload["content"][2]["file"])

    def test_messages_to_openai_supports_audio_parts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "bird.wav"
            with audio_path.open("wb") as handle:
                handle.write(b"RIFF$\x00\x00\x00WAVEfmt ")

            message = ChatMessage(
                role="user",
                content="listen to this recording",
                content_parts=[
                    MessagePart.text_part("listen to this recording"),
                    MessagePart.audio_part(
                        path=str(audio_path),
                        mime_type="audio/wav",
                        name="bird.wav",
                        metadata={"duration_seconds": 3.2},
                    ),
                ],
            )

            payload = messages_to_openai([message], provider_name="openai")
            self.assertEqual(payload[0]["content"][0]["type"], "text")
            self.assertEqual(payload[0]["content"][1]["type"], "input_audio")
            self.assertEqual(payload[0]["content"][1]["input_audio"]["format"], "wav")

    def test_messages_to_anthropic_supports_image_and_pdf_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image_path = root / "bird.png"
            pdf_path = root / "paper.pdf"
            _write_dummy_png(image_path)
            pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")

            user_message = ChatMessage(
                role="user",
                content="review the attachments",
                content_parts=[
                    MessagePart.text_part("review the attachments"),
                    MessagePart.image_part(
                        path=str(image_path),
                        mime_type="image/png",
                        name="bird.png",
                    ),
                    MessagePart.document_part(
                        path=str(pdf_path),
                        mime_type="application/pdf",
                        text="fallback pdf text",
                        name="paper.pdf",
                    ),
                ],
            )

            payload = messages_to_anthropic([ChatMessage(role="system", content="system"), user_message])
            blocks = payload[0]["content"]
            self.assertEqual(blocks[0]["type"], "text")
            self.assertEqual(blocks[1]["type"], "image")
            self.assertEqual(blocks[2]["type"], "document")

    def test_document_extract_supports_docx(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docx_path = root / "report.docx"
            _write_minimal_docx(docx_path, "Forest carbon report")
            settings = HarnessSettings.from_workspace(root)

            extracted = extract_document(str(docx_path), settings=settings)

            self.assertIn("Forest carbon report", extracted.text)
            self.assertEqual(extracted.metadata["paragraph_count"], 1)

    def test_build_user_message_expands_video_to_summary_and_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            video_path = root / "clip.mp4"
            frame_path = root / ".ecology_harness" / "media" / "video_frames" / "frame-001.jpg"
            frame_path.parent.mkdir(parents=True, exist_ok=True)
            video_path.write_bytes(b"video")
            _write_dummy_png(frame_path)

            settings = HarnessSettings.from_workspace(root)
            with patch(
                "ecology_harness.runtime.attachments.sample_video_frames",
                return_value=[frame_path],
            ):
                with patch(
                    "ecology_harness.runtime.attachments.inspect_video",
                    return_value=type(
                        "Inspection",
                        (),
                        {
                            "display_path": "clip.mp4",
                            "mime_type": "video/mp4",
                            "size_bytes": 5,
                            "metadata": {"duration_seconds": 2.0, "fps": 24.0},
                        },
                    )(),
                ):
                    message = build_user_message(
                        "review this clip",
                        [str(video_path)],
                        settings=settings,
                    )

            types = [part.type for part in message.content_parts]
            self.assertEqual(types, ["text", "video", "image"])
            self.assertIn("Attached video", message.content_text())

    def test_document_tools_are_registered_and_read_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            notes_path = root / "notes.md"
            notes_path.write_text("# Findings\nBlue carbon is increasing.\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "DocumentInspect",
                {"path": "notes.md"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("headings:", result.content)
            self.assertIn("Findings", result.content)

    def test_cli_supports_attach_flag_for_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc_path = root / "brief.md"
            doc_path.write_text("# Brief\nWetland restoration update.\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--attach",
                        "brief.md",
                        "--prompt",
                        "summarize this document",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("attachments: document: brief.md", buffer.getvalue())

    def test_repl_supports_attach_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image_path = root / "leaf.png"
            _write_dummy_png(image_path)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch(
                    "builtins.input",
                    side_effect=["/attach leaf.png", "/attachments", "/quit"],
                ):
                    exit_code = main(["--workspace", tmpdir, "--repl"])

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Pending attachments: image: leaf.png", output)
            self.assertIn("Pending Attachments", output)

    def test_cli_supports_audio_attach_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "bird.wav"
            with audio_path.open("wb") as handle:
                handle.write(b"RIFF$\x00\x00\x00WAVEfmt ")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch("builtins.input", side_effect=["/audio bird.wav", "/attachments", "/quit"]):
                    exit_code = main(["--workspace", tmpdir, "--repl"])

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("audio: bird.wav", output)

    def test_session_persists_attachment_content_parts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc_path = root / "notes.md"
            doc_path.write_text("# Attachment\nDocument text.\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt("summarize this", attachment_paths=["notes.md"])
            self.assertTrue(result.messages)

            payload = json.loads((root / ".ecology_harness" / "sessions" / "latest.json").read_text(encoding="utf-8"))
            user_messages = [item for item in payload["messages"] if item["role"] == "user"]
            self.assertTrue(user_messages)
            self.assertTrue(user_messages[-1]["content_parts"])


if __name__ == "__main__":
    unittest.main()
