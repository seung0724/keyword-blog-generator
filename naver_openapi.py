# naver_openapi.py
import requests, os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_trend_data(keyword):
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    body = {
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "timeUnit": "month",
        "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}],
        "device": "pc",
        "ages": ["20", "30", "40"],
        "gender": "f"
    }

    res = requests.post(url, headers=headers, json=body)
    return res.json() if res.status_code == 200 else {"error": res.text}

def get_blog_snippets(keyword):
    url = f"https://openapi.naver.com/v1/search/blog?query={keyword}&display=3"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return []

    data = res.json()
    return [item["description"] for item in data["items"]]
