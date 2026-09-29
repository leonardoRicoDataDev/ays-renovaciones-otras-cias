import time
import requests

from app.config.settings import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REDIRECT_URI,
    ZOHO_ACCOUNTS_URL,
    ZOHO_REFRESH_TOKEN,
)


# ============================================================
# CACHÉ DEL ACCESS TOKEN
# ============================================================

_token_data = None
_token_expiration = 0


# ============================================================
# INTERCAMBIAR AUTHORIZATION CODE
# ============================================================

def exchange_authorization_code(code: str) -> dict:
    """
    Intercambia un Authorization Code de Zoho
    por un Access Token y Refresh Token.
    """

    url = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "redirect_uri": ZOHO_REDIRECT_URI,
        "code": code,
    }

    response = requests.post(
        url,
        data=data,
        timeout=30,
    )

    if not response.ok:
        print("Error al obtener tokens:")
        print(response.status_code)
        print(response.text)

    response.raise_for_status()

    return response.json()


# ============================================================
# RENOVAR ACCESS TOKEN
# ============================================================

def refresh_access_token() -> dict:
    """
    Obtiene un nuevo Access Token utilizando el Refresh Token.
    """

    url = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token"

    data = {
        "grant_type": "refresh_token",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "refresh_token": ZOHO_REFRESH_TOKEN,
    }

    response = requests.post(
        url,
        data=data,
        timeout=30,
    )

    if not response.ok:
        print("Error al renovar access token:")
        print(response.status_code)
        print(response.text)

    response.raise_for_status()

    token_data = response.json()

    if "access_token" not in token_data:
        raise RuntimeError(
            f"Zoho no devolvió un access_token: {token_data}"
        )

    return token_data


# ============================================================
# OBTENER ACCESS TOKEN
# ============================================================

def get_zoho_token_data() -> dict:
    """
    Retorna un Access Token válido.

    Si existe un token almacenado y todavía no ha expirado,
    reutiliza el mismo token.

    Si no existe o está próximo a expirar, solicita uno nuevo
    utilizando el Refresh Token.
    """

    global _token_data
    global _token_expiration

    current_time = time.time()

    # Reutilizar token existente
    if (
        _token_data is not None
        and current_time < _token_expiration
    ):
        return _token_data

    # Solicitar un nuevo token
    _token_data = refresh_access_token()

    expires_in = _token_data.get(
        "expires_in",
        3600,
    )

    # Margen de seguridad de 60 segundos
    _token_expiration = (
        current_time
        + expires_in
        - 60
    )

    return _token_data