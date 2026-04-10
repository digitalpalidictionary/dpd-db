import json
import shutil
import subprocess

from tools.ai_manager import AIResponse


class ClaudeManager:
    def __init__(self) -> None:
        self.claude_path = shutil.which("claude")

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: str | None = None,
        timeout: float = 60.0,
        grounding: bool = False,
        **kwargs,
    ) -> AIResponse:
        if grounding:
            return AIResponse(
                content=None,
                status_message="Claude CLI wrapper does not support grounding.",
            )

        if not self.claude_path:
            return AIResponse(content=None, status_message="Claude CLI not found.")

        full_prompt = f"{prompt_sys}\n\n{prompt}" if prompt_sys else prompt
        command = [
            self.claude_path,
            "-p",
            "--output-format",
            "json",
            "--model",
            model,
            full_prompt,
        ]

        try:
            completed_process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return AIResponse(content=None, status_message="Claude request timed out.")
        except Exception as e:
            return AIResponse(content=None, status_message=str(e))

        output = completed_process.stdout.strip() or completed_process.stderr.strip()
        if not output:
            return AIResponse(content=None, status_message="Claude returned no output.")

        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return AIResponse(content=None, status_message=output)

        if payload.get("is_error"):
            return AIResponse(
                content=None, status_message=payload.get("result", output)
            )

        result = payload.get("result")
        if not isinstance(result, str) or not result.strip():
            return AIResponse(content=None, status_message="Claude returned no result.")

        return AIResponse(content=result, status_message="Success")
