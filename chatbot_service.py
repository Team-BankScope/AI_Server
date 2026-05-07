import os
import requests
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'bank'),
}

# 전체 지식 베이스 (상품 + 사이트 가이드)
knowledge_base: list[str] = []


def load_site_guide() -> list[str]:
    guide_path = os.path.join(os.path.dirname(__file__), 'site_guide.txt')
    try:
        with open(guide_path, encoding='utf-8') as f:
            content = f.read()
        chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
        print(f"[알림] 사이트 가이드 {len(chunks)}개 문단 로드 완료")
        return chunks
    except Exception as e:
        print(f"[WARN] 사이트 가이드 로드 실패: {e}")
        return []


def build_knowledge_base():
    global knowledge_base
    print("[알림] 지식 베이스를 구축합니다...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT product_name, description, base_interest_rate, max_interest_rate, "
            "product_category, target_type FROM financial_product WHERE is_active = 1"
        )
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        product_texts = [
            f"상품명: {p['product_name']}, 카테고리: {p['product_category']}, "
            f"대상: {'법인' if p['target_type'] == 'CORPORATE' else '개인'}, "
            f"기본금리: {p['base_interest_rate']}%, 최고금리: {p['max_interest_rate']}%, "
            f"설명: {p['description']}"
            for p in products
        ]
    except Exception as e:
        print(f"[WARN] 상품 로드 실패: {e}")
        product_texts = []

    guide_texts = load_site_guide()
    knowledge_base = product_texts + guide_texts
    print(f"성공: 상품 {len(product_texts)}개 + 가이드 {len(guide_texts)}개 지식 베이스 구축 완료")


def keyword_search(query: str, k: int = 6) -> list[str]:
    """키워드 기반 관련 문서 검색 (임베딩 API 불필요)"""
    query_words = set(query.replace('?', '').replace('요', '').split())
    scores = []
    for text in knowledge_base:
        score = sum(1 for word in query_words if word in text)
        scores.append((score, text))
    scores.sort(key=lambda x: x[0], reverse=True)
    # 점수 0인 것도 일부 포함 (가이드 전체 맥락 제공)
    return [text for _, text in scores[:k]]


build_knowledge_base()


def get_chat_response(user_id: int, user_message: str) -> dict:
    if not knowledge_base:
        return {
            "sender": "bot",
            "content": "데이터베이스 연결 오류로 상담이 불가합니다.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    try:
        context_docs = keyword_search(user_message, k=6)
        context = "\n".join(context_docs)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        )
        prompt = (
            "당신은 BankScope 은행 AI 상담원입니다. "
            "아래 참조 데이터를 바탕으로 고객 질문에 친절하고 정확하게 답변하세요. "
            "참조 데이터에 없는 내용은 '직접 방문 또는 고객센터 문의'를 안내하세요.\n\n"
            f"[참조 데이터]\n{context}\n\n"
            f"[고객 질문]\n{user_message}"
        )

        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15
        )
        result = response.json()

        if response.status_code == 200:
            try:
                ai_content = result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                print(f"응답 구조 오류: {result}")
                ai_content = "답변 생성 과정에서 오류가 발생했습니다."
        else:
            print(f"API 실패 ({response.status_code}): {result}")
            ai_content = "죄송합니다. 서비스 응답에 실패했습니다. 잠시 후 다시 시도해주세요."

        return {
            "sender": "bot",
            "content": ai_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"Chat Service Error: {e}")
        return {
            "sender": "bot",
            "content": "처리 중 일시적인 오류가 발생했습니다.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
