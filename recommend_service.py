import joblib
import pandas as pd
import mysql.connector

try:
    model = joblib.load('product_model.pkl')
    print("상품 추천 모델 로딩 성공")
except Exception as e:
    print(f"상품 추천 모델 로딩 실패: {e}")
    model = None

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'test1234',
    'database': 'bank'
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error:
        return None

PRODUCT_MAP = {
    0: {
        "product": "BankScope 입출금통장",
        "reason": "거래가 활발한 고객님께 수수료 면제 혜택 상품을 추천드립니다."
    },
    1: {
        "product": "BankScope 정기예금 / 적금",
        "reason": "안정적인 자산을 보유하신 고객님께 높은 금리 예금 상품을 추천드립니다."
    },
    2: {
        "product": "BankScope 신용대출",
        "reason": "고객님의 금융 상황에 맞는 대출 상품을 추천드립니다."
    },
    3: {
        "product": "BankScope 법인 사업자 전용 우대 예금",
        "reason": "기업 고객님 전용 우대 금리 상품입니다."
    }
}

def get_recommendation(user_id: int):
    conn = get_db_connection()
    if not conn:
        return {"result": "FAILURE", "message": "DB 연결 실패"}

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                u.age, u.user_type,
                COALESCE((SELECT SUM(balance) FROM account WHERE user_id = u.id), 0) AS total_balance,
                CASE WHEN EXISTS (
                    SELECT 1 FROM loan WHERE user_id = u.id AND status = 'ACTIVE'
                ) THEN 1 ELSE 0 END AS has_active_loan,
                (SELECT COUNT(*) FROM transaction_history 
                 WHERE user_id = u.id 
                 AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) AS recent_tx_count
            FROM user u
            WHERE u.id = %s
        """
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            return {"result": "FAILURE", "message": "해당 유저 정보가 없습니다."}

        try:
            age_str = str(user_data['age']).replace('대', '').replace('세', '').strip()
            age = int(age_str)
        except (ValueError, TypeError):
            age = 30

        user_type_str = str(user_data.get('user_type') or '').upper()
        is_corporate = 1 if user_type_str in ('CORPORATE', '기업', '법인', 'BUSINESS') else 0

        input_df = pd.DataFrame([{
            "age": age,
            "is_corporate": is_corporate,
            "total_balance": int(user_data['total_balance']),
            "has_active_loan": int(user_data['has_active_loan']),
            "recent_tx_count": int(user_data['recent_tx_count'])
        }])

        if model:
            pred = int(model.predict(input_df)[0])
            proba = model.predict_proba(input_df)[0]
            confidence = round(float(max(proba)) * 100, 1)
        else:
            pred = 0
            confidence = 0.0

        result = PRODUCT_MAP.get(pred, PRODUCT_MAP[0])

        return {
            "result": "SUCCESS",
            "predicted_class": pred,
            "recommended_product": result["product"],
            "reason": result["reason"],
            "confidence": confidence
        }

    except Exception as e:
        return {"result": "FAILURE", "message": str(e)}
    finally:
        cursor.close()
        conn.close()