import requests
from auth import get_token
from bs4 import BeautifulSoup

GRAPH_URL = "https://graph.microsoft.com/v1.0/me/onenote"

def get_notebooks():
    token = get_token()
    resp = requests.get(
        f"{GRAPH_URL}/notebooks",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.json()["value"]

def get_sections(notebook_id):
    token = get_token()
    resp = requests.get(
        f"{GRAPH_URL}/notebooks/{notebook_id}/sections",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.json()["value"]

def get_pages(section_id):
    token = get_token()
    resp = requests.get(
        f"{GRAPH_URL}/sections/{section_id}/pages",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.json()["value"]

def get_page_content(page_id):
    token = get_token()
    resp = requests.get(
        f"{GRAPH_URL}/pages/{page_id}/content",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.text

def clean_onenote_html(raw_html: str) -> str:
    """Simplifie le HTML pour QTextBrowser (sans CSS global)."""
    soup = BeautifulSoup(raw_html, "html.parser")

    body = soup.body if soup.body else soup

    # Supprimer les scripts et styles
    for tag in body(["script", "style"]):
        tag.decompose()

    # Ajouter un peu de style inline
    for p in body.find_all("p"):
        p["style"] = "margin:6px 0; font-family:Arial; font-size:12pt; color:#333;"

    for h in body.find_all(["h1", "h2", "h3"]):
        h["style"] = "margin-top:12px; font-weight:bold; font-family:Arial;"

    for img in body.find_all("img"):
        img["style"] = "max-width:90%; border-radius:8px; margin:8px 0;"

    for a in body.find_all("a"):
        a["style"] = "color:#0066cc; text-decoration:none;"

    return str(body)

#    return style + cleaned_html

#def get_notebooks():
#    token = get_token()
#    resp = requests.get(
#        f"{GRAPH_URL}/notebooks",
#        headers={"Authorization": f"Bearer {token}"}
#    )
#    if resp.status_code == 200:
#        return resp.json()["value"]
#    else:
#        raise Exception(f"Erreur API: {resp.status_code} {resp.text}")
