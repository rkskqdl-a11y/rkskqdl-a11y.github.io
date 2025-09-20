import os
import requests
import hmac
import hashlib
import json
from time import gmtime, strftime

# 쿠팡 API 키는 깃허브 Secrets에서 가져옴
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    print("Error: COUPANG_ACCESS_KEY or COUPANG_SECRET_KEY not found in environment variables.")
    # GitHub Actions에서 에러 발생 시 실패로 처리
    raise ValueError("Missing Coupang API keys. Please set COUPANG_ACCESS_KEY and COUPANG_SECRET_KEY in GitHub Secrets.")


DOMAIN = "https://api-gateway.coupang.com" # 파트너스 API 도메인

def generate_hmac_signature(method, url, secret_key, access_key):
    path, *query = url.split("?")
    
    # 파트너스 API HMAC 서명 생성 규격에 맞춤
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    
    # message 구성 시 path와 query가 둘 다 존재할 경우 합침 (예: /path?query)
    message_content = path
    if query:
        message_content += query[0]

    message = datetime_gmt + method + message_content
    
    signature = hmac.new(bytes(secret_key, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(access_key, datetime_gmt, signature)

# 쿠팡 파트너스 API 호출 함수 (이 함수는 주로 딥링크 생성에 사용될 예정)
def call_coupang_partners_api(method, url, payload=None):
    authorization = generate_hmac_signature(method, url, SECRET_KEY, ACCESS_KEY)
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json"
    }

    full_url = f"{DOMAIN}{url}"
    
    if method == "GET":
        response = requests.get(full_url, headers=headers)
    elif method == "POST":
        response = requests.post(full_url, headers=headers, data=json.dumps(payload) if payload else None)
    
    response.raise_for_status() # 오류 발생 시 예외 발생
    return response.json()


# ---------- 이제 이 API 함수를 이용해서 실제 작업을 할 거야! ----------

# 메인 함수 (테스트용)
if __name__ == "__main__":
    try:
        # 이 예시는 '딥링크' 생성 API 호출 예시임 (네이버 블로그에 올릴 쿠팡 링크를 만드는 작업)
        # 만약 상품 '검색'을 하고 싶으면 다른 파트너스 API 엔드포인트를 사용해야 함
        
        # 상품 검색/추출 로직은 아직 안 넣었지만, 나중에 여기에 추가될 거야.
        # 일단은 테스트를 위해 예시 쿠팡 URL로 딥링크 생성만 해보자.
        
        test_coupang_urls = [
            "https://www.coupang.com/np/search?q=아이폰15&channel=auto", 
            "https://www.coupang.com/vp/products/7690623351?vendorItemId=86851613264"
        ]
        
        deeplink_request_payload = { 
            "coupangUrls": test_coupang_urls
        }
        
        # 딥링크 생성 API 엔드포인트
        DEEPLINK_URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"

        print(f"DeepLink API 호출 시도...")
        deeplink_response = call_coupang_partners_api("POST", DEEPLINK_URL, deeplink_request_payload)
        
        print("\n--- DeepLink 생성 결과 ---")
        print(json.dumps(deeplink_response, indent=4, ensure_ascii=False))

    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
