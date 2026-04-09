import subprocess
import tempfile
from pathlib import Path
import shutil

from tools.ai_manager import AIResponse


class GptManager:
    def __init__(self) -> None:
        self.codex_path = shutil.which("codex")

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
                status_message="Codex GPT wrapper does not support grounding.",
            )

        if not self.codex_path:
            return AIResponse(
                content=None,
                status_message="Codex CLI not found.",
            )

        full_prompt = f"{prompt_sys}\n\n{prompt}" if prompt_sys else prompt

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            output_path = Path(temp_file.name)

        command = [
            self.codex_path,
            "exec",
            "-m",
            model,
            "--output-last-message",
            str(output_path),
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
            output_path.unlink(missing_ok=True)
            return AIResponse(content=None, status_message="Codex request timed out.")
        except Exception as e:
            output_path.unlink(missing_ok=True)
            return AIResponse(content=None, status_message=str(e))

        try:
            if completed_process.returncode != 0:
                error = (
                    completed_process.stderr.strip() or completed_process.stdout.strip()
                )
                return AIResponse(
                    content=None, status_message=error or "Codex request failed."
                )

            try:
                content = output_path.read_text().strip()
            except Exception as e:
                return AIResponse(
                    content=None,
                    status_message=f"Codex output read error: {e}",
                )

            if not content:
                return AIResponse(
                    content=None, status_message="Codex returned no content."
                )
            return AIResponse(content=content, status_message="Success")
        finally:
            output_path.unlink(missing_ok=True)
