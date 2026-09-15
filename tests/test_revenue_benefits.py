import unittest
from unittest.mock import patch

import app


class RevenueBenefitsStepTests(unittest.TestCase):
    def test_rejects_empty_items(self):
        result = app.build_revenue_benefits([])

        self.assertIn("Agrega al menos un item de ingreso o beneficio", result)

    def test_rejects_duplicate_items(self):
        result = app.build_revenue_benefits(["Ahorra 10 horas.", " ahorra 10 horas. "])

        self.assertIn("no puede contener repetidos", result)

    def test_calls_openai_with_revenue_benefits_spec_and_previous_context(self):
        with patch.object(app, "load_compact_feedback_context", return_value=["ctx"]) as load_context:
            with patch.object(app, "call_openai_step", return_value="ok") as call_openai:
                result = app.build_revenue_benefits(
                    ["Reduce un 15% el tiempo de atencion para 500 afiliados."]
                )

        self.assertEqual(result, "ok")
        step_spec, user_input = call_openai.call_args.args[:2]
        extra_context = call_openai.call_args.kwargs["extra_context"]

        self.assertEqual(step_spec["id"], "revenue_benefits")
        self.assertIn("Items de ingresos y/o beneficios", user_input)
        self.assertIn("Reduce un 15% el tiempo de atencion", user_input)
        self.assertEqual(extra_context, ["ctx"])
        self.assertIn("investment_response.md", load_context.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
