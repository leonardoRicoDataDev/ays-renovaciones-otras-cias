from app.integrations.zoho.auth import refresh_access_token

def main():
    try:
        tokens = refresh_access_token()

        print("Access token renovado correctamente.")
        print("API Domain:", tokens.get("api_domain"))
        print("Expira en:", tokens.get("expires_in"), "segundos")

    except Exception as error:
        print("Error al renovar el access token:")
        print(error)

if __name__ == "__main__":
    main()