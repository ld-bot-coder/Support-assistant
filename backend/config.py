import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./support_assistant.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "e5d63b6c008b4777864e7bfa97ac4c4f.5lU4tl9bGL9JGdyxuqbQAYCu")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-oss:20b")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://ollama.com/v1")
