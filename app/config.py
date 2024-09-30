import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    VALIDATION_ASSISTANT_ID = "asst_Av7el8XKLfsbfOOlVxHfFE6t"
    DESCRIPTION_ASSISTANT_ID = "asst_hBxVPAGyvBWRl8yqUGQ4s3DQ"
    JSON_ASSISTANT_ID = "asst_epHy6Z98lbmQQbN65hlldUJi"
    SUGGESTION_ASSISTANT_ID = "asst_w9Ek5KNOB1l1XqxrrfwKnScY"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
