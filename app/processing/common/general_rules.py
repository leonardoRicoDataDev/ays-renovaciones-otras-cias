from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.processing.common.cities import CITY_NORMALIZATION, normalizar_clave_ciudad


# ============================================================
# CONSTANTES COMUNES - MOVILIDAD INDIVIDUAL
# ============================================================
NOMBRE_OPERACION = "Renovación"
PARTICIPACION = "100"
COMISION = "12.5"
IVA = "19"
NUMERO_CUOTA = "1"
MEDIO_PAGO = "Otros medios"
TIPO_RIESGO = "Vehículos"
DISENO = "Estándar"
ESTADO_POLIZA = "Vigente"
SUBRIESGO = "1"
ESTADO_ASEGURADO = "Activo"
LAYOUT_POLIZA_MOVILIDAD = "4933790000008397774"
ENDOSO_SIN_BENEFICIARIO = False
ENDOSO_CON_BENEFICIARIO = True
ESTADO_DEL_ENDOSO = "Activo"

# ============================================================
# PERIODICIDADES
# ============================================================
PERIODICIDAD_MESES = {
    "mensual": 1,
    "trimestral": 3,
    "semestral": 6,
    "anual": 12,
}

# ============================================================
# EQUIVALENCIAS EN LIDER
# ============================================================
LIDER_COMERCIAL_EQUIVALENCIAS = {
    "Melissa Restrepo": "Melissa Restrepo Gómez",
    "Sthefanie Lopez": "Sthefanie Lopez Escobar",
    "Elizabeth Lopez": "Elizabeth López Moreno",
    "Ana María Duque": "Ana Maria Duque Bran",
    "Angelina Correa Ortiz": "Angelina Correa Ortiz",
}

# ============================================================
# REGLAS DE RIESGOS - MOVILIDAD INDIVIDUAL
# ============================================================

CLASE_RIESGO = {
    "CAMPERO": "Camperos y camionetas",
    "AUTOMOVIL": "Autos familiares",
    "FURGON": "Vehículos de carga o mixto",
    "MOTOCICLETA": "Motos",
}

CATEGORIAS_CILINDRAJE_VEHICULOS = {
    "menor_1500": "Menos de 1500 c.c.",
    "1500_2500": "1500 a 2500 c.c.",
    "mayor_2500": "Más de 2500 c.c.",
}

CATEGORIAS_CILINDRAJE_MOTOS = {
    "menor_100": "Menos de 100 c.c.",
    "100_200": "De 100 a 200 c.c.",
    "mayor_200": "Más de 200 c.c.",
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def normalize_periodicidad(
    periodicidad: str | None,
) -> str | None:

    if not periodicidad:
        return None

    periodicidad_normalizada = periodicidad.strip().lower()

    equivalencias = {
        "mensual": "Mensual",
        "trimestral": "Trimestral",
        "semestral": "Semestral",
        "anual": "Anual",
    }

    return equivalencias.get(periodicidad_normalizada)


def parse_date(
    date_value: str | None,
) -> datetime | None:
    """
    Convierte una fecha en formato dd/mm/yyyy
    a datetime.
    """

    if not date_value:
        return None

    try:
        return datetime.strptime(
            date_value.strip(),
            "%d/%m/%Y",
        )

    except ValueError as exc:
        raise ValueError(
            f"Fecha inválida: {date_value}. " "Se esperaba el formato DD/MM/YYYY."
        ) from exc


def format_date(
    date_value: datetime | None,
) -> str | None:
    """
    Convierte un objeto datetime nuevamente
    al formato DD/MM/YYYY.
    """

    if date_value is None:
        return None

    return date_value.strftime("%d/%m/%Y")


# ============================================================
# DETERMINAR REEMPLAZO DE PÓLIZA
# ============================================================
def determine_policy_replacement(
    extracted_data: dict,
    webhook_data: dict,
) -> bool:
    """
    Compara el número de póliza obtenido de la carátula
    contra el número de póliza actualmente relacionado
    con la tarea.
    """

    extracted_policy_number = extracted_data.get("poliza_numero")

    current_policy_number = webhook_data.get("poliza_numero_actual")

    if not extracted_policy_number:
        raise ValueError(
            "No se encontró el número de póliza " "en los datos extraídos."
        )

    if not current_policy_number:
        raise ValueError(
            "No se recibió el número de póliza actual " "asociado a la tarea."
        )

    extracted_number = str(extracted_policy_number).strip()

    current_number = str(current_policy_number).strip()

    if current_number in extracted_number:
        return False

    return True


# ============================================================
# CALCULAR FECHA FIN DEL CERTIFICADO
# ============================================================
def calculate_certificate_end_date(
    policy_start_date: str | None,
    periodicidad: str | None,
) -> str | None:
    """
    Calcula la fecha de finalización del certificado
    según la periodicidad de la póliza.
    """

    if not policy_start_date or not periodicidad:
        return None

    policy_start = parse_date(policy_start_date)

    periodicidad_normalizada = periodicidad.strip().lower()

    meses = PERIODICIDAD_MESES.get(periodicidad_normalizada)

    if meses is None:
        raise ValueError(f"Periodicidad no soportada: {periodicidad}")

    certificate_end = policy_start + relativedelta(months=meses) - relativedelta(days=1)

    return format_date(certificate_end)


# ============================================================
# DETERMINAR VALOR1 / FECHA 1
# ============================================================
def calculate_first_payment_data(
    extracted_data: dict,
) -> dict:
    """
    Determina los valores de:
    - valor_1
    - fecha_1
    """
    periodicidad = extracted_data.get("poliza_periodicidad")
    periodicidad_normalizada = normalize_periodicidad(periodicidad)
    if periodicidad_normalizada == "Anual":
        return {
            "valor_1": None,
            "fecha_1": None,
        }
    if periodicidad_normalizada in {
        "Mensual",
        "Trimestral",
        "Semestral",
    }:
        return {
            "valor_1": extracted_data.get("poliza_importe_total"),
            "fecha_1": extracted_data.get("poliza_fecha_inicio_vigencia"),
        }
    raise ValueError(f"Periodicidad no soportada: {periodicidad}")


# ============================================================
# DETERMINAR LIDER DE POLIZA NUEVA
# ============================================================
def normalizar_lider_comercial(
    lider_comercial: str | None,
) -> str | None:
    if not lider_comercial:
        return None

    lider_limpio = lider_comercial.strip()

    return LIDER_COMERCIAL_EQUIVALENCIAS.get(
        lider_limpio,
        lider_limpio,
    )


def build_observaciones(
    policy_start_date: str | None,
    periodicidad: str | None,
) -> str | None:
    """
    Construye el campo Observaciones según el año de inicio
    de vigencia y la periodicidad de la póliza.
    """

    if not policy_start_date:
        return None

    start_date = parse_date(policy_start_date)

    if start_date is None:
        return None

    year = start_date.year

    periodicidad_normalizada = normalize_periodicidad(periodicidad)

    if periodicidad_normalizada == "Anual":
        return f"Renovación {year}"

    if periodicidad_normalizada in {
        "Mensual",
        "Trimestral",
        "Semestral",
    }:
        return f"Renovación {year} y cobro 1"

    raise ValueError(f"Periodicidad no soportada: {periodicidad}")


# ============================================================
# FORMA DE PAGO
# ============================================================
def calculate_forma_pago(
    periodicidad: str | None,
) -> str | None:
    """
    Determina la forma de pago según la periodicidad.
    """

    periodicidad_normalizada = normalize_periodicidad(periodicidad)

    if periodicidad_normalizada in {
        "Mensual",
        "Trimestral",
        "Semestral",
    }:
        return "Fraccionado"

    if periodicidad_normalizada == "Anual":
        return "Contado"

    return None


def normalizar_zona_circulacion(zona: str | None) -> str | None:
    if not zona:
        return None

    zona_limpia = zona.strip()

    clave = normalizar_clave_ciudad(zona_limpia)
    zona_normalizada = CITY_NORMALIZATION.get(clave)

    if zona_normalizada:
        return zona_normalizada

    return zona_limpia


# ============================================================
# CLASE
# ============================================================
def transformar_clase(clase: str | None) -> str | None:
    if not clase:
        return None

    clase_normalizada = clase.strip().upper()

    return CLASE_RIESGO.get(clase_normalizada, clase)


def transformar_mayusculas(valor: str | None) -> str | None:
    if not valor:
        return None

    return valor.strip().upper()