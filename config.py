import os
from dotenv import load_dotenv

# Load variabel dari file .env
load_dotenv()

# Konfigurasi Utama
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-flash-lite" # Model yang tadi sukses dan cepat
