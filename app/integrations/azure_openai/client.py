from openai import AzureOpenAI

from app.config.settings import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
)

def get_azure_openai_client() -> AzureOpenAI:
    """
    Crea y devuelve el cliente de Azure OpenAI.
    """

    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )

