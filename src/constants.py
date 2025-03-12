import os

ACTION_TYPE = os.environ.get("ACTION_TYPE")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

CUSTOM_PROMPT = os.environ.get("CUSTOM_PROMPT")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
GITHUB_EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH")

MAX_TURNS = int(os.environ.get("MAX_TURNS", 30))
