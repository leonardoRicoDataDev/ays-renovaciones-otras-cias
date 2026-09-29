import re

def normalizar_numero_poliza_allianz(
    numero_poliza: str | None,
) -> str | None:
    if not numero_poliza:
        return None

    numero = numero_poliza.strip()

    # Tomar únicamente la parte anterior a "/"
    numero = numero.split("/", 1)[0].strip()

    # Eliminar ceros a la izquierda
    numero = numero.lstrip("0")

    return numero or "0"

# ============================================================
# EXTRAER CILINDARJE DE LA VERSION
# ============================================================
def extraer_cilindraje(version: str | None) -> int | None:
    """
    Extrae el cilindraje de la versión.

    Ejemplo:
        SR5-MT 4000CC 4X4 9036085
        -> 4000
    """
    if not version:
        return None

    coincidencia = re.search(r"(\d+)\s*CC\b", version.upper())

    if not coincidencia:
        return None

    return int(coincidencia.group(1))


# ============================================================
# CLASIFICAR CILINDRAJE
# ============================================================
def clasificar_cilindraje(cilindraje: int | None, clase: str | None) -> str | None:
    """
    Clasifica el cilindraje dependiendo de si el riesgo
    corresponde a un automóvil/vehículo o a una motocicleta.
    """

    if cilindraje is None or not clase:
        return None

    clase_normalizada = clase.strip().upper()

    # Motocicletas
    if clase_normalizada == "MOTOCICLETA":
        if cilindraje < 100:
            return "Menos de 100 c.c."
        elif cilindraje <= 200:
            return "De 100 a 200 c.c."
        else:
            return "Más de 200 c.c."

    # Vehículos y furgones
    if clase_normalizada in {
        "AUTOMOVIL",
        "CAMPERO",
        "FURGON",
    }:
        if cilindraje < 1500:
            return "Menos de 1500 c.c."
        elif cilindraje <= 2500:
            return "1500 a 2500 c.c."
        else:
            return "Más de 2500 c.c."


# ============================================================
# CONSTRUCCIÓN DE CARACTERÍSTICAS
# ============================================================
def construir_caracteristicas(
    marca: str | None, tipo: str | None, version: str | None
) -> str | None:
    """
    Construye el campo características a partir de:
    marca + tipo + versión.

    Elimina el código Fasecolda de 7 dígitos de la versión.
    """

    partes = []

    if marca:
        partes.append(marca.strip())

    if tipo:
        partes.append(tipo.strip())

    if version:
        # El código Fasecolda corresponde a 7 dígitos.
        version_limpia = re.sub(r"\b\d{7}\b", "", version)
        version_limpia = re.sub(r"\s+", " ", version_limpia).strip()

        if version_limpia:
            partes.append(version_limpia)

    if not partes:
        return None

    return " ".join(partes).upper()
