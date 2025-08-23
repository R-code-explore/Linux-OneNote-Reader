import requests
from auth import get_token

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
    return resp.text  # retourne du HTML complet

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