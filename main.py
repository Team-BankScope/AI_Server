import joblib
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import mysql.connector
from datetime import datetime
import chatbot_service  
import recommend

app = FastAPI()

# 1. 학습된 Random Forest 모델 불러오기
try:
    model = joblib.load('bank_model.pkl')
    print("BankScope AI 모델 로딩 성공")
except Exception as e:
    print(f"모델 로딩 실패 (bank_model.pkl 파일 확인): {e}")
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

# --- 데이터 모델 (DTO) ---

class AutoTaskRequest(BaseModel):
    user_id: int

# 챗봇용 데이터 모델 (프론트에서 전송할 형식)
class ChatRequest(BaseModel):
    user_id: int
    message: str

# 프론트엔드에서 보낼 형태 정의
class RecommendRequest(BaseModel):
    user_id: int

# --- API 엔드포인트 ---

# 1. 자동 업무 접수 로직 (기존 코드 전체 유지)
@app.post("/py/auto-insert-task")
def auto_insert_task(req: AutoTaskRequest):
    conn = get_db_connection()
    if not conn:
        return {"result": "FAILURE"}

    cursor = conn.cursor(dictionary=True)
    try:
        # 사용자 데이터 조회
        query = """
            SELECT 
                u.age,
                u.user_type,
                COALESCE((SELECT SUM(balance) FROM account WHERE user_id = u.id), 0) AS total_balance,
                CASE WHEN EXISTS (SELECT 1 FROM loan WHERE user_id = u.id AND status = 'ACTIVE') THEN 1 ELSE 0 END AS has_active_loan,
                (SELECT COUNT(*) FROM transaction_history WHERE user_id = u.id AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) AS recent_tx_count
            FROM user u
            WHERE u.id = %s
        """
        cursor.execute(query, (req.user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return {"result": "FAILURE"}
            
        # 데이터 전처리
        try:
            age_str = str(user_data['age']).replace('대', '').replace('세', '').strip() if user_data['age'] else '30'
            age = int(age_str)
        except ValueError:
            age = 30
            
        user_type_str = str(user_data['user_type']).upper() if user_data['user_type'] else ''
        is_corporate = 1 if user_type_str in ('CORPORATE', '기업', '법인', 'BUSINESS') else 0
        total_balance = int(user_data['total_balance'])
        has_active_loan = int(user_data['has_active_loan'])
        recent_tx_count = int(user_data['recent_tx_count'])
        
        input_df = pd.DataFrame([{
            "age": age,
            "is_corporate": is_corporate,
            "total_balance": total_balance,
            "has_active_loan": has_active_loan,
            "recent_tx_count": recent_tx_count
        }])
        
        # 모델 예측
        # pred = 0  # model.predict 대신 일단 0으로 고정! , 원래는  pred = int(model.predict(input_df)[0])
        if model:
            pred = int(model.predict(input_df)[0])
        else:
            pred = 0 # 만약 AI 모델이 오류로 안 켜졌다면 기본값(빠른업무)으로 보냄
        # 업무 매핑 로직
        if pred == 0:
            task_type = "빠른 업무"
            assigned_level = "LEVEL_1"
            processing_time = 5
            prefix = "A"
            if total_balance == 0:
                task_detail_type = "계좌 개설"
            elif recent_tx_count > 10:
                task_detail_type = "이체"
            else:
                task_detail_type = "출금"
        elif pred == 1:
            task_type = "상담 업무"
            assigned_level = "LEVEL_2"
            processing_time = 10
            prefix = "B"
            if has_active_loan == 1:
                task_detail_type = "대출 상환"
            elif total_balance >= 50000000:
                task_detail_type = "예금"
            else:
                task_detail_type = "금융상품가입"
        else:
            task_type = "기업 • 특수"
            assigned_level = "LEVEL_3"
            processing_time = 25
            prefix = "C"
            if is_corporate == 1 and has_active_loan == 0:
                task_detail_type = "법인계좌 개설"
            elif is_corporate == 1 and has_active_loan == 1:
                task_detail_type = "기업대출"
            else:
                task_detail_type = "연체관리"
                
        # 티켓 번호 생성
        cursor.execute("SELECT ticket_number FROM task WHERE ticket_number LIKE %s ORDER BY task_id DESC LIMIT 1", (f"{prefix}-%",))
        last_ticket = cursor.fetchone()
        next_num = 1
        if last_ticket and last_ticket.get('ticket_number'):
            num_part = str(last_ticket['ticket_number']).split("-")[1]
            next_num = int(num_part) + 1
        ticket_number = f"{prefix}-{next_num:03d}"

        def get_min_level(level_str):
            if level_str == "LEVEL_1": return 1
            if level_str == "LEVEL_2": return 3
            if level_str == "LEVEL_3": return 5
            return 1
            
        min_level = get_min_level(assigned_level)
        
        # 대기 시간 및 순번 계산
        cursor.execute("SELECT COUNT(*) as cnt FROM task WHERE task_type = %s AND status = 'WAITING'", (task_type,))
        waiting_count_row = cursor.fetchone()
        waiting_count = waiting_count_row['cnt'] if waiting_count_row else 0
        
        cursor.execute("SELECT COUNT(*) as cnt FROM member WHERE level >= %s AND status = 1", (min_level,))
        available_member_count_row = cursor.fetchone()
        available_member_count = available_member_count_row['cnt'] if available_member_count_row else 0
        if available_member_count == 0:
            available_member_count = 1
        
        ranking = int(waiting_count) + 1
        expected_waiting_time = int((waiting_count * processing_time) / available_member_count)
        
        # 멤버 할당 로직
        member_id = None
        cursor.execute("SELECT * FROM task WHERE user_id = %s AND status = 'WAITING'", (req.user_id,))
        waiting_tasks = cursor.fetchall()
        
        if waiting_tasks:
            max_min_level = min_level
            task_ids_to_update = []
            for task in waiting_tasks:
                task_ids_to_update.append(task['task_id'])
                task_min_level = get_min_level(task['assigned_level'])
                if task_min_level > max_min_level:
                    max_min_level = task_min_level
            cursor.execute("SELECT id FROM member WHERE level >= %s AND status = 1 LIMIT 1", (max_min_level,))
            member_row = cursor.fetchone()
            if member_row:
                member_id = member_row['id']
            if member_id is not None and task_ids_to_update:
                format_strings = ','.join(['%s'] * len(task_ids_to_update))
                update_query = f"UPDATE task SET member_id = %s WHERE task_id IN ({format_strings})"
                cursor.execute(update_query, [member_id] + task_ids_to_update)
        else:
            cursor.execute("SELECT id FROM member WHERE level >= %s AND status = 1 LIMIT 1", (min_level,))
            member_row = cursor.fetchone()
            if member_row:
                member_id = member_row['id']
        
        # DB 인서트
        insert_query = """
            INSERT INTO task (
                user_id, ticket_number, task_type, task_detail_type,
                assigned_level, expected_waiting_time, status,
                member_id, ranking, created_at, updated_at, is_ai
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.now()
        values = (req.user_id, ticket_number, task_type, task_detail_type, assigned_level, expected_waiting_time, "WAITING", member_id, ranking, now, now, 1)
        cursor.execute(insert_query, values)
        conn.commit()
        
        inserted_task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM task WHERE task_id = %s", (inserted_task_id,))
        new_task = cursor.fetchone()
        
        if new_task:
            if isinstance(new_task.get('created_at'), datetime):
                new_task['created_at'] = new_task['created_at'].strftime('%Y-%m-%dT%H:%M:%S')
            if isinstance(new_task.get('updated_at'), datetime):
                new_task['updated_at'] = new_task['updated_at'].strftime('%Y-%m-%dT%H:%M:%S')
                
        return {"result": "SUCCESS", "taskResult": new_task}
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return {"result": "FAILURE"}
    finally:
        cursor.close()
        conn.close()

# 2. RAG 기반 챗봇 상담 엔드포인트
@app.post("/py/chat")
def chat_bot(req: ChatRequest):
    try:
        # chatbot_service의 RAG 로직을 호출하여 답변 생성
        answer = chatbot_service.get_chat_response(req.message)
        return {
            "result": "SUCCESS",
            "answer": answer
        }
    except Exception as e:
        print(f"Chat Error: {e}")
        return {
            "result": "FAILURE",
            "answer": "죄송합니다. 현재 챗봇 서비스를 이용할 수 없습니다."
        }
    

# 3. 맞춤형 금융 상품 추천 엔드포인트 
@app.get("/py/recommend")
def get_user_recommendation(user_id: int):
    conn = get_db_connection()
    if not conn:
        return {"result": "FAILURE", "message": "DB 연결 실패"}

    cursor = conn.cursor(dictionary=True)

    try:
        # 1) 실제 DB에서 유저 정보 가져오기
        query = """
            SELECT 
                u.age, u.user_type,
                COALESCE((SELECT SUM(balance) FROM account WHERE user_id = u.id), 0) AS total_balance,
                CASE WHEN EXISTS (SELECT 1 FROM loan WHERE user_id = u.id AND status = 'ACTIVE') THEN 1 ELSE 0 END AS has_active_loan,
                (SELECT COUNT(*) FROM transaction_history WHERE user_id = u.id AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) AS recent_tx_count
            FROM user u
            WHERE u.id = %s
        """
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            return {"result": "FAILURE", "message": "유저 정보가 없습니다."}

        # 2) recommend_service.py에 넣을 수 있게 데이터 형태 맞추기
        age_str = str(user_data['age']).replace('대', '').replace('세', '').strip() if user_data['age'] else '30'
        age = int(age_str)
        user_type_str = str(user_data['user_type']).upper() if user_data['user_type'] else ''
        is_corporate = 1 if user_type_str in ('CORPORATE', '기업', '법인', 'BUSINESS') else 0

        input_df = pd.DataFrame([{
            "age": age,
            "is_corporate": is_corporate,
            "total_balance": int(user_data['total_balance']),
            "has_active_loan": int(user_data['has_active_loan']),
            "recent_tx_count": int(user_data['recent_tx_count'])
        }])

        # 3) recommend_service.py의 짧은 추천 함수 실행
        recommended_names = recommend.get_recommendation(input_df)

        if not recommended_names:
            return {"result": "SUCCESS", "user_id": user_id, "products": []}

        # 4) 추천받은 상품명으로 DB에서 상세 정보 조회
        format_strings = ','.join(['%s'] * len(recommended_names))
        query = f"SELECT * FROM financial_product WHERE product_name IN ({format_strings}) LIMIT 3"
        
        cursor.execute(query, tuple(recommended_names))
        products = cursor.fetchall()

        if not products:
            return {"result": "SUCCESS", "user_id": user_id, "products": []}

        formatted_products = []
        for product in products:
            formatted_product = {
                "productId": product['product_id'],
                "productCategory": product['product_category'],
                "productName": product['product_name'],
                "baseInterestRate": float(product['base_interest_rate']) if product['base_interest_rate'] is not None else 0.0,
                "maxInterestRate": float(product['max_interest_rate']) if product['max_interest_rate'] is not None else None,
                "minDurationMonths": product['min_duration_months'],
                "maxDurationMonths": product['max_duration_months'],
                "minAmount": product['min_amount'],
                "maxAmount": product['max_amount'],
                "description": product['description'],
                "isActive": bool(product['is_active'])
            }
            formatted_products.append(formatted_product)

        # 추천 우선순위에 맞춰서 정렬
        sorted_products = sorted(
            formatted_products, 
            key=lambda x: recommended_names.index(x['productName']) if x['productName'] in recommended_names else 999
        )

        return {
            "result": "SUCCESS",
            "user_id": user_id,
            "products": sorted_products
        }

    except Exception as e:
        print(f"Recommend Error: {e}")
        return {"result": "FAILURE", "message": str(e)}

    finally:
        cursor.close()
        conn.close()