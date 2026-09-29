from datetime import datetime
from uuid import uuid4


class ProcessController:
    """
    Controla el estado y la trazabilidad de una ejecución.

    El controller mantiene:
    - Estado general de la ejecución.
    - Etapa actual.
    - Motivo asociado a la etapa/error.
    - Fechas de inicio y finalización.
    - Identificadores de la ejecución y de Zoho.
    """

    ESTADO_NO_INICIADO = "No iniciado"
    ESTADO_EN_PROCESO = "En proceso"
    ESTADO_FINALIZADO = "Finalizado"
    ESTADO_FINALIZADO_ERROR = "Finalizado con error"

    ETAPA_INICIO = 0
    ETAPA_EXTRACCION = 1
    ETAPA_TRANSFORMACION = 2
    ETAPA_ACTUALIZAR_POLIZA = 3
    ETAPA_CREAR_POLIZA = 4
    ETAPA_CREAR_OPERACION = 5
    ETAPA_ACTUALIZAR_RIESGO = 6
    ETAPA_CREAR_ASEGURADO = 7
    ETAPA_FIN = 8

    def __init__(
        self,
        task_id: str,
        poliza_id: str | None = None,
    ):
        self.execution_id = str(uuid4())
        self.task_id = task_id
        self.poliza_id = poliza_id

        self.estado = self.ESTADO_NO_INICIADO
        self.etapa = self.ETAPA_INICIO
        self.motivo = None

        self.fecha_inicio = None
        self.fecha_fin = None

    def iniciar(self):
        """Inicia la ejecución."""

        self.estado = self.ESTADO_EN_PROCESO
        self.etapa = self.ETAPA_INICIO
        self.motivo = None
        self.fecha_inicio = datetime.now()

    def actualizar_etapa(
        self,
        etapa: int,
        motivo: str | None = None,
    ):
        """Actualiza la etapa actual del procesamiento."""

        self.etapa = etapa
        self.motivo = motivo

    def finalizar(self):
        """Marca la ejecución como finalizada correctamente."""

        self.estado = self.ESTADO_FINALIZADO
        self.etapa = self.ETAPA_FIN
        self.motivo = "Procesamiento exitoso"
        self.fecha_fin = datetime.now()

    def finalizar_con_error(
        self,
        etapa: int,
        motivo: str,
    ):
        """Marca la ejecución como finalizada con error."""

        self.estado = self.ESTADO_FINALIZADO_ERROR
        self.etapa = etapa
        self.motivo = motivo
        self.fecha_fin = datetime.now()

    def get_data(self) -> dict:
        """
        Retorna la información de la ejecución.

        Estos datos serán posteriormente almacenados
        en la base de datos y utilizados por la interfaz.
        """

        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "poliza_id": self.poliza_id,
            "estado": self.estado,
            "etapa": self.etapa,
            "motivo": self.motivo,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
        }
