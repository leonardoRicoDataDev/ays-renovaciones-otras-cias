import os

from dotenv import load_dotenv
load_dotenv()

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")
ZOHO_ACCOUNTS_URL = os.getenv("ZOHO_ACCOUNTS_URL")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

required_settings = {
    "ZOHO_CLIENT_ID": ZOHO_CLIENT_ID,
    "ZOHO_CLIENT_SECRET": ZOHO_CLIENT_SECRET,
    "ZOHO_REDIRECT_URI": ZOHO_REDIRECT_URI,
    "ZOHO_ACCOUNTS_URL": ZOHO_ACCOUNTS_URL,
    "ZOHO_REFRESH_TOKEN": ZOHO_REFRESH_TOKEN,
    "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
    "AZURE_OPENAI_API_KEY": AZURE_OPENAI_API_KEY,
    "AZURE_OPENAI_API_VERSION": AZURE_OPENAI_API_VERSION,
    "AZURE_OPENAI_DEPLOYMENT": AZURE_OPENAI_DEPLOYMENT,
}

missing_settings = [
    name
    for name, value in required_settings.items()
    if not value
]

if missing_settings:
    raise RuntimeError(
        f"Faltan variables de entorno: {', '.join(missing_settings)}"
    )