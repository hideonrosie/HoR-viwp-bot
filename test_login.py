from utils.api import login, call_api

login()
res = call_api({
    "action": "query",
    "meta": "userinfo",
    "format": "json"
})
print(res)
