import time
from tools.printer import printer as pr

last_request_time = 0


def extract_with_ai(
    manager, word, html, model, prompt_template, rate_limit=3.0, prompt_data=None
) -> tuple[str, str] | None:
    """Extract POS and meaning from HTML."""
    global last_request_time

    if "free" in model:
        current_time = time.monotonic()
        elapsed = current_time - last_request_time
        if elapsed < rate_limit:
            time.sleep(rate_limit - elapsed)

    last_request_time = time.monotonic()

    if prompt_data:
        prompt = prompt_template.format(**prompt_data)
    else:
        prompt = prompt_template.format(word=word, html=html)

    response = manager.request(
        prompt=prompt,
        model=model,
        prompt_sys="You are a Pali dictionary editor. Extract accurate POS and meanings from dictionary HTML entries.",
        timeout=30.0,
    )

    if response.content:
        content = response.content.strip()
        if "|" in content:
            parts = content.split("|", 1)
            pos = parts[0].strip()
            meaning = parts[1].strip() if len(parts) > 1 else ""
            return (pos, meaning)

    if response.status_message and "Success" in response.status_message:
        if response.content and "NOT_FOUND" in response.content:
            return ("NOT_FOUND", "")

    pr.no("API error")
    pr.red(f"{response.status_message}")
    return None
