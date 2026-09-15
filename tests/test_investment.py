import unittest
from unittest.mock import patch

import app


class InvestmentStepTests(unittest.TestCase):
    def test_calculates_item_and_totals(self):
        item = app.make_investment_item(
            "Equipo de Integraciones",
            320,
            "Implementar integraciones con sistemas internos.",
        )

        totals = app.calculate_investment_totals(
            [
                item,
                app.make_investment_item("Equipo de UX", 80, "Validar experiencia."),
            ]
        )

        self.assertEqual(item["fte"], 2.0)
        self.assertEqual(totals["total_hours"], 400)
        self.assertEqual(totals["total_ftes"], 2.5)

    def test_rejects_empty_items(self):
        result = app.build_investment([], "2026-06-01", "2026-07-01")

        self.assertIn("Agrega al menos un equipo participante", result)

    def test_rejects_duplicate_team_names(self):
        items = [
            app.make_investment_item("Equipo de Datos", 160, "Analizar datos."),
            app.make_investment_item(" equipo de datos ", 80, "Acompanamiento."),
        ]

        result = app.build_investment(items, "2026-06-01", "2026-07-01")

        self.assertIn("no puede contener equipos repetidos", result)

    def test_rejects_invalid_dates(self):
        items = [app.make_investment_item("Equipo de Datos", 160, "Analizar datos.")]

        result = app.build_investment(items, "2026-08-01", "2026-07-01")

        self.assertIn("no puede ser anterior", result)

    def test_calls_openai_with_investment_spec_totals_dates_and_previous_context(self):
        items = [app.make_investment_item("Equipo de Datos", 160, "Analizar datos.")]

        with patch.object(app, "load_compact_feedback_context", return_value=["ctx"]) as load_context:
            with patch.object(app, "call_openai_step", return_value="ok") as call_openai:
                result = app.build_investment(items, "2026-06-01", "2026-07-01")

        self.assertEqual(result, "ok")
        step_spec, user_input = call_openai.call_args.args[:2]
        extra_context = call_openai.call_args.kwargs["extra_context"]

        self.assertEqual(step_spec["id"], "investment")
        self.assertIn("Equipos participantes", user_input)
        self.assertIn("Total Horas: 160", user_input)
        self.assertIn("Total FTEs: 1.00", user_input)
        self.assertIn("Fecha Tentativa inicio: 2026-06-01", user_input)
        self.assertIn("Fecha Tentativa fin: 2026-07-01", user_input)
        self.assertEqual(extra_context, ["ctx"])
        self.assertIn("channels_response.md", load_context.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
