import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import app


class FinalDocumentTests(unittest.TestCase):
    def test_saves_latest_response_title_as_third_level_heading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "vision_response.md"

            app.save_latest_response(
                "## Vision propuesta\nCrecer con eficiencia.",
                output_path,
                "1. Vision",
            )

            content = output_path.read_text(encoding="utf-8")

        self.assertTrue(content.startswith("### Ultima respuesta 1. Vision\n\n"))
        self.assertIn("\n\nGenerada: ", content)

    def test_builds_timestamped_markdown_filename_with_sanitized_base(self):
        filename = app.build_export_filename(
            " Caso Beneficios 2026! ",
            generated_at=datetime(2026, 5, 27, 15, 4),
        )

        self.assertEqual(filename, "260527_1504_caso-beneficios-2026.md")

    def test_uses_default_base_when_name_is_empty(self):
        filename = app.build_export_filename(
            "   ",
            generated_at=datetime(2026, 5, 27, 15, 4),
        )

        self.assertEqual(filename, "260527_1504_product-vision-board.md")

    def test_generates_document_in_feedback_with_available_and_pending_sections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_dir = Path(temp_dir)
            (feedback_dir / "vision_response.md").write_text(
                "# Ultima respuesta Vision\n\nCrecer con eficiencia.",
                encoding="utf-8",
            )

            with patch.object(app, "FEEDBACK_DIR", feedback_dir):
                status, output_path = app.generate_final_markdown_document(
                    "PVB",
                    generated_at=datetime(2026, 5, 27, 15, 4),
                )

            generated_path = Path(output_path)
            content = generated_path.read_text(encoding="utf-8")

        self.assertEqual(generated_path.name, "260527_1504_pvb.md")
        self.assertIn("Documento generado:", status)
        self.assertEqual(content.count("\n---\n## "), len(app.FINAL_DOCUMENT_STEPS))
        self.assertIn("\n---\n## 1. Vision", content)
        self.assertIn("## 1. Vision", content)
        self.assertIn("Crecer con eficiencia.", content)
        self.assertIn("\n---\n## 2. Target", content)
        self.assertIn("## 2. Target", content)
        self.assertIn("Pendiente", content)


if __name__ == "__main__":
    unittest.main()
