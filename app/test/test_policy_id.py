from app.integrations.zoho.task_policy import (
    get_task_policy_data,
)


task_id = "4933790000275856583"

resultado = get_task_policy_data(
    task_id=task_id,
)

print(resultado)