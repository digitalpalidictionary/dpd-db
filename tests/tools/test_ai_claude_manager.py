import json
import sys
import types
from unittest.mock import Mock, patch

from tools.ai_manager import AIResponse


def test_request_uses_claude_json_output_and_returns_result_field() -> None:
    completed_process = Mock(
        returncode=0,
        stdout=json.dumps({"result": '{"ok": true}', "is_error": False}),
        stderr="",
    )

    with (
        patch("tools.ai_claude_manager.shutil.which", return_value="/usr/bin/claude"),
        patch(
            "tools.ai_claude_manager.subprocess.run", return_value=completed_process
        ) as mock_run,
    ):
        from tools.ai_claude_manager import ClaudeManager

        manager = ClaudeManager()
        response = manager.request(
            prompt="hello",
            prompt_sys="return json",
            model="sonnet",
        )

    assert response == AIResponse(content='{"ok": true}', status_message="Success")
    command = mock_run.call_args.args[0]
    assert command[:6] == [
        "/usr/bin/claude",
        "-p",
        "--output-format",
        "json",
        "--model",
        "sonnet",
    ]
    assert "return json\n\nhello" in command


def test_ai_manager_registers_claude_provider_and_models() -> None:
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
        patch("tools.ai_claude_manager.shutil.which", return_value="/usr/bin/claude"),
    ):
        from tools.ai_manager import AIManager

        manager = AIManager()

    assert "claude" in manager.providers
    assert any(
        provider == "claude" and model == "opus"
        for provider, model, _delay in manager.DEFAULT_MODELS
    )
    assert any(
        provider == "claude" and model == "sonnet"
        for provider, model, _delay in manager.DEFAULT_MODELS
    )
    assert any(
        provider == "claude" and model == "haiku"
        for provider, model, _delay in manager.DEFAULT_MODELS
    )
