from app.integrations.zoho.attachments import (
    get_task_attachments,
    download_task_attachment,
)

from app.extraction.extractor import extract_from_documents

from app.processing.transformer import (
    transform_data,
    build_operation_data,
    build_insured_data,
    build_insured_key,
)

from app.control.controller import ProcessController

from app.integrations.zoho.crm_records import (
    update_policy,
    create_policy,
    create_operation,
    update_risk,
    update_replaced_policy,
    create_insured,
    get_risk_record_id,
    update_task_extraction_status,
    resolve_insured_and_beneficiary,
    get_insured_record_id,
    update_insured,
)

from app.processing.allianz.allianz_rules import (
    normalizar_numero_poliza_allianz,
)


def process_renewal(webhook_data: dict) -> dict:
    """
    Procesa una renovación recibida mediante webhook.

    El flujo realiza:
    - Descarga de adjuntos de la Task.
    - Extracción de datos.
    - Transformación.
    - Creación o actualización de póliza.
    - Creación de operación.
    - Actualización del riesgo.
    - Creación o actualización del asegurado.
    - Actualización del estado de la Task.

    Args:
        webhook_data:
            Datos recibidos desde el webhook de Zoho.

    Returns:
        Información final de la ejecución.
    """

    # ========================================================
    # DATOS DEL WEBHOOK
    # ========================================================

    task_id = webhook_data["task_id"]

    # ========================================================
    # CONTROLLER
    # ========================================================

    controller = ProcessController(
        task_id=task_id,
        poliza_id=webhook_data.get("poliza_id"),
    )

    controller.iniciar()

    caratula_path = None
    recibo_path = None

    try:

        # ====================================================
        # 1. OBTENER Y DESCARGAR ADJUNTOS
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_EXTRACCION)

        attachments = get_task_attachments(task_id)

        for attachment in attachments:

            attachment_id = attachment.get("id")
            file_name = attachment.get("File_Name")

            file_path = download_task_attachment(
                task_id=task_id,
                attachment_id=attachment_id,
                file_name=file_name,
            )

            file_name_lower = file_name.lower()

            if "caratula" in file_name_lower:
                caratula_path = file_path

            elif "recibo" in file_name_lower:
                recibo_path = file_path

        # ====================================================
        # 2. VALIDAR DOCUMENTOS
        # ====================================================

        if caratula_path is None:
            raise FileNotFoundError("No se encontró la carátula.")

        if recibo_path is None:
            raise FileNotFoundError("No se encontró el recibo.")

        # ====================================================
        # 3. EXTRAER DATOS
        # ====================================================

        extracted_data = extract_from_documents(
            caratula_path=caratula_path,
            recibo_path=recibo_path,
        )

        # ====================================================
        # 4. TRANSFORMAR DATOS
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_TRANSFORMACION)

        transformed_data = transform_data(
            extracted_data=extracted_data,
            webhook_data=webhook_data,
        )

        policy_data = transformed_data["poliza"]

        # Inicialmente no existe una nueva póliza.
        new_policy_id = None

        # ====================================================
        # 5. ACTUALIZAR / CREAR PÓLIZA
        # ====================================================

        if transformed_data["action"] == "create":

            controller.actualizar_etapa(ProcessController.ETAPA_CREAR_POLIZA)

            zoho_policy_response = create_policy(
                policy_data=policy_data,
            )

            # ================================================
            # OBTENER ID DE LA NUEVA PÓLIZA
            # ================================================

            new_policy_id = zoho_policy_response["data"][0]["details"]["id"]

            # ================================================
            # ACTUALIZAR PÓLIZA REEMPLAZADA
            # ================================================

            update_replaced_policy(record_id=webhook_data["poliza_id"])

        else:

            controller.actualizar_etapa(ProcessController.ETAPA_ACTUALIZAR_POLIZA)

            update_policy(
                record_id=webhook_data["poliza_id"],
                policy_data=policy_data,
            )

        # ====================================================
        # 6. CREAR OPERACIÓN
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_CREAR_OPERACION)

        operation_data = build_operation_data(
            extracted_data=extracted_data,
            webhook_data=webhook_data,
            new_policy_id=new_policy_id,
        )

        create_operation(
            operation_data=operation_data,
        )

        # ====================================================
        # 7. ACTUALIZAR RIESGO
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_ACTUALIZAR_RIESGO)

        risk_data = transformed_data["riesgo"]

        update_risk(
            risk_data=risk_data,
        )

        # ====================================================
        # 8. PROCESAR ASEGURADO
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_PROCESAR_ASEGURADO)

        # ----------------------------------------------------
        # OBTENER ID DEL RIESGO
        # ----------------------------------------------------

        risk_id = get_risk_record_id(key_riesgo=risk_data["auto_placa"])

        if not risk_id:
            raise RuntimeError(
                "No fue posible obtener el ID del riesgo "
                f"para la placa {risk_data['auto_placa']}."
            )

        # ----------------------------------------------------
        # RESOLVER ASEGURADO Y BENEFICIARIO
        # ----------------------------------------------------

        person_data = resolve_insured_and_beneficiary(
            asegurado_id=extracted_data.get("asegurado1_ID"),
            beneficiario_id=extracted_data.get("beneficiario_ID"),
        )

        # ====================================================
        # CASO 1:
        # SE CREÓ UNA NUEVA PÓLIZA
        # CREAR ASEGURADO
        # ====================================================

        if transformed_data["action"] == "create":

            insured_data = build_insured_data(
                webhook_data=webhook_data,
                new_policy_id=new_policy_id,
                risk_id=risk_id,
                person_data=person_data,
                risk_data=risk_data,
            )

            create_insured(
                insured_data=insured_data,
            )

        # ====================================================
        # CASO 2:
        # LA PÓLIZA YA EXISTE
        # ACTUALIZAR ASEGURADO
        # ====================================================

        else:

            # ------------------------------------------------
            # CONSTRUIR KEY ALTERNO DEL ASEGURADO
            # ------------------------------------------------

            insured_key = build_insured_key(
                policy_number=(
                    normalizar_numero_poliza_allianz(
                        extracted_data.get("poliza_numero")
                    )
                ),
                ramo=webhook_data.get("ramo"),
                aseguradora=webhook_data.get("aseguradora"),
                asegurado_identification=(extracted_data.get("asegurado1_ID")),
            )

            # ------------------------------------------------
            # BUSCAR ASEGURADO EXISTENTE
            # ------------------------------------------------

            insured_record_id = get_insured_record_id(key_alterno_asegurado=insured_key)

            if not insured_record_id:
                raise RuntimeError(
                    "No se encontró el asegurado con "
                    "Key_alterno_asegurado: "
                    f"{insured_key}."
                )

            # ------------------------------------------------
            # CONSTRUIR DATOS PARA ACTUALIZAR
            # ------------------------------------------------

            insured_data = build_insured_data(
                webhook_data=webhook_data,
                new_policy_id=webhook_data.get("poliza_id"),
                risk_id=risk_id,
                person_data=person_data,
                risk_data=risk_data,
            )

            # ------------------------------------------------
            # ACTUALIZAR ASEGURADO
            # ------------------------------------------------

            update_insured(
                record_id=insured_record_id,
                insured_data=insured_data,
            )

        # ====================================================
        # 9. PROCESAMIENTO FINALIZADO
        # ====================================================

        controller.finalizar()

    except Exception as e:

        controller.finalizar_con_error(
            etapa=controller.etapa,
            motivo=str(e),
        )

    # ========================================================
    # 10. ACTUALIZAR ESTADO DE LA TASK
    # No se hará actualización del estado hasta que se guarde de manera automática los documentos de la tarea.
    # ========================================================
    
    try:
        pass
        # update_task_extraction_status(
        #     task_id=task_id,
        #     status=controller.estado,
        # )

    except Exception:
        # Un error actualizando el estado de la Task
        # no debe reemplazar el resultado del procesamiento.
        pass

    finally:

        # ====================================================
        # 11. LIMPIEZA DE ARCHIVOS TEMPORALES
        # ====================================================

        if caratula_path is not None:
            caratula_path.unlink(missing_ok=True)

        if recibo_path is not None:
            recibo_path.unlink(missing_ok=True)

    # ========================================================
    # RESULTADO DEL PROCESAMIENTO
    # ========================================================

    return controller.get_data()
