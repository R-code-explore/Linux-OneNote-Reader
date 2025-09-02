import os
import json
import requests
import msal
from bs4 import BeautifulSoup

# ---------- Config Microsoft Graph / MSAL ----------
GRAPH_URL = "https://graph.microsoft.com/v1.0/me/onenote"

CLIENT_ID = "Your CLient ID"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Notes.ReadWrite.All"]

CACHE_FILE = "token_cache.bin"


# ---------- Cache MSAL ----------
def _load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())


# ---------- Auth ----------
def get_token():
    cache = _load_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=cache
    )

    # 1) tentative silencieuse depuis le cache
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]

    # 2) sinon device code flow (une seule fois normalement)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("Device flow initiation failed")
    print(f"To sign in, open {flow['verification_uri']} and enter code: {flow['user_code']}")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        _save_cache(cache)
        return result["access_token"]

    raise Exception("Authentication failed: %s" % json.dumps(result, indent=2))


# ---------- Helpers HTTP (Graph) ----------
def _auth_headers(extra=None):
    h = {"Authorization": f"Bearer {get_token()}"}
    if extra:
        h.update(extra)
    return h


def graph_get_json(url):
    resp = requests.get(url, headers=_auth_headers())
    resp.raise_for_status()
    return resp.json()


def graph_get_text(url):
    resp = requests.get(url, headers=_auth_headers())
    resp.raise_for_status()
    return resp.text


def graph_post(url, payload=None, headers=None):
    resp = requests.post(url, headers=_auth_headers(headers), data=payload)
    resp.raise_for_status()
    return resp.json() if resp.text else None


def graph_patch(url, operations_json, etag_required=True):
    """
    Envoie les opérations PATCH OneNote (JSON array) sur /pages/{id}/content.
    Ajoute automatiquement l'en-tête If-Match avec l'ETag courant si etag_required=True.
    """
    extra_headers = {"Content-Type": "application/json"}
    if etag_required:
        etag = get_page_etag(_extract_page_id_from_url(url))
        extra_headers["If-Match"] = etag

    resp = requests.patch(url, headers=_auth_headers(extra_headers), data=json.dumps(operations_json))
    resp.raise_for_status()
    # 204 No Content attendu sur succès
    return True


def _extract_page_id_from_url(url: str) -> str:
    # simple extraction pour .../pages/{id}/content
    parts = url.split("/pages/")
    if len(parts) > 1:
        tail = parts[1]
        return tail.split("/")[0]
    return ""


# ---------- OneNote: lecture ----------
def get_notebooks():
    data = graph_get_json(f"{GRAPH_URL}/notebooks")
    return data.get("value", [])


def get_sections(notebook_id):
    data = graph_get_json(f"{GRAPH_URL}/notebooks/{notebook_id}/sections")
    return data.get("value", [])


def get_pages(section_id):
    data = graph_get_json(f"{GRAPH_URL}/sections/{section_id}/pages")
    return data.get("value", [])


def get_page_metadata(page_id):
    """Retourne le JSON d'une page (inclut eTag)."""
    return graph_get_json(f"{GRAPH_URL}/pages/{page_id}")


def get_page_etag(page_id):
    """Récupère l'ETag actuel de la page (utilisé dans If-Match pour PATCH)."""
    meta = get_page_metadata(page_id)
    # L'ETag peut être exposé sous 'eTag' (string) ou '@odata.etag' selon versions
    etag = meta.get("eTag") or meta.get("@odata.etag")
    if not etag:
        # fallback via HEAD du contenu (si nécessaire)
        r = requests.head(f"{GRAPH_URL}/pages/{page_id}/content", headers=_auth_headers())
        r.raise_for_status()
        etag = r.headers.get("ETag")
    if not etag:
        raise RuntimeError("Impossible de récupérer l'ETag de la page.")
    return etag


def get_page_content(page_id):
    """HTML brut (sans IDs)."""
    return graph_get_text(f"{GRAPH_URL}/pages/{page_id}/content")


def get_page_content_with_ids(page_id):
    """HTML avec data-id injectés par Graph pour cibler les éléments dans un PATCH."""
    return graph_get_text(f"{GRAPH_URL}/pages/{page_id}/content?includeIDs=true")


# ---------- OneNote: écriture / modification ----------
def create_page(section_id, title, content_html):
    """
    Crée une page dans la section donnée.
    content_html : fragment HTML du <body> (par ex: "<h1>...</h1><p>...</p>")
    """
    url = f"{GRAPH_URL}/sections/{section_id}/pages"
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
</head>
<body>
    {content_html}
</body>
</html>"""
    headers = {"Content-Type": "application/xhtml+xml"}
    return graph_post(url, payload=html_body.encode("utf-8"), headers=headers)


def replace_page_body(page_id, new_body_html):
    """
    Remplace entièrement le contenu du <body> de la page.
    """
    url = f"{GRAPH_URL}/pages/{page_id}/content"
    ops = [{
        "target": "body",
        "action": "replace",
        "content": new_body_html
    }]
    return graph_patch(url, ops, etag_required=True)


def append_to_body(page_id, html_fragment):
    """
    Ajoute du contenu à la fin du <body>.
    """
    url = f"{GRAPH_URL}/pages/{page_id}/content"
    ops = [{
        "target": "body",
        "action": "append",
        "content": html_fragment
    }]
    return graph_patch(url, ops, etag_required=True)


def prepend_to_body(page_id, html_fragment):
    """
    Ajoute du contenu au début du <body>.
    """
    url = f"{GRAPH_URL}/pages/{page_id}/content"
    ops = [{
        "target": "body",
        "action": "prepend",
        "content": html_fragment
    }]
    return graph_patch(url, ops, etag_required=True)


def replace_element(page_id, element_id, new_html_fragment):
    """
    Remplace un élément précis (#element_id) par du nouveau HTML.
    Nécessite d'avoir récupéré le contenu avec ?includeIDs=true pour connaître l'ID.
    """
    url = f"{GRAPH_URL}/pages/{page_id}/content"
    ops = [{
        "target": f"#{element_id}",
        "action": "replace",
        "content": new_html_fragment
    }]
    return graph_patch(url, ops, etag_required=True)


def delete_element(page_id, element_id):
    """
    Supprime un élément précis (#element_id).
    """
    url = f"{GRAPH_URL}/pages/{page_id}/content"
    ops = [{
        "target": f"#{element_id}",
        "action": "delete"
    }]
    return graph_patch(url, ops, etag_required=True)


def insert_html(page_id, element_id, html_fragment, position="after"):
    """
    Insère du HTML par rapport à un élément (#element_id).
    position: "before" | "after"
    """
    if position not in ("before", "after"):
        raise ValueError("position must be 'before' or 'after'")
    url = f"{GRAPH_URL}/pages/{page_id}/content"
    ops = [{
        "target": f"#{element_id}",
        "action": "insert",
        "position": position,
        "content": html_fragment
    }]
    return graph_patch(url, ops, etag_required=True)


# ---------- Nettoyage / présentation HTML ----------
def clean_onenote_html(raw_html: str) -> str:
    """
    Simplifie le HTML OneNote (supprime scripts/styles, styles inline lisibles).
    Idéal pour QWebEngineView (ou QTextBrowser avec HTML simple).
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    body = soup.body if soup.body else soup

    # Supprimer scripts & styles
    for tag in body(["script", "style"]):
        tag.decompose()

    # Styles inline légers
    for p in body.find_all("p"):
        p["style"] = "margin:6px 0; font-family:Arial; font-size:12pt; color:#333;"

    for h in body.find_all(["h1", "h2", "h3"]):
        h["style"] = "margin-top:12px; font-weight:bold; font-family:Arial;"

    for img in body.find_all("img"):
        img["style"] = "max-width:90%; border-radius:8px; margin:8px 0;"

    for a in body.find_all("a"):
        a["style"] = "color:#0066cc; text-decoration:none;"

    return str(body)