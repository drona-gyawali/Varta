import requests

url = "http://127.0.0.1:8000/api/v1/rooms/?limit=20&offset=0"

cookies = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmM2EzNjE2NS0xYjhlLTQ1NzMtOGI1Zi1lZmExZjU0ZWEwNTYiLCJleHAiOjE3NjI1ODMwMjd9.fXItYdQg_1d9rkSKXYeliEA-AlQHCwQjbbKoXDu79-8"
}

for i in range(25):
    res = requests.get(url, cookies=cookies)
    print(f"{i+1}: {res.status_code} - {res.text}")
