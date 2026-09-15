import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import app


class SessionDocumentTests(unittest.TestCase):
    def test_builds_timestamped_session_filename_with_sanitized_base(self):
        filename = app.build_session_filename(
            " Reemplazo firma electronica Contractia ",
            generated_at=datetime(2026, 6, 12, 18, 35),
        )

        self.assertEqual(
            filename,
            "260612_1835_sesion_reemplazo-firma-electronica-contractia.md",
        )

    def test_session_markdown_contains_warning_and_machine_readable_state(self):
        content = app.build_session_markdown_content(
            session_name="Caso Contractia",
            raw_inputs={"vision": {"comments": "Reducir tiempos."}},
            validated_outputs={
                "vision": "### Ultima respuesta 1. Vision\n\nVision validada."
            },
            selected_model_id="gpt-5",
            generated_at=datetime(2026, 6, 12, 18, 35),
        )

        self.assertIn("No modificar esta sección para mantener el estado.", content)
        state = app.extract_session_state(content)

        self.assertEqual(state["session_name"], "Caso Contractia")
        self.assertEqual(state["selected_model_id"], "gpt-5")
        self.assertEqual(
            state["raw_inputs"]["vision"]["comments"],
            "Reducir tiempos.",
        )
        self.assertIn("vision", state["validated_outputs"])

    def test_save_session_reads_validated_outputs_from_feedback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_dir = Path(temp_dir)
            (feedback_dir / "vision_response.md").write_text(
                "### Ultima respuesta 1. Vision\n\nVision validada.",
                encoding="utf-8",
            )

            with patch.object(app, "FEEDBACK_DIR", feedback_dir):
                status, output_path = app.generate_session_markdown_document(
                    "Caso Contractia",
                    {"vision": {"comments": "Reducir tiempos."}},
                    "gpt-5",
                    generated_at=datetime(2026, 6, 12, 18, 35),
                )

            generated_path = Path(output_path)
            state = app.extract_session_state(generated_path.read_text(encoding="utf-8"))

        self.assertEqual(
            generated_path.name,
            "260612_1835_sesion_caso-contractia.md",
        )
        self.assertIn("Sesion guardada:", status)
        self.assertIn("vision", state["validated_outputs"])
        self.assertNotIn("target", state["validated_outputs"])

    def test_save_current_session_uses_ui_outputs_instead_of_stale_feedback_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_dir = Path(temp_dir) / "feedback"
            logs_dir = Path(temp_dir) / "logs"
            feedback_dir.mkdir()
            (feedback_dir / "target_response.md").write_text(
                "# Ultima respuesta 2. Target\n\nTarget viejo de otro PVB.",
                encoding="utf-8",
            )

            with patch.object(app, "FEEDBACK_DIR", feedback_dir):
                with patch.object(app, "LOGS_DIR", logs_dir):
                    with patch.object(app, "SESSIONS_LOG_PATH", logs_dir / "sesiones.jsonl"):
                        status, output_path, _ = app.save_current_session(
                            session_name="PVB Infra Eventos",
                            selected_model_id="gpt-5",
                            vision_comments="Arquitectura Orientada a Eventos",
                            target_items=[],
                            target_draft_item="",
                            business_items=[],
                            business_draft_item="",
                            need_items=[],
                            need_draft_item="",
                            pps_items=[],
                            pps_draft_item="",
                            competition_items=[],
                            competition_draft_item="",
                            channels_items=[],
                            channels_draft_item="",
                            investment_items=[],
                            investment_team="",
                            investment_hours="",
                            investment_role="",
                            investment_start_date="",
                            investment_end_date="",
                            revenue_items=[],
                            revenue_draft_item="",
                            vision_output="### Ultima respuesta 1. Vision\n\nVision nueva.",
                            target_output="",
                            business_output="",
                            need_output="",
                            pps_output="",
                            competition_output="",
                            channels_output="",
                            investment_output="",
                            revenue_output="",
                        )

            state = app.extract_session_state(Path(output_path).read_text(encoding="utf-8"))

        self.assertIn("Sesion guardada:", status)
        self.assertEqual(
            state["validated_outputs"],
            {"vision": "### Ultima respuesta 1. Vision\n\nVision nueva."},
        )

    def test_build_context_snapshot_extracts_canonical_decisions(self):
        snapshot = app.build_context_snapshot(
            {
                "vision": "\n".join(
                    [
                        "### Ultima respuesta 1. Vision",
                        "",
                        "## Vision propuesta",
                        "Modernizar capacidades criticas del negocio.",
                        "",
                        "## Validacion",
                        "- Extension: cumple",
                        "",
                        "## Ajustes sugeridos",
                        "- Confirmar si seguridad es driver principal.",
                    ]
                ),
                "target": "\n".join(
                    [
                        "## Target propuesto",
                        "- Unidad beneficiaria: Tecnologia.",
                        "- Segmento: equipos backend consumidores de SGI.",
                        "",
                        "## Validacion",
                        "- Lista no vacia: cumple",
                        "",
                        "## Ajustes sugeridos",
                        "- Confirmar si Plataforma SGI es constructor.",
                    ]
                ),
            }
        )

        self.assertEqual(
            snapshot["vision"]["decision"],
            "Modernizar capacidades criticas del negocio.",
        )
        self.assertIn("equipos backend", snapshot["target"]["decision"])
        self.assertIn("Confirmar si seguridad", snapshot["vision"]["guidance"])
        self.assertNotIn("Extension: cumple", snapshot["vision"]["decision"])

    def test_compact_feedback_context_uses_snapshot_instead_of_full_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_dir = Path(temp_dir)
            (feedback_dir / "vision_response.md").write_text(
                "\n".join(
                    [
                        "## Vision propuesta",
                        "Modernizar capacidades criticas del negocio.",
                        "",
                        "## Validacion",
                        "- Extension: cumple",
                        "",
                        "## Ajustes sugeridos",
                        "- Confirmar metricas de agilidad.",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.object(app, "FEEDBACK_DIR", feedback_dir):
                context = app.load_compact_feedback_context(["vision_response.md"])

        self.assertEqual(len(context), 1)
        self.assertIn("Contexto canonico compacto del PVB", context[0])
        self.assertIn("Modernizar capacidades criticas", context[0])
        self.assertIn("No inventes datos", context[0])
        self.assertNotIn("Extension: cumple", context[0])

    def test_session_state_persists_context_snapshot_without_losing_full_outputs(self):
        full_output = "\n".join(
            [
                "## Vision propuesta",
                "Modernizar capacidades criticas del negocio.",
                "",
                "## Validacion",
                "- Extension: cumple",
            ]
        )
        content = app.build_session_markdown_content(
            session_name="PVB Gateway",
            raw_inputs={"vision": {"comments": "Evento"}},
            validated_outputs={"vision": full_output},
            selected_model_id="gpt-5",
            generated_at=datetime(2026, 6, 16, 14, 30),
        )

        state = app.extract_session_state(content)

        self.assertEqual(state["validated_outputs"]["vision"], full_output)
        self.assertEqual(
            state["context_snapshot"]["vision"]["decision"],
            "Modernizar capacidades criticas del negocio.",
        )

    def test_restore_session_replaces_active_feedback_and_clears_missing_steps(self):
        session_state = {
            "raw_inputs": {"vision": {"comments": "Nueva vision"}},
            "validated_outputs": {
                "vision": "### Ultima respuesta 1. Vision\n\nNueva vision validada."
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_dir = Path(temp_dir) / "feedback"
            feedback_dir.mkdir()
            (feedback_dir / "vision_response.md").write_text(
                "Vision anterior",
                encoding="utf-8",
            )
            (feedback_dir / "target_response.md").write_text(
                "Target anterior de otro PVB",
                encoding="utf-8",
            )
            session_path = feedback_dir / "260612_1835_sesion_caso.md"
            session_path.write_text(
                app.build_session_markdown_content(
                    "Caso",
                    session_state["raw_inputs"],
                    session_state["validated_outputs"],
                    selected_model_id="gpt-5",
                    generated_at=datetime(2026, 6, 12, 18, 35),
                ),
                encoding="utf-8",
            )

            with patch.object(app, "FEEDBACK_DIR", feedback_dir):
                status, state = app.restore_session_from_path(session_path)

            vision_content = (feedback_dir / "vision_response.md").read_text(
                encoding="utf-8"
            )

        self.assertIn("Sesion cargada.", status)
        self.assertIn("Se restauraron 1 pasos", status)
        self.assertIn("Nueva vision validada.", vision_content)
        self.assertFalse((feedback_dir / "target_response.md").exists())
        self.assertEqual(state["raw_inputs"]["vision"]["comments"], "Nueva vision")

    def test_restore_session_logs_error_when_file_cannot_be_parsed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_dir = Path(temp_dir) / "feedback"
            logs_dir = Path(temp_dir) / "logs"
            feedback_dir.mkdir()
            invalid_session = feedback_dir / "invalid.md"
            invalid_session.write_text("No contiene estado valido.", encoding="utf-8")

            with patch.object(app, "FEEDBACK_DIR", feedback_dir):
                with patch.object(app, "LOGS_DIR", logs_dir):
                    with patch.object(app, "SESSIONS_LOG_PATH", logs_dir / "sesiones.jsonl"):
                        status, state = app.restore_session_from_path(invalid_session)

            log_record = json.loads(
                (logs_dir / "sesiones.jsonl").read_text(encoding="utf-8").splitlines()[0]
            )

        self.assertIn("No se pudo cargar la sesion", status)
        self.assertEqual(state, {})
        self.assertEqual(log_record["action"], "load_session")
        self.assertEqual(log_record["status"], "error")
        self.assertIn("error", log_record)

    def test_loaded_session_restores_model_selector_as_disabled(self):
        state = {
            "session_name": "Caso Contractia",
            "selected_model_id": "gemini:gemini-2.5-flash-lite",
            "raw_inputs": {},
            "validated_outputs": {},
        }

        outputs = app.build_loaded_session_outputs("Sesion cargada.", state)
        model_update = outputs[2]

        self.assertEqual(model_update["value"], "gemini:gemini-2.5-flash-lite")
        self.assertFalse(model_update["interactive"])

    def test_collect_session_raw_inputs_keeps_lists_and_unadded_drafts(self):
        raw_inputs = app.collect_session_raw_inputs(
            vision_comments="Vision en borrador",
            target_items=["Gerencia Comercial"],
            target_draft_item="Atencion al socio",
            business_items=["Reducir costos"],
            business_draft_item="Aumentar conversion",
            need_items=[],
            need_draft_item="Evitar reprocesos",
            pps_items=["Portal interno"],
            pps_draft_item="",
            competition_items=["Solucion A"],
            competition_draft_item="Solucion B",
            channels_items=[],
            channels_draft_item="Email",
            investment_items=[
                {
                    "team_name": "Arquitectura",
                    "hours": 80,
                    "fte": 0.5,
                    "role": "Revision",
                }
            ],
            investment_team="Seguridad",
            investment_hours=40,
            investment_role="Analisis",
            investment_start_date="2026-06-15",
            investment_end_date="2026-08-30",
            revenue_items=[],
            revenue_draft_item="Menor costo operativo",
        )

        self.assertEqual(raw_inputs["vision"]["comments"], "Vision en borrador")
        self.assertEqual(raw_inputs["target"]["items"], ["Gerencia Comercial"])
        self.assertEqual(raw_inputs["target"]["draft_item"], "Atencion al socio")
        self.assertEqual(raw_inputs["investment"]["draft_item"]["team_name"], "Seguridad")
        self.assertEqual(raw_inputs["investment"]["start_date"], "2026-06-15")
        self.assertEqual(raw_inputs["revenue_benefits"]["draft_item"], "Menor costo operativo")


if __name__ == "__main__":
    unittest.main()
