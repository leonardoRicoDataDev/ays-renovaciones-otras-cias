import requests

ACCESS_TOKEN = "1000.ee81cbad7ba30e9bfffee74fbea47ce8.d8a2c83d379af64eb612453fcbb999d5"

task_id = "4933790000274945102"
attachment_id = "4933790000274945129"

url = (
    f"https://www.zohoapis.com/crm/v8/"
    f"Tasks/{task_id}/Attachments/{attachment_id}"
)

headers = {
    "Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"
}

response = requests.get(
    url,
    headers=headers
)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Tamaño:", len(response.content), "bytes")

if response.status_code == 200:
    with open("archivo_adjunto.jpeg", "wb") as archivo:
        archivo.write(response.content)

    print("Archivo descargado correctamente.")
else:
    print(response.text)