import os
import json

# Credenciales Críticas
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME", "miguelguerra200022-sudo/Genesis-Cloud")

# Configuración Padre
try: ID_PADRE = int(os.environ.get("ID_PADRE", "0"))
except: ID_PADRE = 0

# Cargar Firebase
FIREBASE_JSON = os.environ.get("FIREBASE_CREDENTIALS")
CRED_DICT = json.loads(FIREBASE_JSON) if FIREBASE_JSON else None
