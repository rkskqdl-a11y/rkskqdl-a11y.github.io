import os
import requests
import hmac
import hashlib
import json
from time import gmtime, strftime
import random
from urllib.parse import quote_plus

# 쿠팡 API 키는 깃허브 Secrets에서 가져옴
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    print("Error: COUPANG_ACCESS_KEY or COUPANG_SECRET_KEY not found in environment variables.")
    raise ValueError("Missing Coupang API keys. Please set COUPANG_ACCESS_KEY and COUPANG_SECRET_KEY in GitHub Secrets.")

DOMAIN = "https://api-gateway.coupang.com"

def generate_hmac_signature(method, url, secret_key, access_key):
    path, query_string = (url.split("?") + [''])[:2]
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message_to_sign = datetime_gmt + method + path
    if query_string:
        message_to_sign += "?" + query_string
    signature = hmac.new(bytes(secret_key, "utf-8"),
                         message_to_sign.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

def call_coupang_partners_api(method, url_path, params=None, payload=None):
    full_url = url_path
    query_string = ""
    if params:
        query_string = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        full_url += "?" + query_string
    authorization = generate_hmac_signature(method, full_url, SECRET_KEY, ACCESS_KEY)
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json" if payload else "application/x-www-form-urlencoded"
    }
    request_url = f"{DOMAIN}{full_url}"
    if method == "GET":
        response = requests.get(request_url, headers=headers)
    else:  # POST
        response = requests.post(request_url, headers=headers, data=json.dumps(payload) if payload else None)
    response.raise_for_status()
    return response.json()

def search_products(keyword, page=1, limit=30):
    url_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    params = {
        "keyword": keyword,
        "limit": limit,
        "offset": (page-1)*limit
    }
    return call_coupang_partners_api("GET", url_path, params=params)

def generate_deeplinks(coupang_urls):
    url_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    payload = {
        "coupangUrls": coupang_urls
    }
    return call_coupang_partners_api("POST", url_path, payload=payload)

if __name__ == "__main__":
    try:
        SEARCH_KEYWORDS_LIST = [
            "노트북", "캠핑용품", "아이폰15", "무선 이어폰", "게이밍 마우스", 
            "에어프라이어", "로봇청소기", "캡슐커피머신", "전기 주전자", "토스터기",
            # ... (필요하면 더 추가)
        ]
        keyword = random.choice(SEARCH_KEYWORDS_LIST)
        print(f"랜덤 키워드 선택: '{keyword}'")

        search_result = search_products(keyword, limit=30)

        if not search_result.get('data'):
            print("검색 결과 없음")
            exit(0)

        urls = []
        for item in search_result['data']:
            url = item.get('productUrl')
            if url:
                urls.append(url)
                print(f"상품명: {item.get('productName','')} 링크: {url}")

        if not urls:
            print("딥링크 생성할 상품 URL 없음")
            exit(0)

        deeplink_response = generate_deeplinks(urls)
        print("\n--- 생성된 딥링크 ---")
        for link_info in deeplink_response.get('data', []):
            print(f"원본 URL: {link_info.get('originalUrl')}")
            print(f"파트너스 URL: {link_info.get('shortenUrl')}\n")

    except requests.exceptions.HTTPError as err:
        print(f"HTTP 오류: {err.response.status_code} - {err.response.text}")
    except Exception as e:
        print(f"오류 발생: {e}")
