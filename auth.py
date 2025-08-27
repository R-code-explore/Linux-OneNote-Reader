#Old login methond## CLIENT_ID = "YOUR_CLIENT_ID"
#TENANT_ID = "YOUR_TENANT_ID"
#AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
#SCOPES = ["Notes.ReadWrite.All"]
import msal
import os
import atexit
import json

CLIENT_ID = "YOUR_CLIENT_ID"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Notes.ReadWrite.All"]

CACHE_FILE = "token_cache.bin"


def load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        cache.deserialize(open(CACHE_FILE, "r").read())
    return cache


def save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_token():
    cache = load_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=cache
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result:
            save_cache(cache)
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("Device flow initiation failed")

    print(f"To sign in, use a web browser to open {flow['verification_uri']} and enter the code {flow['user_code']}")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        save_cache(cache)
        return result["access_token"]
    else:
        raise Exception("Authentication failed: %s" % json.dumps(result, indent=2))
