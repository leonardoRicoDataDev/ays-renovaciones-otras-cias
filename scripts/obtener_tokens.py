from app.integrations.zoho.auth import exchange_authorization_code


def main():
    authorization_code = input("Ingresa el AUTHORIZATION_CODE: ").strip()

    if not authorization_code:
        print("Error: no se ingresó ningún AUTHORIZATION_CODE.")
        return

    try:
        tokens = exchange_authorization_code(authorization_code)

        print("\nTokens obtenidos correctamente.")
        print("Access Token:", tokens.get("access_token"))
        print("Refresh Token:", tokens.get("refresh_token"))
        print("API Domain:", tokens.get("api_domain"))
        print("Expira en:", tokens.get("expires_in"), "segundos")

    except Exception as error:
        print("\nError al obtener los tokens:")
        print(error)


if __name__ == "__main__":
    main()