import logging
import secrets

import requests

from fastapi import (
    APIRouter,
    HTTPException,
    Header,
    status,
)
from fastapi.encoders import jsonable_encoder
from app.api.models import RenewalWebhook
from app.services.renewal_service import process_renewal
from app.integrations.zoho.task_policy import (
    get_task_policy_data,
)
from app.config.settings import WEBHOOK_SECRET

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)


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
    Recibe solicitudes de renovación desde Zoho CRM.

    Registra eventos operativos para facilitar
    el diagnóstico desde Dokploy.
    """

    # ========================================================
    # 1. VALIDAR AUTENTICACIÓN
    # ========================================================

    if x_webhook_secret is None or not secrets.compare_digest(
        x_webhook_secret,
        WEBHOOK_SECRET,
    ):
        logger.warning("Solicitud de webhook no autorizada.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook no autorizado.",
        )

    # ========================================================
    # 2. OBTENER DATOS DEL WEBHOOK
    # ========================================================

    webhook_data = payload.model_dump()

    task_id = webhook_data["task_id"]

    logger.info(
        "Inicio procesamiento renovación | task_id=%s",
        task_id,
    )

    # ========================================================
    # 3. CONSULTAR PÓLIZA RELACIONADA
    # ========================================================

    try:

        logger.info(
            "Consultando póliza relacionada | task_id=%s",
            task_id,
        )

        policy_data = get_task_policy_data(
            task_id=task_id,
        )

        logger.info(
            "Póliza relacionada recuperada | task_id=%s",
            task_id,
        )

    except ValueError as exc:

        logger.warning(
            "Validación fallida al recuperar póliza | " "task_id=%s | motivo=%s",
            task_id,
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except requests.RequestException:

        logger.exception(
            "Error HTTP consultando Zoho CRM | task_id=%s",
            task_id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=("No fue posible consultar los datos " "de la póliza en Zoho CRM."),
        )

    except (RuntimeError, KeyError, TypeError):

        logger.exception(
            "Error recuperando póliza relacionada | " "task_id=%s",
            task_id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=("No fue posible recuperar la póliza " "relacionada con la tarea."),
        )

    # ========================================================
    # 4. COMPLETAR DATOS DEL WEBHOOK
    # ========================================================

    webhook_data.update(policy_data)

    # ========================================================
    # 5. PROCESAR RENOVACIÓN
    # ========================================================

    logger.info(
        "Iniciando servicio de renovación | task_id=%s",
        task_id,
    )

    try:

        result = process_renewal(
            webhook_data=webhook_data,
        )

    except Exception:

        logger.exception(
            "Excepción inesperada durante renovación | " "task_id=%s",
            task_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Error interno durante la renovación.",
        )

    # ========================================================
    # 6. VALIDAR RESULTADO
    # ========================================================

    if result.get("estado") == "Finalizado con error":

        logger.error(
            "Renovación fallida | " "execution_id=%s | " "task_id=%s | " "etapa=%s",
            result.get("execution_id"),
            task_id,
            result.get("etapa"),
        )

        raise HTTPException(
            status_code=500,
            detail=jsonable_encoder(result),
        )

    # ========================================================
    # 7. REGISTRAR FINALIZACIÓN
    # ========================================================

    logger.info(
        "Renovación finalizada correctamente | " "execution_id=%s | " "task_id=%s",
        result.get("execution_id"),
        task_id,
    )

    return result
