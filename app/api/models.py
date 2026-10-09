from pydantic import BaseModel


class RenewalWebhook(BaseModel):
    """
    Modelo de los datos recibidos desde el webhook
    nativo de Zoho CRM.

    El ID y el número de la póliza se obtienen
    posteriormente mediante la API de Zoho.
    """

    task_id: str
    aseguradora: str
    ramo: str
    lider_comercial: str
    tomador_id: str
    tomador_nombre: str
