from app.processing.common.general_rules import (
    NOMBRE_OPERACION,
    PARTICIPACION,
    COMISION,
    IVA,
    NUMERO_CUOTA,
    MEDIO_PAGO,
    TIPO_RIESGO,
    ESTADO_POLIZA,
    SUBRIESGO,
    ESTADO_ASEGURADO,
    LAYOUT_POLIZA_MOVILIDAD,
    determine_policy_replacement,
    calculate_certificate_end_date,
    calculate_first_payment_data,
    normalizar_lider_comercial,
    calculate_forma_pago,
    transformar_clase,
    transformar_mayusculas,
    normalize_periodicidad,
    normalizar_zona_circulacion,
    build_observaciones,
)

from app.processing.allianz.allianz_rules import (
    normalizar_numero_poliza_allianz,
    extraer_cilindraje,
    clasificar_cilindraje,
    construir_caracteristicas,
)

# ============================================================
# DATOS DE OPERACIONES
# ============================================================


def build_operation_data(
    extracted_data: dict,
    webhook_data: dict,
    new_policy_id: str | None = None,
) -> dict:
    policy_start_date = extracted_data.get("poliza_fecha_inicio_vigencia")

    periodicidad = normalize_periodicidad(extracted_data.get("poliza_periodicidad"))

    forma_pago = calculate_forma_pago(periodicidad)

    certificate_end_date = calculate_certificate_end_date(
        policy_start_date=policy_start_date,
        periodicidad=periodicidad,
    )

    observaciones = build_observaciones(
        policy_start_date,
        periodicidad,
    )

    if forma_pago == "Fraccionado":
        prima_sin_iva = None
        numero_cuota = NUMERO_CUOTA
        pago_total_cuota = extracted_data.get("poliza_importe_total")

    elif forma_pago == "Contado":
        prima_sin_iva = extracted_data.get("poliza_prima_sin_iva")
        numero_cuota = None
        pago_total_cuota = None

    else:
        prima_sin_iva = None
        numero_cuota = None
        pago_total_cuota = None

    # En caso de reemplazo, la operación se relaciona
    # con la nueva póliza.
    key_poliza_id = new_policy_id if new_policy_id else webhook_data.get("poliza_id")

    return {
        "key_poliza_id": key_poliza_id,
        "nombre_operacion": NOMBRE_OPERACION,
        "id_tomador": webhook_data.get("tomador_id"),
        "aseguradora": webhook_data.get("aseguradora"),
        "poliza_fecha_inicio_vigencia": policy_start_date,
        "poliza_fecha_fin_vigencia": extracted_data.get("poliza_fecha_fin_vigencia"),
        "certificado_fecha_inicio_vigencia": policy_start_date,
        "certificado_fecha_fin_vigencia": certificate_end_date,
        "fecha_expedicion": extracted_data.get("poliza_fecha_expedicion"),
        "certificado": extracted_data.get("poliza_N_recibo"),
        "forma_pago": forma_pago,
        "medio_pago": MEDIO_PAGO,
        "periodicidad": periodicidad,
        "participacion": PARTICIPACION,
        "comision": COMISION,
        "iva": IVA,
        "prima_sin_iva": prima_sin_iva,
        "numero_cuota": numero_cuota,
        "pago_total_cuota": pago_total_cuota,
        "observaciones": observaciones,
    }


# ============================================================
# ACTUALIZAR PÓLIZA EXISTENTE
# ============================================================


def build_existing_policy_update(
    extracted_data: dict,
) -> dict:
    """
    Construye los campos que deben actualizarse
    sobre una póliza existente.
    """

    periodicidad = normalize_periodicidad(extracted_data.get("poliza_periodicidad"))

    first_payment_data = calculate_first_payment_data(
        extracted_data=extracted_data,
    )

    return {
        "poliza_fecha_inicio_vigencia": extracted_data.get(
            "poliza_fecha_inicio_vigencia"
        ),
        "poliza_fecha_fin_vigencia": extracted_data.get("poliza_fecha_fin_vigencia"),
        "valor_1": first_payment_data["valor_1"],
        "fecha_1": first_payment_data["fecha_1"],
        "plan": extracted_data.get("poliza_plan"),
        "periodicidad": periodicidad,
        "forma_pago": calculate_forma_pago(periodicidad),
        "medio_pago": MEDIO_PAGO,
        "estado_poliza": ESTADO_POLIZA,
    }


# ============================================================
# CREAR PÓLIZA NUEVA
# ============================================================


def build_new_policy_data(
    extracted_data: dict,
    webhook_data: dict,
) -> dict:
    """
    Construye todos los campos necesarios para
    crear una nueva póliza.
    """

    periodicidad = normalize_periodicidad(extracted_data.get("poliza_periodicidad"))

    first_payment_data = calculate_first_payment_data(
        extracted_data=extracted_data,
    )

    return {
        "id_tomador": webhook_data.get("tomador_id"),
        "reemplaza_poliza_actual": True,
        "key_id_poliza_actual": webhook_data.get("poliza_id"),
        "num_poliza": normalizar_numero_poliza_allianz(
            extracted_data.get("poliza_numero")
        ),
        "ramo": webhook_data.get("ramo"),
        "aseguradora": webhook_data.get("aseguradora"),
        "poliza_fecha_inicio_vigencia": extracted_data.get(
            "poliza_fecha_inicio_vigencia"
        ),
        "poliza_fecha_fin_vigencia": extracted_data.get("poliza_fecha_fin_vigencia"),
        "lider_comercial": normalizar_lider_comercial(
            webhook_data.get("lider_comercial")
        ),
        "forma_pago": calculate_forma_pago(periodicidad),
        "medio_pago": MEDIO_PAGO,
        "periodicidad": periodicidad,
        "valor_1": first_payment_data["valor_1"],
        "fecha_1": first_payment_data["fecha_1"],
        "plan": extracted_data.get("poliza_plan"),
        "participacion": PARTICIPACION,
        "comision": COMISION,
        "iva": IVA,
        "estado_pliza": ESTADO_POLIZA,
        "layout": LAYOUT_POLIZA_MOVILIDAD,
    }


# ============================================================
# DATOS DE RIESGOS
# ============================================================


def build_risk_data(datos: dict) -> dict:
    clase = datos.get("auto_clase")
    version = datos.get("auto_version")

    cilindraje = extraer_cilindraje(version)

    return {
        "auto_placa": datos.get("auto_placa"),
        "auto_fasecolda_cf": datos.get("auto_fasecolda_cf"),
        "auto_marca": transformar_mayusculas(datos.get("auto_marca")),
        "auto_clase": transformar_clase(clase),
        "auto_tipo": transformar_mayusculas(datos.get("auto_tipo")),
        "auto_zona_cirulacion": normalizar_zona_circulacion(
            datos.get("auto_ciudad_zona_cirulacion")
        ),
        "auto_modelo": datos.get("auto_modelo"),
        "auto_valor_asegurado": datos.get("auto_valor_asegurado"),
        "auto_valor_accesorios": datos.get("auto_valor_accesorios"),
        "auto_motor": transformar_mayusculas(datos.get("auto_motor")),
        "auto_version": transformar_mayusculas(version),
        "auto_chasis": transformar_mayusculas(datos.get("auto_chasis")),
        "auto_valor_blindaje": datos.get("auto_valor_blindaje"),
        "características": construir_caracteristicas(
            datos.get("auto_marca"),
            datos.get("auto_tipo"),
            version,
        ),
        "tipo_riesgo": TIPO_RIESGO,
        "Cilindraje": clasificar_cilindraje(
            cilindraje,
            clase,
        ),
    }


# ============================================================
# DATOS DE ASEGURADO
# ============================================================


def build_insured_data(
    webhook_data: dict,
    new_policy_id: str,
    risk_id: str,
    person_data: dict,
) -> dict:

    return {
        "poliza_id": new_policy_id,
        "ramo": webhook_data.get("ramo"),
        "aseguradora": webhook_data.get("aseguradora"),
        "subriesgo": SUBRIESGO,
        "estado": ESTADO_ASEGURADO,
        "riesgo_id": risk_id,

        "asegurado_id": person_data.get("asegurado_zoho_id"),
        "beneficiario_id": person_data.get("beneficiario_zoho_id"),

        "endoso": person_data.get("endoso"),
        "estado_del_endoso": person_data.get("estado_del_endoso"),
        "beneficiario_oneroso": person_data.get(
            "beneficiario_oneroso"
        ),
    }


# ============================================================
# FUNCIÓN PRINCIPAL DE TRANSFORMACIÓN
# ============================================================


def transform_data(
    extracted_data: dict,
    webhook_data: dict,
) -> dict:
    """
    Punto de entrada de la transformación.

    Determina si la póliza debe actualizarse
    o si debe crearse una nueva.
    """

    replaces_current_policy = determine_policy_replacement(
        extracted_data=extracted_data,
        webhook_data=webhook_data,
    )

    operations_data = build_operation_data(
        extracted_data=extracted_data,
        webhook_data=webhook_data,
    )

    if replaces_current_policy:
        policy_data = build_new_policy_data(
            extracted_data=extracted_data,
            webhook_data=webhook_data,
        )
        action = "create"

    else:
        policy_data = build_existing_policy_update(
            extracted_data=extracted_data,
        )
        action = "update"

    risk_data = build_risk_data(
        datos=extracted_data,
    )

    return {
        "action": action,
        "replaces_current_policy": replaces_current_policy,
        "operaciones": operations_data,
        "poliza": policy_data,
        "riesgo": risk_data,
    }
