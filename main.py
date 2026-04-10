import joblib
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import mysql.connector
from datetime import datetime

app = FastAPI()

# 1. 학습된 Random Forest 모델 불러오기
model = joblib.load('bank_model.pkl')

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

# 프론트엔드의 "자동 접수" 버튼 클릭 시 오직 user_id만 전송
class AutoTaskRequest(BaseModel):
    user_id: int

@app.post("/py/auto-insert-task")
def auto_insert_task(req: AutoTaskRequest):
    conn = get_db_connection()
    if not conn:
        return {"result": "FAILURE"}

    cursor = conn.cursor(dictionary=True)
    try:
        # 1. DB에서 사용자 특성 실시간 조회
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
            return {"result": "FAILURE"} # 사용자를 찾을 수 없음
            
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
        
        # 2. 모델 예측 (0: 빠른업무, 1: 상담업무, 2: 기업/특수)
        pred = int(model.predict(input_df)[0])
        
        # 3. 비즈니스 룰에 따른 16개 세부 업무 매핑
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
                
        else:  # pred == 2
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
                
        # 4. 대기표 번호 생성
        cursor.execute("SELECT ticket_number FROM task WHERE ticket_number LIKE %s ORDER BY task_id DESC LIMIT 1", (f"{prefix}-%",))
        last_ticket = cursor.fetchone()
        next_num = 1
        if last_ticket and last_ticket.get('ticket_number'):
            num_part = str(last_ticket['ticket_number']).split("-")[1]
            next_num = int(num_part) + 1
        ticket_number = f"{prefix}-{next_num:03d}"
        
        # 5. 대기 인원 파악 및 예상 대기 시간 계산
        cursor.execute("SELECT COUNT(*) as cnt FROM task WHERE task_type = %s AND status = 'WAITING'", (task_type,))
        waiting_count_row = cursor.fetchone()
        waiting_count = waiting_count_row['cnt'] if waiting_count_row else 0
        
        ranking = int(waiting_count) + 1
        expected_waiting_time = ranking * processing_time
        member_id = None
        
        # 6. DB Insert
        insert_query = """
            INSERT INTO task (
                user_id, ticket_number, task_type, task_detail_type,
                assigned_level, expected_waiting_time, status,
                member_id, ranking, created_at, updated_at, is_ai
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.now()
        values = (
            req.user_id,
            ticket_number,
            task_type,
            task_detail_type,
            assigned_level,
            expected_waiting_time,
            "WAITING",
            member_id,
            ranking,
            now,
            now,
            1
        )
        cursor.execute(insert_query, values)
        conn.commit()
        
        inserted_task_id = cursor.lastrowid
        
        # 7. Insert된 전체 엔티티 조회 및 반환
        cursor.execute("SELECT * FROM task WHERE task_id = %s", (inserted_task_id,))
        new_task = cursor.fetchone()
        
        if new_task:
            if isinstance(new_task.get('created_at'), datetime):
                new_task['created_at'] = new_task['created_at'].strftime('%Y-%m-%dT%H:%M:%S')
            if isinstance(new_task.get('updated_at'), datetime):
                new_task['updated_at'] = new_task['updated_at'].strftime('%Y-%m-%dT%H:%M:%S')
                
        return {
            "result": "SUCCESS",
            "taskResult": new_task
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return {"result": "FAILURE"}
    finally:
        cursor.close()
        conn.close()