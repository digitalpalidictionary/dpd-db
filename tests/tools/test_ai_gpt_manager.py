import sys
import types
from unittest.mock import Mock, patch

from tools.ai_manager import AIResponse
from tools.ai_gpt_manager import GptManager


def test_request_uses_codex_exec_and_returns_output() -> None:
    completed_process = Mock(returncode=0, stdout="", stderr="")

    with (
        patch("tools.ai_gpt_manager.shutil.which", return_value="/usr/bin/codex"),
        patch(
            "tools.ai_gpt_manager.subprocess.run", return_value=completed_process
        ) as mock_run,
        patch("tools.ai_gpt_manager.Path.read_text", return_value="OK"),
    ):
        manager = GptManager()

        response = manager.request(
            prompt="hello",
            prompt_sys="system",
            model="gpt-5.4",
        )

    assert response == AIResponse(content="OK", status_message="Success")
    command = mock_run.call_args.args[0]
    assert command[:4] == ["/usr/bin/codex", "exec", "-m", "gpt-5.4"]
    assert "system\n\nhello" in command


def test_ai_manager_registers_codex_provider() -> None:
    gemini_module = types.ModuleType("tools.ai_gemini_manager")
    deepseek_module = types.ModuleType("tools.ai_deepseek_manager")
    openrouter_module = types.ModuleType("tools.ai_open_router")

    gemini_module.GeminiManager = Mock(return_value=Mock())
    deepseek_module.DeepseekManager = Mock(return_value=Mock())
    openrouter_module.OpenRouterManager = Mock(return_value=Mock())

    with (
        patch.dict(
            sys.modules,
            {
                "tools.ai_gemini_manager": gemini_module,
                "tools.ai_deepseek_manager": deepseek_module,
                "tools.ai_open_router": openrouter_module,
            },
        ),
        patch("tools.ai_manager.config_read", return_value=None),
        patch("tools.ai_gpt_manager.shutil.which", return_value="/usr/bin/codex"),
    ):
        from tools.ai_manager import AIManager

        manager = AIManager()

    assert "codex" in manager.providers
    assert any(
        provider == "codex" and model == "gpt-5.4"
        for provider, model, _delay in manager.DEFAULT_MODELS
    )
    assert any(
        provider == "codex" and model == "gpt-5.4-mini"
        for provider, model, _delay in manager.DEFAULT_MODELS
    )
