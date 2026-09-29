import requests

ACCESS_TOKEN = "1000.1a005dd1c50aa923d65d831fc246b62b.45a49f348fcbd07fd56bb186162d4809"

task_id = "4933790000274945102"

url = f"https://www.zohoapis.com/crm/v8/Tasks/{task_id}"

headers = {
    "Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"
}

params = {
    "fields": "id,Subject,Status,Priority,Due_Date,Owner,Description,Created_Time,Modified_Time"
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Status:", response.status_code)
print("\nRespuesta:")
print(response.json())