from fastapi import APIRouter

from app.api.models import RenewalWebhook
from app.services.renewal_service import process_renewal

router = APIRouter()

@router.post("/webhooks/renewal")
def renewal_webhook(
    payload: RenewalWebhook,
):
    webhook_data = payload.model_dump()

    result = process_renewal(webhook_data=webhook_data)

    return result
