import msal

CLIENT_ID = "YOUR CLIENT ID"
TENANT_ID = "YOUR TENANT ID"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Notes.ReadWrite.All"]

_app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

_token_cache = None

def get_token():
    global _token_cache
    if _token_cache:
        return _token_cache

    accounts = _app.get_accounts()
    result = None
    if accounts:
        result = _app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = _app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise ValueError("Erreur device flow")
        print(flow["message"])
        result = _app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        _token_cache = result["access_token"]
        return _token_cache
    else:
        raise Exception("Erreur auth: " + str(result))
