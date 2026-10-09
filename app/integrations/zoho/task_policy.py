import requests

from app.integrations.zoho.auth import get_zoho_token_data

# ============================================================
# CONFIGURACIÓN
# ============================================================

ZOHO_API_VERSION = "v8"
TASK_MODULE = "Tasks"
POLICY_MODULE = "Polizas"

# ============================================================
# CONSULTAR REGISTRO DE ZOHO
# ============================================================


def get_zoho_record(
    module_api_name: str,
    record_id: str,
) -> dict:
    """
    Obtiene un registro específico de Zoho CRM.

    Args:
        module_api_name:
            API Name del módulo.

        record_id:
            ID interno del registro.

    Returns:
        Diccionario con los campos del registro.
    """

    token_data = get_zoho_token_data()

    access_token = token_data["access_token"]

    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com",
    )

    url = (
        f"{api_domain}/crm/" f"{ZOHO_API_VERSION}/" f"{module_api_name}/" f"{record_id}"
    )

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    response_data = response.json()

    records = response_data.get("data", [])

    if not records:
        raise RuntimeError(
            f"No se encontró el registro en el módulo " f"{module_api_name}."
        )

    return records[0]


# ============================================================
# OBTENER PÓLIZA RELACIONADA CON TASK
# ============================================================


def get_task_policy_data(
    task_id: str,
) -> dict:
    """
    Obtiene el ID y el número de la póliza relacionada
    con una Task de Zoho CRM.

    La función valida que la relación corresponda
    al módulo Polizas.

    Returns:
        {
            "poliza_id": str,
            "poliza_numero_actual": str
        }
    """

    # ========================================================
    # 1. CONSULTAR TASK
    # ========================================================

    task_record = get_zoho_record(
        module_api_name=TASK_MODULE,
        record_id=task_id,
    )

    # ========================================================
    # 2. VALIDAR MÓDULO RELACIONADO
    # ========================================================

    related_module = task_record.get("$se_module")

    if related_module != POLICY_MODULE:
        raise ValueError(
            "La tarea no está relacionada con " "un registro del módulo Polizas."
        )

    # ========================================================
    # 3. OBTENER ID DE PÓLIZA
    # ========================================================

    related_record = task_record.get("What_Id")

    if not related_record:
        raise ValueError("La tarea no tiene una póliza relacionada.")

    if isinstance(related_record, dict):
        policy_id = related_record.get("id")
    else:
        policy_id = related_record

    if not policy_id:
        raise ValueError("No fue posible obtener el ID " "de la póliza relacionada.")

    policy_id = str(policy_id)

    # ========================================================
    # 4. CONSULTAR PÓLIZA
    # ========================================================

    policy_record = get_zoho_record(
        module_api_name=POLICY_MODULE,
        record_id=policy_id,
    )

    # ========================================================
    # 5. OBTENER NÚMERO DE PÓLIZA
    # ========================================================

    policy_number = policy_record.get("Name")

    if not policy_number:
        raise ValueError("La póliza relacionada no tiene " "un número de póliza.")

    # ========================================================
    # 6. RETORNAR INFORMACIÓN
    # ========================================================

    return {
        "poliza_id": policy_id,
        "poliza_numero_actual": str(policy_number).strip(),
    }