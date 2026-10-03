from pydantic import BaseModel


class RenewalWebhook(BaseModel):
    task_id: str
    aseguradora: str
    ramo: str
    lider_comercial: str
    tomador_id: str
    tomador_nombre: str
    poliza_id: str
    poliza_numero_actual: str