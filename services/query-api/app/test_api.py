from google import genai

from config import load_settings


settings = load_settings()

if not settings.gemini_api_key:
    checked = "\n- ".join(["process environment", *settings.env_files_checked])
    raise SystemExit(
        "No Gemini API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY in one of these places:\n"
        f"- {checked}"
    )

print(f"Using Gemini API key source: {settings.gemini_api_key_source}")

client = genai.Client(api_key=settings.gemini_api_key)

response = client.models.generate_content(
    model=settings.llm_model_name,
    contents="Reply with exactly this text: GEMINI_OK",
)
print(response.text)