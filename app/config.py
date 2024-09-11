import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ASSISTANT_ID = "asst_Av7el8XKLfsbfOOlVxHfFE6t"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
