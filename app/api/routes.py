import secrets

import requests

from fastapi import (APIRouter, HTTPException, Header, status,)
from fastapi.encoders import jsonable_encoder
from app.api.models import RenewalWebhook
from app.services.renewal_service import process_renewal
from app.integrations.zoho.task_policy import (
    get_task_policy_data,
)
from app.config.settings import WEBHOOK_SECRET

# ============================================================
# ROUTER
# ============================================================

router = APIRouter()

# ============================================================
# WEBHOOK DE RENOVACIONES
# ============================================================

@router.post("/webhooks/renewal")
def renewal_webhook(
    payload: RenewalWebhook,
    x_webhook_secret: str | None = Header(default=None),
):
    """
    Recibe una solicitud de renovación desde Zoho CRM.

    Flujo:

    1. Validar autenticación.
    2. Obtener datos enviados por Zoho.
    3. Consultar la póliza relacionada con la Task.
    4. Completar los datos del webhook.
    5. Ejecutar el procesamiento de renovación.
    6. Retornar el resultado.
    """

    # ========================================================
    # 1. VALIDAR AUTENTICACIÓN
    # ========================================================

    if x_webhook_secret is None or not secrets.compare_digest(
        x_webhook_secret,
        WEBHOOK_SECRET,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook no autorizado.",
        )

    # ========================================================
    # 2. OBTENER DATOS DEL WEBHOOK
    # ========================================================

    webhook_data = payload.model_dump()

    # ========================================================
    # 3. CONSULTAR PÓLIZA RELACIONADA
    # ========================================================

    try:

        policy_data = get_task_policy_data(
            task_id=webhook_data["task_id"],
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=("No fue posible consultar los datos " "de la póliza en Zoho CRM."),
        ) from exc

    except (RuntimeError, KeyError, TypeError) as exc:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=("No fue posible recuperar la póliza " "relacionada con la tarea."),
        ) from exc

    # ========================================================
    # 4. COMPLETAR DATOS DEL WEBHOOK
    # ========================================================

    webhook_data.update(policy_data)

    # En este punto, webhook_data vuelve a contener
    # los ocho campos que requiere renewal_service.py.

    # ========================================================
    # 5. PROCESAR RENOVACIÓN
    # ========================================================

    result = process_renewal(
        webhook_data=webhook_data,
    )

    # ========================================================
    # 6. VALIDAR RESULTADO
    # ========================================================

    if result.get("estado") == "Finalizado con error":

        raise HTTPException(
            status_code=500,
            detail=jsonable_encoder(result),
        )

    return result
