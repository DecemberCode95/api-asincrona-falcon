# 1. Nativas
import os
# 2. Terceros
from dotenv import load_dotenv

load_dotenv() # Carga las variables ocultas

class Settings:
    CLIENT_ID: str = os.getenv("CLIENT_ID", "default")
    CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "default")
    REFRESH_TOKEN: str = os.getenv("REFRESH_TOKEN", "default")
    TOKEN_URL: str = os.getenv("TOKEN_URL", "https://httpbin.org/post")

settings = Settings()