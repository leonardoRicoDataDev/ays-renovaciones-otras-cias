import requests
from datetime import datetime

from app.integrations.zoho.auth import get_zoho_token_data

from app.processing.common.general_rules import (
    ENDOSO_SIN_BENEFICIARIO,
    ENDOSO_CON_BENEFICIARIO,
    ESTADO_DEL_ENDOSO,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

ZOHO_API_VERSION = "v8"


# ============================================================
# FORMATEAR FECHAS PARA ZOHO
# ============================================================


def format_zoho_date(date_value: str | None) -> str | None:
    """
    Convierte una fecha DD/MM/YYYY al formato requerido
    por Zoho CRM: YYYY-MM-DD.
    """

    if not date_value:
        return None

    try:
        date = datetime.strptime(
            date_value.strip(),
            "%d/%m/%Y",
        )

        return date.strftime("%Y-%m-%d")

    except ValueError as exc:
        raise ValueError(
            f"Fecha inválida para Zoho: {date_value}. "
            "Se esperaba el formato DD/MM/YYYY."
        ) from exc


# ============================================================
# ACTUALIZAR REGISTRO GENÉRICO
# ============================================================


def update_record(
    module_api_name: str,
    record_id: str,
    data: dict,
) -> dict:
    """
    Actualiza un registro existente en Zoho CRM.
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
        "Content-Type": "application/json",
    }

    payload = {"data": [data]}

    response = requests.put(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        print("\nError de Zoho CRM:")
        print(f"Status Code: {response.status_code}")
        print(f"Respuesta: {response.text}")

    response.raise_for_status()

    return response.json()


# ============================================================
# CREAR REGISTRO GENÉRICO
# ============================================================


def create_record(
    module_api_name: str,
    data: dict,
) -> dict:
    """
    Crea un registro nuevo en Zoho CRM.
    """

    token_data = get_zoho_token_data()

    access_token = token_data["access_token"]

    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com",
    )

    url = f"{api_domain}/crm/" f"{ZOHO_API_VERSION}/" f"{module_api_name}"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    payload = {"data": [data]}

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        print("\nError de Zoho CRM:")
        print(f"Status Code: {response.status_code}")
        print(f"Respuesta: {response.text}")

    response.raise_for_status()

    return response.json()


# ============================================================
# BUSCAR ID DE PÓLIZA
# ============================================================


def get_policy_record_id(
    key_poliza: str,
) -> str | None:
    """
    Busca una póliza por su campo único y retorna su ID.
    """

    if not key_poliza:
        return None

    token_data = get_zoho_token_data()

    access_token = token_data["access_token"]

    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com",
    )

    url = f"{api_domain}/crm/" f"{ZOHO_API_VERSION}/" "Polizas/search"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    params = {
        "criteria": f"(Key:equals:{key_poliza})",
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    if response.status_code == 204:
        return None

    response.raise_for_status()

    records = response.json().get(
        "data",
        [],
    )

    if not records:
        return None

    return records[0].get("id")


# ============================================================
# ACTUALIZAR PÓLIZA EXISTENTE
# ============================================================


def update_policy(
    record_id: str,
    policy_data: dict,
) -> dict:
    """
    Actualiza una póliza existente en el módulo Polizas.
    """

    data = {
        "P_liza_Fecha_de_inicio_vigencia": format_zoho_date(
            policy_data.get("poliza_fecha_inicio_vigencia")
        ),
        "P_liza_Fecha_fin_de_la_vigencia": format_zoho_date(
            policy_data.get("poliza_fecha_fin_vigencia")
        ),
        "Pago_1": policy_data.get("valor_1"),
        "Fecha_1": format_zoho_date(policy_data.get("fecha_1")),
        "Referencia_Plan": policy_data.get("plan"),
        "Frecuencia": policy_data.get("periodicidad"),
        "Modo_de_pago": policy_data.get("forma_pago"),
        "Medio_de_pago": policy_data.get("medio_pago"),
    }

    return update_record(
        module_api_name="Polizas",
        record_id=record_id,
        data=data,
    )


# ============================================================
# ACTUALIZAR PÓLIZA REEMPLAZADA
# ============================================================


def update_replaced_policy(
    record_id: str,
) -> dict:
    """
    Marca una póliza anterior como Reemplazada.
    """

    data = {
        "Estado_de_la_p_liza": "Reemplazada",
    }

    return update_record(
        module_api_name="Polizas",
        record_id=record_id,
        data=data,
    )


# ============================================================
# CREAR PÓLIZA
# ============================================================


def create_policy(
    policy_data: dict,
) -> dict:
    """
    Crea una nueva póliza en el módulo Polizas.
    """

    reemplaza_poliza_actual = policy_data.get("reemplaza_poliza_actual")

    if reemplaza_poliza_actual is True:
        reemplaza_poliza_actual = "Si"

    elif reemplaza_poliza_actual is False:
        reemplaza_poliza_actual = "No"

    data = {
        "Tomador_principal1": policy_data.get("id_tomador"),
        "Reemplaza_p_liza_actual": reemplaza_poliza_actual,
        "P_liza_anterior": policy_data.get("key_id_poliza_actual"),
        "Name": policy_data.get("num_poliza"),
        "Ramo": policy_data.get("ramo"),
        "Aseguradora1": policy_data.get("aseguradora"),
        "L_der_Comercial": policy_data.get("lider_comercial"),
        "P_liza_Fecha_de_inicio_vigencia": format_zoho_date(
            policy_data.get("poliza_fecha_inicio_vigencia")
        ),
        "P_liza_Fecha_fin_de_la_vigencia": format_zoho_date(
            policy_data.get("poliza_fecha_fin_vigencia")
        ),
        "Modo_de_pago": policy_data.get("forma_pago"),
        "Medio_de_pago": policy_data.get("medio_pago"),
        "Frecuencia": policy_data.get("periodicidad"),
        "Pago_1": policy_data.get("valor_1"),
        "Fecha_1": format_zoho_date(policy_data.get("fecha_1")),
        "Referencia_Plan": policy_data.get("plan"),
        "Participaci_n": policy_data.get("participacion"),
        "comisi_n": policy_data.get("comision"),
        "IVA": policy_data.get("iva"),
        "Estado_de_la_p_liza": policy_data.get("estado_poliza"),
        "estado_pliza": policy_data.get("estado_pliza"),
        "Layout": policy_data.get("layout"),
    }

    return create_record(
        module_api_name="Polizas",
        data=data,
    )


# ============================================================
# CREAR OPERACIÓN
# ============================================================


def create_operation(
    operation_data: dict,
) -> dict:
    """
    Crea una nueva Operación en Zoho CRM.
    """

    data = {
        "P_liza": operation_data.get("key_poliza_id"),
        "Name": operation_data.get("nombre_operacion"),
        "Tomador": operation_data.get("id_tomador"),
        "Aseguradora": operation_data.get("aseguradora"),
        "P_liza_Fecha_de_inicio_vigencia": format_zoho_date(
            operation_data.get("poliza_fecha_inicio_vigencia")
        ),
        "P_liza_Fecha_fin_de_la_vigencia": format_zoho_date(
            operation_data.get("poliza_fecha_fin_vigencia")
        ),
        "Certificado_Fecha_de_inicio_de_vigencia": (
            format_zoho_date(operation_data.get("certificado_fecha_inicio_vigencia"))
        ),
        "Certificado_Fecha_de_Fin_de_vigencia": (
            format_zoho_date(operation_data.get("certificado_fecha_fin_vigencia"))
        ),
        "Fecha_de_expedici_n_de_p_liza": format_zoho_date(
            operation_data.get("fecha_expedicion")
        ),
        "N_mero_de_certificado": operation_data.get("certificado"),
        "Forma_de_pago": operation_data.get("forma_pago"),
        "Medio_de_pago": operation_data.get("medio_pago"),
        "Periodicidad": operation_data.get("periodicidad"),
        "Participaci_n": operation_data.get("participacion"),
        "Comisi_n": operation_data.get("comision"),
        "IVA": operation_data.get("iva"),
        "Observaciones": operation_data.get("observaciones"),
        "Prima": operation_data.get("prima_sin_iva"),
        "Numero_de_cuota": operation_data.get("numero_cuota"),
        "Valor_de_cuota": operation_data.get("pago_total_cuota"),
    }

    return create_record(
        module_api_name="Opeeraciones",
        data=data,
    )


# ============================================================
# BUSCAR ID DE RIESGO
# ============================================================


def get_risk_record_id(
    key_riesgo: str,
) -> str | None:
    """
    Busca un Riesgo utilizando el Key Riesgo
    (campo Name) y retorna su ID.
    """

    if not key_riesgo:
        return None

    token_data = get_zoho_token_data()

    access_token = token_data["access_token"]

    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com",
    )

    url = f"{api_domain}/crm/" f"{ZOHO_API_VERSION}/" "Riesgos/search"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    params = {
        "criteria": f"(Name:equals:{key_riesgo})",
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    if response.status_code == 204:
        return None

    if not response.ok:
        print("\nError buscando Riesgo en Zoho CRM:")
        print(f"Status Code: {response.status_code}")
        print(f"Respuesta: {response.text}")

    response.raise_for_status()

    records = response.json().get(
        "data",
        [],
    )

    if not records:
        return None

    return records[0].get("id")


# ============================================================
# ACTUALIZAR RIESGO
# ============================================================


def update_risk(
    risk_data: dict,
) -> dict | None:

    key_riesgo = risk_data.get("auto_placa")

    if not key_riesgo:
        print("[RIESGO] No se puede actualizar el Riesgo: " "no se encontró la placa.")
        return None

    record_id = get_risk_record_id(
        key_riesgo=key_riesgo,
    )

    if not record_id:
        print(
            f"[RIESGO] No se encontró un Riesgo para "
            f"la placa: {key_riesgo}. "
            "Se continúa el proceso."
        )
        return None

    data = {
        "Tipo_de_riesgo": risk_data.get("tipo_riesgo"),
        "Placa_del_vehiculo": risk_data.get("auto_placa"),
        "Marca_Tipo_Caracter_sticas": risk_data.get("características"),
        "Ciudad": risk_data.get("auto_zona_cirulacion"),
        "Clase": risk_data.get("auto_clase"),
        "Cilindraje_C_C_o_pasajeros": risk_data.get("Cilindraje"),
        "Modelo": risk_data.get("auto_modelo"),
        "Motor": risk_data.get("auto_motor"),
        "Chasis": risk_data.get("auto_chasis"),
        "C_dig_Fasecolda": risk_data.get("auto_fasecolda_cf"),
    }

    return update_record(
        module_api_name="Riesgos",
        record_id=record_id,
        data=data,
    )


# ============================================================
# CREAR ASEGURADO
# ============================================================


def create_insured(
    insured_data: dict,
) -> dict:

    data = {
        "P_liza": insured_data.get("poliza_id"),
        "Ramo": insured_data.get("ramo"),
        "Aseguradora": insured_data.get("aseguradora"),
        "Name": insured_data.get("subriesgo"),
        "Estado": insured_data.get("estado"),
        "Riesgo": insured_data.get("riesgo_id"),
        "Asegurado": insured_data.get("asegurado_id"),
        "Beneficiario": insured_data.get("beneficiario_id"),
        "Endoso": insured_data.get("endoso"),
        "Estado_del_endoso": insured_data.get("estado_del_endoso"),
        "Beneficiario_Oneroso": insured_data.get("beneficiario_oneroso"),
        "Valor_asegurado": insured_data.get("valor_asegurado"),
        "Accesorios": insured_data.get("accesorios"),
        "Blindaje": insured_data.get("blindaje"),
    }

    return create_record(
        module_api_name="Riesgos1",
        data=data,
    )


# ============================================================
# ACTUALIZAR ESTADO DE EXTRACCIÓN DE LA TASK
# ============================================================


def update_task_extraction_status(
    task_id: str,
    status: str,
) -> dict:
    """
    Actualiza el estado de extracción de una Task.

    Si el procesamiento finalizó correctamente,
    también cambia el Status de la Task a Completado.
    """

    data = {
        "Estado_de_extracci_n": status,
    }

    if status == "Finalizado":
        data["Status"] = "Completado"

    return update_record(
        module_api_name="Tasks",
        record_id=task_id,
        data=data,
    )


# ============================================================
# BUSCAR ID Y NOMBRE DE ASEGURADO/BENEFICIARIO
# ============================================================


def get_person_by_identification(identification: str) -> dict | None:
    """
    Busca una persona en Zoho por su número de identificación.
    """

    token_data = get_zoho_token_data()

    access_token = token_data["access_token"]
    api_domain = token_data.get("api_domain", "https://www.zohoapis.com")

    url = f"{api_domain}/crm/{ZOHO_API_VERSION}/Contacts/search"

    params = {"criteria": f"(N_mero_de_ID:equals:{identification})"}

    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    records = data.get("data", [])

    if not records:
        return None

    person = records[0]

    return {
        "id": person.get("id"),
        "name": person.get("Nombre_comercial"),
    }


# ============================================================
# CREA PERSONAS COMO ASEGURADO Y BENEFICIARIO
# ============================================================
def resolve_insured_and_beneficiary(
    asegurado_id: str | None,
    beneficiario_id: str | None,
) -> dict:
    """
    Resuelve los IDs de Zoho correspondientes al asegurado
    y beneficiario.

    Si no existe beneficiario oneroso:
        - asegurado = persona buscada
        - beneficiario = mismo asegurado

    Si existe beneficiario oneroso:
        - asegurado = persona buscada
        - beneficiario = persona buscada
    """

    if not asegurado_id:
        raise ValueError("No se recibió asegurado1_ID.")

    asegurado = get_person_by_identification(asegurado_id)

    if not asegurado:
        raise RuntimeError(
            f"No se encontró en Zoho el asegurado "
            f"con identificación {asegurado_id}."
        )

    # Caso SIN beneficiario oneroso
    if not beneficiario_id:

        return {
            "asegurado_zoho_id": asegurado["id"],
            "asegurado_nombre": asegurado["name"],
            "beneficiario_zoho_id": asegurado["id"],
            "beneficiario_nombre": asegurado["name"],
            "beneficiario_oneroso": None,
            "endoso": ENDOSO_SIN_BENEFICIARIO,
            "estado_del_endoso": None,
        }

    # Caso CON beneficiario oneroso
    beneficiario = get_person_by_identification(beneficiario_id)

    if not beneficiario:
        raise RuntimeError(
            f"No se encontró en Zoho el beneficiario "
            f"con identificación {beneficiario_id}."
        )

    return {
        "asegurado_zoho_id": asegurado["id"],
        "asegurado_nombre": asegurado["name"],
        "beneficiario_zoho_id": beneficiario["id"],
        "beneficiario_nombre": beneficiario["name"],
        "beneficiario_oneroso": beneficiario["name"],
        "endoso": ENDOSO_CON_BENEFICIARIO,
        "estado_del_endoso": ESTADO_DEL_ENDOSO,
    }


# ============================================================
# BUSCAR ID ASEGURADO
# ============================================================
def get_insured_record_id(
    key_alterno_asegurado: str,
) -> str | None:
    """
    Busca un registro en Riesgos1 mediante
    Key_alterno_asegurado.

    Retorna el ID del registro si existe.
    """

    if not key_alterno_asegurado:
        return None

    token_data = get_zoho_token_data()

    access_token = token_data["access_token"]
    api_domain = token_data.get(
        "api_domain",
        "https://www.zohoapis.com",
    )

    url = f"{api_domain}/crm/{ZOHO_API_VERSION}/" "Riesgos1/search"

    params = {
        "criteria": (f"(Key_alterno_asegurado:equals:" f"{key_alterno_asegurado})")
    }

    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    # Zoho puede responder 204 cuando no encuentra registros.
    if response.status_code == 204:
        return None

    response.raise_for_status()

    records = response.json().get("data", [])

    if not records:
        return None

    return records[0].get("id")


# ============================================================
# ACTUALIZAR DATOS DEL ASEGURADO
# ============================================================
def update_insured(
    record_id: str,
    insured_data: dict,
) -> dict:

    data = {
        "Asegurado": insured_data.get("asegurado_id"),
        "Beneficiario": insured_data.get("beneficiario_id"),
        "Riesgo": insured_data.get("riesgo_id"),
        "Valor_asegurado": insured_data.get("valor_asegurado"),
        "Accesorios": insured_data.get("accesorios"),
        "Blindaje": insured_data.get("blindaje"),
    }

    return update_record(
        module_api_name="Riesgos1",
        record_id=record_id,
        data=data,
    )
