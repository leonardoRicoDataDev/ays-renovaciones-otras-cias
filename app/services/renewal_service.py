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

    print("=" * 60)
    print("INICIO DEL PROCESAMIENTO")
    print("=" * 60)

    print(f"\nTask ID utilizado: {task_id}")

    caratula_path = None
    recibo_path = None

    try:

        # ====================================================
        # 1. OBTENER Y DESCARGAR ADJUNTOS
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_EXTRACCION)

        attachments = get_task_attachments(task_id)

        print(f"\nAdjuntos encontrados: {len(attachments)}")

        for attachment in attachments:

            attachment_id = attachment.get("id")
            file_name = attachment.get("File_Name")

            print(f"\nAdjunto: {file_name}")

            file_path = download_task_attachment(
                task_id=task_id,
                attachment_id=attachment_id,
                file_name=file_name,
            )

            print(f"Archivo descargado: " f"{file_path.resolve()}")

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

        print("\n" + "=" * 60)
        print("EXTRACCIÓN DE DATOS")
        print("=" * 60)

        extracted_data = extract_from_documents(
            caratula_path=caratula_path,
            recibo_path=recibo_path,
        )

        print("\nDatos extraídos:")
        print(extracted_data)

        # ====================================================
        # 4. TRANSFORMAR DATOS
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_TRANSFORMACION)

        print("\n" + "=" * 60)
        print("TRANSFORMACIÓN DE DATOS")
        print("=" * 60)

        transformed_data = transform_data(
            extracted_data=extracted_data,
            webhook_data=webhook_data,
        )

        print("\nDatos transformados:")
        print(transformed_data)

        policy_data = transformed_data["poliza"]

        # Inicialmente no existe una nueva póliza.
        new_policy_id = None

        # ====================================================
        # 5. ACTUALIZAR / CREAR PÓLIZA
        # ====================================================

        if transformed_data["action"] == "create":

            controller.actualizar_etapa(ProcessController.ETAPA_CREAR_POLIZA)

            print("\n" + "=" * 60)
            print("CREACIÓN DE PÓLIZA")
            print("=" * 60)

            zoho_policy_response = create_policy(
                policy_data=policy_data,
            )

            print("\nRespuesta de Zoho:")
            print(zoho_policy_response)

            # ================================================
            # OBTENER ID DE LA NUEVA PÓLIZA
            # ================================================

            new_policy_id = zoho_policy_response["data"][0]["details"]["id"]

            print(f"\nID de nueva póliza: " f"{new_policy_id}")

            # ================================================
            # ACTUALIZAR PÓLIZA REEMPLAZADA
            # ================================================

            print("\n" + "=" * 60)
            print("ACTUALIZACIÓN DE PÓLIZA REEMPLAZADA")
            print("=" * 60)

            replaced_policy_response = update_replaced_policy(
                record_id=webhook_data["poliza_id"]
            )

            print("\nRespuesta de Zoho:")
            print(replaced_policy_response)

        else:

            controller.actualizar_etapa(ProcessController.ETAPA_ACTUALIZAR_POLIZA)

            print("\n" + "=" * 60)
            print("ACTUALIZACIÓN DE PÓLIZA")
            print("=" * 60)

            zoho_policy_response = update_policy(
                record_id=webhook_data["poliza_id"],
                policy_data=policy_data,
            )

            print("\nRespuesta de Zoho:")
            print(zoho_policy_response)

        # ====================================================
        # 6. CREAR OPERACIÓN
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_CREAR_OPERACION)

        print("\n" + "=" * 60)
        print("CREACIÓN DE OPERACIÓN")
        print("=" * 60)

        operation_data = build_operation_data(
            extracted_data=extracted_data,
            webhook_data=webhook_data,
            new_policy_id=new_policy_id,
        )

        print("\nDatos de Operación:")
        print(operation_data)

        zoho_operation_response = create_operation(
            operation_data=operation_data,
        )

        print("\nRespuesta de Zoho:")
        print(zoho_operation_response)

        # ====================================================
        # 7. ACTUALIZAR RIESGO
        # ====================================================

        controller.actualizar_etapa(ProcessController.ETAPA_ACTUALIZAR_RIESGO)

        print("\n" + "=" * 60)
        print("ACTUALIZACIÓN DE RIESGO")
        print("=" * 60)

        risk_data = transformed_data["riesgo"]

        print("\nDatos de Riesgo:")
        print(risk_data)

        zoho_risk_response = update_risk(
            risk_data=risk_data,
        )

        if zoho_risk_response is not None:

            print("\nRespuesta de Zoho:")
            print(zoho_risk_response)

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
                f"para la placa "
                f"{risk_data['auto_placa']}."
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

            print("\n" + "=" * 60)
            print("CREACIÓN DE ASEGURADO")
            print("=" * 60)

            insured_data = build_insured_data(
                webhook_data=webhook_data,
                new_policy_id=new_policy_id,
                risk_id=risk_id,
                person_data=person_data,
                risk_data=risk_data,
            )

            print("\nDatos de Asegurado:")
            print(insured_data)

            zoho_insured_response = create_insured(
                insured_data=insured_data,
            )

            print("\nRespuesta de Zoho:")
            print(zoho_insured_response)

        # ====================================================
        # CASO 2:
        # LA PÓLIZA YA EXISTE
        # ACTUALIZAR ASEGURADO
        # ====================================================

        else:

            print("\n" + "=" * 60)
            print("ACTUALIZACIÓN DE ASEGURADO")
            print("=" * 60)

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

            print("\nKey alterno del asegurado:")
            print(insured_key)

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

            print("\nID del asegurado encontrado:")
            print(insured_record_id)

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

            print("\nDatos de Asegurado:")
            print(insured_data)

            # ------------------------------------------------
            # ACTUALIZAR ASEGURADO
            # ------------------------------------------------

            zoho_insured_response = update_insured(
                record_id=insured_record_id,
                insured_data=insured_data,
            )

            print("\nRespuesta de Zoho:")
            print(zoho_insured_response)

        # ====================================================
        # 9. PROCESAMIENTO FINALIZADO
        # ====================================================

        controller.finalizar()

        print("\n" + "=" * 60)
        print("PROCESAMIENTO FINALIZADO")
        print("=" * 60)

    except Exception as e:

        controller.finalizar_con_error(
            etapa=controller.etapa,
            motivo=str(e),
        )

        print(f"\nError durante el procesamiento: {e}")

    # ========================================================
    # 10. ACTUALIZAR ESTADO DE LA TASK
    # ========================================================

    try:

        controller_data = controller.get_data()

        print("\n" + "=" * 60)
        print("ACTUALIZACIÓN DEL ESTADO DE EXTRACCIÓN")
        print("=" * 60)

        print("\nEstado final:")
        print(controller_data)

        zoho_status_response = update_task_extraction_status(
            task_id=task_id,
            status=controller.estado,
        )

        print("\nRespuesta de Zoho:")
        print(zoho_status_response)

    except Exception as e:

        print("\nError actualizando el estado " f"de la tarea: {e}")

    finally:

        # ====================================================
        # 11. LIMPIEZA DE ARCHIVOS TEMPORALES
        # ====================================================

        print("\n" + "=" * 60)
        print("LIMPIEZA")
        print("=" * 60)

        if caratula_path is not None:
            caratula_path.unlink(missing_ok=True)

        if recibo_path is not None:
            recibo_path.unlink(missing_ok=True)

        print("Archivos temporales eliminados.")

    # ========================================================
    # RESULTADO DEL PROCESAMIENTO
    # ========================================================

    return controller.get_data()
