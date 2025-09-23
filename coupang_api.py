import os
import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
import random
from urllib.parse import urlencode, quote_plus
import re
import sys
import xml.etree.ElementTree as ET # XML 파싱용
from xml.dom import minidom # XML 예쁘게 저장용 (xmlns 중복 방지)
from datetime import datetime

# 쿠팡 API 키 환경변수에서 불러옴 (GitHub Secrets에 설정!)
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    raise ValueError("COUPANG_ACCESS_KEY와 COUPANG_SECRET_KEY를 GitHub Secrets에 꼭 설정해라!")

DOMAIN = "https://api-gateway.coupang.com"

# 사이트맵 관련 설정
SITEMAP_PATH = 'sitemap.xml'
SITE_BASE_URL = 'https://rkskqdl-a11y.github.io/' # 너의 깃허브 페이지 기본 URL
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9" # 사이트맵 네임스페이스 정의

# XML 네임스페이스를 ElementTree에 미리 등록 (ns0: 방지)
ET.register_namespace('', SITEMAP_NAMESPACE)

# HMAC 서명 생성 함수
def generate_hmac(method, url_for_hmac, secret_key, access_key):
    path, *query = url_for_hmac.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    signature = hmac.new(bytes(secret_key, 'utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

# 쿠팡 API 호출 함수
def call_coupang_api(method, api_path, query_params=None, body=None):
    url_for_hmac = api_path
    if query_params:
        query_str = urlencode(query_params, quote_via=quote_plus)
        url_for_hmac = f"{api_path}?{query_str}"
    authorization = generate_hmac(method, url_for_hmac, SECRET_KEY, ACCESS_KEY)
    full_url = f"{DOMAIN}{url_for_hmac}"
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    if method == "GET":
        resp = requests.get(full_url, headers=headers)
    else:
        resp = requests.post(full_url, headers=headers, data=json.dumps(body))
    resp.raise_for_status() # HTTP 에러 발생 시 예외 발생
    return resp.json()

# 상품 검색 API 함수
def search_products(keyword, page=1, limit=10):
    api_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    params = {"keyword": keyword, "limit": limit, "offset": (page-1)*limit}
    return call_coupang_api("GET", api_path, params)

# HTML 페이지 생성 함수 (세련된 스타일, 풍부한 정보, 쿠팡 글자 제거, 이미지 링크, '실구매후기' 버튼 추가)
def create_html(product):
    name = product.get('productName', '상품명 없음')
    url = product.get('productUrl', '#')
    img = product.get('productImage', 'https://via.placeholder.com/400x300?text=이미지+없음') # 이미지 없을 때 표시
    price = product.get('productPrice', 0)
    category = product.get('categoryName', '정보 없음')
    rank = product.get('rank', 'N/A')
    
    # 배송 정보와 후기 개수는 이제 HTML에 직접 표시하지 않음 (요청 반영)

    # 파일명으로 사용할 수 없는 문자 제거 및 공백 대체
    safe_name = re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')[:50].strip('_')
    if not safe_name: safe_name = f"product_{hash(name+url) % 1000000}"

    filename = f"{safe_name}.html"
    disclosure = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공합니다." # 대가성 문구에만 '쿠팡'

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
  body {{
    font-family: 'Noto Sans KR', sans-serif;
    max-width: 820px; margin: auto; padding: 20px; background: #fdfdfd; color: #222;
  }}
  h1 {{
    font-weight: 700; font-size: 2.3rem; color: #333; margin-bottom: 20px; text-align: center;
  }}
  .product-img {{
    text-align: center; margin-bottom: 20px;
  }}
  .product-img img {{
    max-width: 100%; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    cursor: pointer; transition: transform 0.3s ease;
  }}
  .product-img img:hover {{
    transform: scale(1.03);
  }}
  .price {{
    font-size: 1.8rem; color: #e64e32; font-weight: 800;
    margin: 15px 0; text-align: center;
  }}
  .detail-info {{
    font-size: 1rem; line-height: 1.6; color: #555;
    border-top: 1px solid #eee; padding-top: 20px; margin-bottom: 30px;
  }}
  .detail-info p {{
    margin: 6px 0;
  }}
  .detail-info strong {{
    color: #ff5a3c;
  }}
  .button-group {{
    display: flex;
    flex-direction: column;
    gap: 15px; /* 버튼 사이 간격 */
    max-width: 320px;
    margin: auto; /* 중앙 정렬 */
    margin-top: 25px; /* 버튼 그룹 상단 여백 */
  }}
  .buy-btn, .review-btn {{
    display: block;
    padding: 16px 0;
    color: #fff;
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.3rem;
    text-align: center;
    text-decoration: none;
    transition: background 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2); /* 공통 그림자 */
  }}
  .buy-btn {{
    background: linear-gradient(90deg, #ff5a3c 0%, #ff7a5a 100%);
    box-shadow: 0 5px 15px rgba(255,90,60,0.6);
  }}
  .buy-btn:hover {{
    background: linear-gradient(90deg, #ff764e 0%, #ff956e 100%);
    box-shadow: 0 8px 20px rgba(255,90,60,0.8);
  }}
  .review-btn {{
    background: linear-gradient(90deg, #5c67f2 0%, #8c96ff 100%); /* 다른 색상 (파란 계열) */
    box-shadow: 0 5px 15px rgba(92,103,242,0.6);
  }}
  .review-btn:hover {{
    background: linear-gradient(90deg, #707bf3 0%, #a0a8ff 100%);
    box-shadow: 0 8px 20px rgba(92,103,242,0.8);
  }}
  .disclosure {{
    font-size: 0.85rem;
    color: #999;
    border-top: 1px solid #eee;
    text-align: center;
    padding-top: 20px;
    margin-top: 40px;
  }}
  @media (max-width: 600px) {{
    body {{
      padding: 15px 10px;
    }}
    h1 {{
      font-size: 1.8rem;
      margin-bottom: 15px;
    }}
    .button-group {{
      max-width: none;
      width: 100%;
    }}
    .buy-btn, .review-btn {{
      padding: 14px 0;
      font-size: 1.1rem;
      border-radius: 10px;
    }}
  }}
</style>
</head>
<body>
  <h1>{name}</h1>
  <div class="product-img">
    <a href="{url}" target="_blank" rel="noopener noreferrer">
      <img src="{img}" alt="{name}">
    </a>
  </div>
  <div class="price">{price:,}원</div>
  <div class="detail-info">
    <p><strong>카테고리:</strong> {category}</p>
    <p><strong>검색 순위:</strong> {rank}위</p>
    <p>실시간 가격 및 최신 정보는 버튼을 눌러 확인하세요.</p>
  </div>
  <div class="button-group">
    <a href="{url}" class="review-btn" target="_blank" rel="nofollow noopener sponsored">실구매후기 보러가기</a>
    <a href="{url}" class="buy-btn" target="_blank" rel="nofollow noopener sponsored">바로 구매하기</a>
  </div>
  <div class="disclosure">{disclosure}</div>
</body>
</html>
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return filename

# --- 사이트맵 자동 업데이트 관련 함수들 ---
# ET.register_namespace는 이미 위에 선언했음 (전역으로 한 번)

def load_sitemap_doc():
    try:
        # 파일을 바이너리 모드(rb)로 읽어서 BOM과 공백 처리
        with open(SITEMAP_PATH, 'rb') as f:
            raw_xml_content = f.read()
        
        # BOM(Byte Order Mark)과 맨 앞 공백 제거 후 UTF-8로 디코딩
        # lstrip(b'\xef\xbb\xbf')는 UTF-8 BOM을 제거. strip()은 맨 앞뒤 공백 제거.
        xml_string = raw_xml_content.lstrip(b'\xef\xbb\xbf').strip().decode('utf-8')

        # 빈 문자열이면 새로운 XML 문서로 처리 (파일이 비었을 때)
        if not xml_string:
            raise ValueError("Sitemap file is empty or corrupted.")

        dom = minidom.parseString(xml_string)
        
        # root element가 urlset이고 올바른 네임스페이스인지 확인
        if dom.documentElement.tagName != 'urlset' or \
           dom.documentElement.getAttribute('xmlns') != SITEMAP_NAMESPACE:
            raise ValueError("Sitemap root element or namespace is invalid.")
            
    except (FileNotFoundError, ValueError, ET.ParseError):
        # 파일 없거나 에러나면 새로 문서 생성
        dom = minidom.Document()
        urlset = dom.createElement('urlset')
        urlset.setAttribute('xmlns', SITEMAP_NAMESPACE) # xmlns 속성을 여기서만 딱! 설정
        dom.appendChild(urlset)
    return dom
def url_exists_in_sitemap_doc(dom_doc, target_url):
    url_elements = dom_doc.getElementsByTagName('url')
    for url_elem in url_elements:
        loc_elem = url_elem.getElementsByTagName('loc')
        if loc_elem and loc_elem[0].firstChild and loc_elem[0].firstChild.nodeValue == target_url:
            return True
    return False

def add_url_to_sitemap_doc(dom_doc, filename):
    full_url = SITE_BASE_URL + filename
    
    if url_exists_in_sitemap_doc(dom_doc, full_url):
        return False  # 이미 있으면 추가 안 함

    urlset_elem = dom_doc.getElementsByTagName('urlset')[0]
    
    url_elem = dom_doc.createElement('url')
    
    loc = dom_doc.createElement('loc')
    loc.appendChild(dom_doc.createTextNode(full_url))
    url_elem.appendChild(loc)
    
    lastmod = dom_doc.createElement('lastmod')
    lastmod.appendChild(dom_doc.createTextNode(datetime.now().strftime('%Y-%m-%d')))
    url_elem.appendChild(lastmod)
    
    changefreq = dom_doc.createElement('changefreq')
    changefreq.appendChild(dom_doc.createTextNode('daily'))
    url_elem.appendChild(changefreq)
    
    priority = dom_doc.createElement('priority')
    priority.appendChild(dom_doc.createTextNode('0.8'))
    url_elem.appendChild(priority)
    
    urlset_elem.appendChild(url_elem)
    
    return True

def save_sitemap_doc(dom_doc):
    # toprettyxml 사용해서 깔끔하게 들여쓰기하고, encoding은 나중에 수동 처리
    pretty_xml_as_bytes = dom_doc.toprettyxml(indent="  ", encoding="utf-8")
    
    # 바이트 스트링을 UTF-8로 디코딩 후 앞뒤 공백 제거 및 파일에 쓰기
    # BOM을 수동으로 제거해줘야 한다면 (b'\xef\xbb\xbf') 이런 식으로 해야 하지만
    # toprettyxml이 utf-8로 인코딩한 결과는 보통 BOM을 포함하지 않음
    # 그래도 혹시 모르니 lstrip()으로 빈 공간만 제거
    pretty_xml_as_string = pretty_xml_as_bytes.decode('utf-8').lstrip() # 맨 앞 공백 제거

    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_as_string)

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    SEARCH_KEYWORDS_LIST = [ # 네가 준 길고 긴 키워드 리스트!
        "노트북", "캠핑용품", "아이폰15", "무선 이어폰", "게이밍 마우스",
        "에어프라이어", "로봇청소기", "캡슐커피머신", "전기 주전자", "토스터기",
        "믹서기", "제습기", "가습기", "선풍기", "에어컨", "온수매트",
        "블루투스 스피커", "태블릿", "스마트워치", "외장하드", "USB 메모리",
        "핸드폰 케이스", "무선 충전기", "차량용 거치대", "블랙박스", "네비게이션",
        "가정용 빔프로젝터", "사운드바", "TV 스탠드", "모니터암", "키보드", "마우스",
        "게이밍 헤드셋", "웹캠", "콘덴서 마이크", "LED 스탠드", "의자", "책상",
        "선반", "수납함", "커튼", "러그", "침구세트", "베개", "이불", "매트리스 커버",
        "욕실 용품", "주방 용품", "프라이팬", "냄비", "도마", "칼 세트", "식기건조대",
        "세탁세제", "섬유유연제", "청소기", "물걸레 청소기", "스팀다리미", "드라이기",
        "고데기", "전동 칫솔", "구강세정기", "영양제", "비타민", "유산균", "콜라겐",
        "단백질 보충제", "운동복", "요가매트", "덤벨", "자전거", "런닝머신",
        "골프채", "낚싯대", "드론", "액션캠", "미러리스 카메라", "렌즈", "삼각대",
        "백팩", "캐리어", "여행용 파우치", "목베개", "보조배터리", "등산화",
        "운동화", "슬리퍼", "샌들", "선글라스", "모자", "장갑", "양말", "속옷",
        "청바지", "티셔츠", "가디건", "자켓", "코트", "원피스", "스커트", "바지",
        "구두", "워커", "로퍼", "향수", "화장품 세트", "수분 크림", "선크림",
        "샴푸", "린스", "바디워시", "핸드크림", "마스크팩", "네일", "헤어 에센스",
        "공기청정기 필터", "정수기 필터", "세탁기 청소 세제", "세면대 청소 세제",
        "자동차 와이퍼", "에어 필터", "엔진 오일", "타이어 광택제", "세차 용품",
        "장난감", "인형", "블록", "퍼즐", "보드게임", "유모차", "카시트", "아기띠",
        "분유", "기저귀", "물티슈", "젖병", "턱받이", "온도계", "체온계",
        "강아지 사료", "고양이 사료", "배변 패드", "고양이 모래", "캣타워", "강아지 집",
        "책", "소설", "에세이", "자기계발서", "아동 도서", "만화책", "잡지",
        "연필", "볼펜", "노트", "다이어리", "형광펜", "지우개", "파일", "클립"
    ]
    API_CALL_LIMIT_PER_PAGE = 10 # 한 번의 API 호출당 가져올 상품 최대 개수
    TOTAL_PRODUCTS_TO_GENERATE = 30 # 최종 목표: 총 생성할 HTML 파일 개수
    MAX_PAGES_PER_KEYWORD = 3 # 하나의 키워드당 최대 검색할 페이지 수 (30개 채울때까지)
    
    all_products_to_generate = [] # 수집된 모든 상품을 저장할 리스트
    keywords_attempted_set = set() # 이미 시도한 키워드를 저장하여 중복 방지
    
    generated_html_filenames = [] # 새로 생성된 HTML 파일명들을 저장할 리스트

    # 목표 개수만큼 상품을 모을 때까지 반복
    while len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE and \
          len(keywords_attempted_set) < len(SEARCH_KEYWORDS_LIST) * MAX_PAGES_PER_KEYWORD: # 무한 루프 방지용 안전 장치
        
        selected_keyword = random.choice(SEARCH_KEYWORDS_LIST)
        if selected_keyword in keywords_attempted_set: # 이미 시도한 키워드면 건너뛰고 다음 키워드 선택
            continue
        
        print(f"\n랜덤 키워드 선택: '{selected_keyword}'")
        keywords_attempted_set.add(selected_keyword) # 시도한 키워드 세트에 추가

        # 선택된 키워드로 여러 페이지를 검색하여 상품 수집
        for page_num in range(1, MAX_PAGES_PER_KEYWORD + 1):
            if len(all_products_to_generate) >= TOTAL_PRODUCTS_TO_GENERATE:
                break # 이미 목표 개수를 채웠으면 키워드/페이지 루프 중단
            
            print(f"'{selected_keyword}' 상품 검색 시도 (페이지 {page_num})...")
            
            try:
                search_results = search_products(selected_keyword, page=page_num, limit=API_CALL_LIMIT_PER_PAGE)
                
                products_on_current_page = search_results.get('data', {}).get('productData', [])
                
                if not products_on_current_page:
                    print(f"'{selected_keyword}' 키워드 (페이지 {page_num})에 더 이상 상품이 없습니다. 다음 키워드로 이동.")
                    break # 현재 키워드에 더 이상 상품이 없으면 다음 키워드로
                
                for product_item in products_on_current_page:
                    if len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE:
                        all_products_to_generate.append(product_item)
                    else:
                        break # 목표 개수를 채웠으면 상품 추가 중단
                        
                if len(products_on_current_page) < API_CALL_LIMIT_PER_PAGE:
                    # 현재 페이지 상품 수가 요청 limit보다 적으면, 이 키워드에 더 이상 상품이 없다고 판단
                    break

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP 오류 ({selected_keyword}, 페이지 {page_num}): {http_err.response.status_code} - {http_err.response.text}", file=sys.stderr)
                break # HTTP 오류 발생 시 이 키워드는 포기
            except Exception as e:
                print(f"API 호출 중 예기치 않은 오류 ({selected_keyword}, 페이지 {page_num}): {e}", file=sys.stderr)
                break # 다른 오류 발생 시 이 키워드는 포기
        
        if len(all_products_to_generate) >= TOTAL_PRODUCTS_TO_GENERATE:
            print(f"최종 목표 상품 개수({TOTAL_PRODUCTS_TO_GENERATE}개) 달성!")
            break # 전체 목표 달성 시 모든 루프 종료

    # 상품 수집 결과 처리
    if not all_products_to_generate:
        print("최대 시도 후에도 상품 데이터를 하나도 확보하지 못했습니다. 키워드, API 키, 네트워크 상태 등을 확인하세요.", file=sys.stderr)
        sys.exit(1) # 상품이 하나도 없으면 스크립트 종료

    print(f"\n--- 총 {len(all_products_to_generate)}개 상품으로 HTML 파일 생성 및 사이트맵 업데이트 중 ---")
    generated_html_files_count = 0
    for product_data in all_products_to_generate:
        try:
            created_filename = create_html(product_data)
            print(f"-> '{created_filename}' 생성 완료")
            generated_html_filenames.append(created_filename) # 생성된 파일명 리스트에 추가
            generated_html_files_count += 1
        except Exception as e:
            print(f"HTML 파일 생성 실패 (상품: {product_data.get('productName', '불명')}) : {e}", file=sys.stderr)

    # --- 사이트맵 업데이트 실행 ---
    sitemap_dom = load_sitemap_doc() # ElementTree 대신 minidom Document 객체로 불러옴
    sitemap_added_count = 0
    for fname in generated_html_filenames:
        if add_url_to_sitemap_doc(sitemap_dom, fname): # minidom 함수 사용
            sitemap_added_count += 1
    save_sitemap_doc(sitemap_dom) # minidom 함수 사용
    print(f"\n[사이트맵] 새로 추가된 URL {sitemap_added_count}개 반영 완료! (파일: {SITEMAP_PATH})")

    print(f"\n총 {generated_html_files_count}개의 HTML 파일이 성공적으로 생성되었습니다.")
    print("이제 GitHub Actions 워크플로우를 실행하여 웹사이트에 반영하세요! 🎉 (sitemap.xml도 자동으로 업데이트 됩니다!)")
