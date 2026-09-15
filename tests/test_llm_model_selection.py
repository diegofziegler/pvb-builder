import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import app


class LlmModelSelectionTests(unittest.TestCase):
    def test_models_include_openai_and_gemini_with_gpt5_as_default(self):
        self.assertEqual(
            app.LLM_MODEL_DROPDOWN_CHOICES,
            [
                ("OpenAI GPT-4o mini", "openai:gpt-4o-mini"),
                ("OpenAI GPT-5 mini", "openai:gpt-5-mini"),
                ("OpenAI GPT-5", "openai:gpt-5"),
                ("Gemini 2.5 Flash-Lite", "gemini:gemini-2.5-flash-lite"),
                ("Gemini 3.5 Flash", "gemini:gemini-3.5-flash"),
            ],
        )
        self.assertEqual(app.DEFAULT_LLM_MODEL_ID, "openai:gpt-5")

    def test_resolves_selected_openai_model_configuration(self):
        selected_model = app.resolve_llm_model("openai:gpt-5-mini")

        self.assertEqual(selected_model["provider"], "openai")
        self.assertEqual(selected_model["model"], "gpt-5-mini")
        self.assertEqual(selected_model["api_key_env"], "OPENAI_API_KEY")

    def test_resolves_selected_gemini_model_configuration(self):
        selected_model = app.resolve_llm_model("gemini:gemini-2.5-flash-lite")

        self.assertEqual(selected_model["provider"], "gemini")
        self.assertEqual(selected_model["model"], "gemini-2.5-flash-lite")
        self.assertEqual(selected_model["api_key_env"], "GEMINI_API_KEY")

    def test_llm_instructions_include_critical_guidance_for_problem_understanding(self):
        instructions = app.build_llm_instructions(app.VISION_SPEC)

        self.assertIn("No actuar de forma complaciente", instructions)
        self.assertIn("mejorar la comprension del problema", instructions)
        self.assertIn("investigar", instructions)

    def test_build_vision_passes_selected_model_to_llm_call(self):
        with patch.object(app, "call_openai_step", return_value="ok") as call_llm:
            result = app.build_vision("Reducir tiempos de atencion.", "openai:gpt-4o-mini")

        self.assertEqual(result, "ok")
        self.assertEqual(call_llm.call_args.kwargs["selected_model_id"], "openai:gpt-4o-mini")

    def test_process_vision_locks_model_selector_after_success(self):
        with patch.object(app, "build_vision", return_value="Vision validada."):
            result, next_step_update, model_update = app.process_vision_and_lock_model(
                "Reducir tiempos de atencion.",
                "gemini:gemini-2.5-flash-lite",
            )

        self.assertEqual(result, "Vision validada.")
        self.assertTrue(next_step_update["visible"])
        self.assertEqual(model_update["value"], "gemini:gemini-2.5-flash-lite")
        self.assertFalse(model_update["interactive"])

    def test_call_openai_step_uses_selected_model_and_api_key_env(self):
        response = SimpleNamespace(output_text=" Respuesta validada. ", usage=None, id="resp_123")
        openai_client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: response)
        )

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch.object(app, "OpenAI", return_value=openai_client) as openai_class:
                with patch.object(app, "save_latest_response"):
                    with patch.object(app, "log_openai_interaction") as log_interaction:
                        result = app.call_openai_step(
                            app.VISION_SPEC,
                            "Comentarios del usuario",
                            selected_model_id="openai:gpt-5-mini",
                        )

        self.assertEqual(result, "Respuesta validada.")
        openai_class.assert_called_once_with(api_key="test-key")
        self.assertEqual(log_interaction.call_args.kwargs["provider"], "openai")
        self.assertEqual(log_interaction.call_args.kwargs["model"], "gpt-5-mini")

    def test_call_openai_step_dispatches_to_gemini_with_selected_key(self):
        response = SimpleNamespace(
            text=" Respuesta Gemini. ",
            usage_metadata=SimpleNamespace(
                prompt_token_count=10,
                candidates_token_count=5,
                total_token_count=15,
            ),
        )
        gemini_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=MagicMock(return_value=response))
        )
        genai_module = SimpleNamespace(Client=MagicMock(return_value=gemini_client))

        with patch.dict("os.environ", {"GEMINI_API_KEY": "gemini-key"}, clear=True):
            with patch.object(app, "load_google_genai", return_value=genai_module):
                with patch.object(app, "save_latest_response"):
                    with patch.object(app, "log_openai_interaction") as log_interaction:
                        result = app.call_openai_step(
                            app.VISION_SPEC,
                            "Comentarios del usuario",
                            selected_model_id="gemini:gemini-3.5-flash",
                        )

        self.assertEqual(result, "Respuesta Gemini.")
        genai_module.Client.assert_called_once_with(api_key="gemini-key")
        gemini_client.models.generate_content.assert_called_once()
        generate_kwargs = gemini_client.models.generate_content.call_args.kwargs
        self.assertEqual(generate_kwargs["model"], "gemini-3.5-flash")
        self.assertEqual(generate_kwargs["contents"], "Comentarios del usuario")
        self.assertIn("system_instruction", generate_kwargs["config"])
        self.assertEqual(log_interaction.call_args.kwargs["provider"], "gemini")
        self.assertEqual(log_interaction.call_args.kwargs["model"], "gemini-3.5-flash")

    def test_missing_gemini_api_key_mentions_expected_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            result = app.call_openai_step(
                app.VISION_SPEC,
                "Comentarios del usuario",
                selected_model_id="gemini:gemini-2.5-flash-lite",
            )

        self.assertIn("GEMINI_API_KEY", result)

    def test_gpt4o_mini_has_pricing_for_cost_estimation(self):
        cost = app.calculate_cost(
            "gpt-4o-mini",
            {
                "billable_input_tokens": 1_000_000,
                "cached_input_tokens": 0,
                "output_tokens": 1_000_000,
            },
        )

        self.assertTrue(cost["pricing_found"])
        self.assertEqual(cost["estimated_total"], 0.75)


if __name__ == "__main__":
    unittest.main()
