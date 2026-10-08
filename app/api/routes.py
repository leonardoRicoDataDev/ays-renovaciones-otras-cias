import secrets

from fastapi import APIRouter, HTTPException, Header, status
from fastapi.encoders import jsonable_encoder

from app.api.models import RenewalWebhook
from app.services.renewal_service import process_renewal
from app.config.settings import WEBHOOK_SECRET


router = APIRouter()


@router.post("/webhooks/renewal")
def renewal_webhook(
    payload: RenewalWebhook,
    x_webhook_secret: str | None = Header(default=None),
):
    """
    Recibe los webhooks de renovación enviados por Zoho CRM.

    Valida el secreto compartido antes de ejecutar
    cualquier operación sobre las pólizas.
    """

    # ====================================================
    # 1. VALIDAR AUTENTICACIÓN
    # ====================================================

    if (
        x_webhook_secret is None
        or not secrets.compare_digest(
            x_webhook_secret,
            WEBHOOK_SECRET,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook no autorizado.",
        )

    # ====================================================
    # 2. OBTENER DATOS DEL WEBHOOK
    # ====================================================

    webhook_data = payload.model_dump()

    # ====================================================
    # 3. PROCESAR RENOVACIÓN
    # ====================================================

    result = process_renewal(
        webhook_data=webhook_data,
    )

    # ====================================================
    # 4. VALIDAR RESULTADO
    # ====================================================

    if result.get("estado") == "Finalizado con error":
        raise HTTPException(
            status_code=500,
            detail=jsonable_encoder(result),
        )

    return result