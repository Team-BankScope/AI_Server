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

def _load_site_guide() -> str:
    guide_path = os.path.join(os.path.dirname(__file__), 'site_guide.txt')
    try:
        with open(guide_path, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[WARN] 사이트 가이드 로드 실패: {e}")
        return ""

def _load_products() -> str:
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
        lines = [
            f"- {p['product_name']} ({p['product_category']}, "
            f"{'법인' if p['target_type'] == 'CORPORATE' else '개인'}): "
            f"기본금리 {p['base_interest_rate']}%, 최고금리 {p['max_interest_rate']}%, "
            f"{p['description']}"
            for p in products
        ]
        return "\n".join(lines)
    except Exception as e:
        print(f"[WARN] 상품 로드 실패: {e}")
        return ""

_SITE_GUIDE = _load_site_guide()
print("[알림] 챗봇 사이트 가이드 로드 완료")


def get_chat_response(user_id: int, user_message: str) -> dict:
    try:
        products_text = _load_products()

        context = f"[사이트 이용 가이드]\n{_SITE_GUIDE}"
        if products_text:
            context += f"\n\n[금융 상품 목록]\n{products_text}"

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        )
        prompt = (
            "당신은 BankScope 은행 AI 상담원입니다. "
            "아래 참조 데이터를 바탕으로 고객 질문에 친절하고 정확하게 답변하세요. "
            "참조 데이터에 없는 내용은 '직접 방문 또는 고객센터 문의'를 안내하세요.\n\n"
            f"{context}\n\n"
            f"[고객 질문]\n{user_message}"
        )

        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
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
