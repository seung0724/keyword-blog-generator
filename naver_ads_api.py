# naver_ads_api.py
import time, hmac, hashlib, base64, requests, json, os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("NAVER_API_KEY")
SECRET_KEY = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID = os.getenv("NAVER_CUSTOMER_ID")

def generate_signature(timestamp, method, uri):
    message = f"{timestamp}.{method}.{uri}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def get_keyword_stats(keyword):
    timestamp = str(int(time.time() * 1000))
    uri = "/keywordstool"
    signature = generate_signature(timestamp, "GET", uri)
    
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": API_KEY,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": signature
    }

    params = {
        "hintKeywords": keyword,
        "showDetail": 1
    }

    url = f"https://api.searchad.naver.com{uri}"
    res = requests.get(url, headers=headers, params=params)
    
    if res.status_code != 200:
        return {"error": f"광고 API 호출 실패 - {res.text}"}

    return res.json()
