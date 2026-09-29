from pathlib import Path
import requests
from app.integrations.zoho.auth import refresh_access_token

ZOHO_API_VERSION = "v8"

# Carpeta temporal para los archivos descargados
TEMP_DIRECTORY = Path("temp")

def get_task_attachments(task_id: str) -> list:
    """
    Obtiene los archivos adjuntos asociados a un Task
    y filtra únicamente los que corresponden a recibo y/o caratula
    """

    token_data = refresh_access_token()

    access_token = token_data["access_token"]
    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com"
    )

    url = (
        f"{api_domain}/crm/{ZOHO_API_VERSION}"
        f"/Tasks/{task_id}/Attachments"
    )

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    params = {
        "fields": "id,File_Name,Size,Parent_Id,$se_module"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    attachments = data.get("data", [])

    # Filtrar únicamente recibo y caratula
    valid_attachments = []

    for attachment in attachments:

        file_name = attachment.get("File_Name", "").lower()

        if "recibo" in file_name or "caratula" in file_name:
            valid_attachments.append(attachment)

    return valid_attachments

def download_task_attachment(
    task_id: str,
    attachment_id: str,
    file_name: str
) -> Path:
    """
    Descarga un archivo adjunto de un Task
    y lo almacena temporalmente dentro de: temp/{task_id}/
    """

    token_data = refresh_access_token()

    access_token = token_data["access_token"]
    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com"
    )

    url = (
        f"{api_domain}/crm/{ZOHO_API_VERSION}"
        f"/Tasks/{task_id}/Attachments/{attachment_id}"
    )

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=60
    )

    response.raise_for_status()

    # Crear carpeta temporal específica para la Task
    download_directory = TEMP_DIRECTORY / task_id

    download_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = download_directory / file_name

    file_path.write_bytes(response.content)

    print(f"Archivo guardado en: {file_path.resolve()}")

    return file_path