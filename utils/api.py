import requests
from utils.config import BOT_USERNAME, BOT_PASSWORD

API_URL = "https://vi.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "ToolforgeBot/1.0 (https://vi.wikipedia.org/wiki/User:%s)" % BOT_USERNAME.split('@')[0]
}

session = requests.Session()


def get_token(type="login"):
    params = {
        "action": "query",
        "meta": "tokens",
        "type": type,
        "format": "json"
    }
    response = session.get(API_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json()["query"]["tokens"][f"{type}token"]


def login():
    login_token = get_token("login")
    data = {
        "action": "login",
        "lgname": BOT_USERNAME,
        "lgpassword": BOT_PASSWORD,
        "lgtoken": login_token,
        "format": "json"
    }
    response = session.post(API_URL, data=data, headers=HEADERS)
    response.raise_for_status()
    result = response.json()
    if result["login"]["result"] != "Success":
        raise Exception(f"Login failed: {result}")
    print("Login successfully")


def get_csrf_token():
    """Lấy CSRF token sau khi đăng nhập"""
    return get_token("csrf")


def call_api(params, method="GET", post_data=None):
    """Gọi API MediaWiki với params và method"""
    if method == "GET":
        response = session.get(API_URL, params=params, headers=HEADERS)
    else:
        response = session.post(API_URL, data=post_data or params, headers=HEADERS)
    response.raise_for_status()
    return response.json()
