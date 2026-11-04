"""Task 1.1: show which model the DeepSeek API reports for each id."""

from tools.ai_openai_compat import OpenAiCompatManager

m = OpenAiCompatManager("deepseek")
for model in ["deepseek-flash", "deepseek-v4-flash", "deepseek-v4.1-flash"]:
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
    }
    resp, err = m._post_request(m.spec.chat_url, payload, timeout=60)
    if resp is None:
        print(model, "-> ERROR", err)
    else:
        j = resp.json()
        print(model, "-> reported model:", j.get("model"), "| content:", repr(j["choices"][0]["message"]["content"][:20]))
