import base64
import json
import time
from pathlib import Path

from app.config.settings import AZURE_OPENAI_DEPLOYMENT
from app.extraction.prompts import ALLIANZ_MOVILIDAD_EXTRACTION_PROMPT
from app.integrations.azure_openai.client import get_azure_openai_client


def encode_pdf(pdf_path: Path) -> str:
    """
    Lee un archivo PDF y lo convierte a Base64.
    """

    if not pdf_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo no es un PDF: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()

    return base64.b64encode(pdf_bytes).decode("utf-8")


def extract_from_documents(
    caratula_path: Path,
    recibo_path: Path,
) -> dict:
    """
    Envía la carátula de renovación y el recibo
    a Azure OpenAI junto con el prompt de extracción.

    Además, mide:
    - Tiempo de respuesta del modelo.
    - Tokens de entrada.
    - Tokens de salida.
    - Tokens totales.
    """

    # --------------------------------------------------------
    # Preparar archivos
    # --------------------------------------------------------

    caratula_base64 = encode_pdf(caratula_path)
    recibo_base64 = encode_pdf(recibo_path)

    # --------------------------------------------------------
    # Obtener cliente Azure OpenAI
    # --------------------------------------------------------

    client = get_azure_openai_client()

    # --------------------------------------------------------
    # Iniciar medición de tiempo
    # --------------------------------------------------------

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # Enviar documentos + prompt al modelo
    # --------------------------------------------------------

    response = client.responses.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": caratula_path.name,
                        "file_data": (
                            f"data:application/pdf;base64," f"{caratula_base64}"
                        ),
                    },
                    {
                        "type": "input_file",
                        "filename": recibo_path.name,
                        "file_data": (
                            f"data:application/pdf;base64," f"{recibo_base64}"
                        ),
                    },
                    {
                        "type": "input_text",
                        "text": ALLIANZ_MOVILIDAD_EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
        max_output_tokens=16384,
    )

    # --------------------------------------------------------
    # Finalizar medición de tiempo
    # --------------------------------------------------------

    elapsed_time = time.perf_counter() - start_time

    # --------------------------------------------------------
    # Obtener respuesta del modelo
    # --------------------------------------------------------

    result_text = response.output_text.strip()

    # --------------------------------------------------------
    # Obtener consumo de tokens
    # --------------------------------------------------------

    usage = response.usage

    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    total_tokens = usage.total_tokens

    # --------------------------------------------------------
    # Mostrar métricas
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("MÉTRICAS DE EXTRACCIÓN")
    print("=" * 60)

    print(f"Tiempo de extracción: {elapsed_time:.2f} segundos")
    print(f"Tokens de entrada: {input_tokens}")
    print(f"Tokens de salida: {output_tokens}")
    print(f"Tokens totales: {total_tokens}")

    print("=" * 60)

    # --------------------------------------------------------
    # Convertir respuesta a diccionario
    # --------------------------------------------------------

    try:
        result = json.loads(result_text)

    except json.JSONDecodeError as exc:
        raise ValueError("Azure OpenAI no devolvió un JSON válido.") from exc

    return result
