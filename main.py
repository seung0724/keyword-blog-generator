# 📁 main.py
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from naver_ads_api import get_keyword_stats
from naver_openapi import get_trend_data
import uvicorn
import os
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ Render 배포 환경을 위한 포트 설정 지원
PORT = int(os.environ.get("PORT", 10000))

def get_naver_post_count(keyword):
    headers = {"User-Agent": "Mozilla/5.0"}
    query = requests.utils.quote(keyword)
    url = f"https://search.naver.com/search.naver?where=post&query={query}"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    stat = soup.select_one(".title_desc")
    return stat.get_text(strip=True) if stat else "(수량 정보 없음)"

def extract_keywords_from_text(text, min_length=2):
    words = re.findall(r"\b[가-힣a-zA-Z]{%d,}\b" % min_length, text)
    filtered = [w for w in words if len(w) >= min_length]
    return Counter(filtered).most_common(10)

def get_blog_snippets(keyword, count=30):
    headers = {"User-Agent": "Mozilla/5.0"}
    query = requests.utils.quote(keyword)
    url = f"https://search.naver.com/search.naver?query={query}&where=post"

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    links = []
    for a in soup.select("a[href^='https://blog.naver.com/']"):
        href = a.get("href")
        if href not in links:
            links.append(href)
        if len(links) >= count:
            break

    snippets = []
    all_text = ""
    for link in links:
        try:
            mobile_url = link.replace("blog.naver.com", "m.blog.naver.com")
            res = requests.get(mobile_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            content = soup.select_one(".se-main-container") or soup.select_one(".post_ct")

            if not content:
                iframe = soup.select_one("iframe#__postView")
                if iframe:
                    iframe_src = iframe.get("src")
                    if iframe_src.startswith("/"):
                        iframe_src = f"https://m.blog.naver.com{iframe_src}"
                    iframe_res = requests.get(iframe_src, headers=headers)
                    iframe_soup = BeautifulSoup(iframe_res.text, "html.parser")
                    content = iframe_soup.select_one(".se-main-container") or iframe_soup.select_one(".post_ct")

            text = content.get_text("\n", strip=True) if content else "(본문 없음)"
            snippets.append(text)
            all_text += "\n" + text
        except Exception as e:
            snippets.append(f"(크롤링 실패: {e})")

    keyword_analysis = extract_keywords_from_text(all_text)
    return "\n---\n".join(snippets), keyword_analysis

def generate_prompt(keyword, keyword_data, trend_data, blog_snippets, post_count_info, keyword_analysis):
    keyword_list = "\n".join([f"• {w} ({c}회)" for w, c in keyword_analysis])

    return f'''
🔍 키워드: {keyword}

- 연관 키워드 및 광고 데이터:
{keyword_data}

- 검색 트렌드:
{trend_data}

- 네이버 블로그 발행량:
{post_count_info}

- 인기 블로그 본문:
{blog_snippets}

- 자주 등장한 단어 분석:
{keyword_list}

✍️ 지시: 위 정보를 바탕으로 SEO 최적화된 블로그 글을 AIDA 기법에 따라 공백 제외 1500자 이상, H2 소제목 포함으로 작성해줘.
'''

@app.get("/generate-blog")
def generate_blog_post(keyword: str = Query(...)):
    keyword_data = get_keyword_stats(keyword)
    trend_data = get_trend_data(keyword)
    post_count_info = get_naver_post_count(keyword)
    blog_snippets, keyword_analysis = get_blog_snippets(keyword)
    result = generate_prompt(keyword, keyword_data, trend_data, blog_snippets, post_count_info, keyword_analysis)
    return {"status": "success", "data": result}

@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/generate-blog-ui", response_class=HTMLResponse)
def generate_blog_ui(request: Request, keyword: str = Query(...)):
    keyword_data = get_keyword_stats(keyword)
    trend_data = get_trend_data(keyword)
    post_count_info = get_naver_post_count(keyword)
    blog_snippets, keyword_analysis = get_blog_snippets(keyword)
    result = generate_prompt(keyword, keyword_data, trend_data, blog_snippets, post_count_info, keyword_analysis)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "keyword": keyword,
        "keyword_data": keyword_data,
        "trend_data": trend_data,
        "post_count_info": post_count_info,
        "snippets": blog_snippets,
        "keyword_analysis": keyword_analysis,
        "blog_result": result
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
