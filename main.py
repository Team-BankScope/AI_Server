import os
import contextlib
import joblib
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import pooling
from mysql.connector.errors import Error
from fastapi.middleware.cors import CORSMiddleware
import chatbot_service
from recommender import ProductRecommender

load_dotenv()

app = FastAPI(title="BankScope AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = joblib.load('bank_model.pkl')
except FileNotFoundError:
    print("[WARN] 모델 파일(bank_model.pkl)을 찾을 수 없습니다. 먼저 train_model.py를 실행하세요.")
    model = None

# RF.py 와 동일한 순서 유지 (어긋나면 예측이 틀어짐)
FEATURE_COLUMNS = ['age', 'is_corporate', 'total_balance', 'has_active_loan', 'recent_tx_count']

POOL_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'bank'),
}

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="bank_pool",
        pool_size=5,
        pool_reset_session=True,
        **POOL_CONFIG
    )
except Error as e:
    print(f"[WARN] DB 연결 풀 초기화 실패: {e}")
    connection_pool = None

@contextlib.contextmanager
def get_db_cursor():
    if connection_pool is None:
        raise RuntimeError("DB 연결 풀이 초기화되지 않았습니다.")
    conn = connection_pool.get_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)
    try:
        yield conn, cursor
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


try:
    base_df = pd.read_csv('bank_data_2.csv')
    try:
        with get_db_cursor() as (conn, cursor):
            cursor.execute("""
                SELECT
                    u.age,
                    u.user_type,
                    COALESCE((SELECT SUM(balance) FROM account WHERE user_id = u.id), 0) AS total_balance,
                    CASE WHEN EXISTS (SELECT 1 FROM loan WHERE user_id = u.id AND status = 'ACTIVE')
                    THEN 1 ELSE 0 END AS has_active_loan,
                    (
                        SELECT COUNT(*) FROM transaction_history th
                        JOIN account a ON th.account_id = a.account_id
                        WHERE a.user_id = u.id
                          AND th.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
                    ) AS recent_tx_count,
                    fp.product_name AS target_product
                FROM user u
                JOIN product_subscription ps ON u.id = ps.user_id AND ps.status = 'ACTIVE'
                JOIN financial_product fp ON ps.product_id = fp.product_id
            """)
            real_rows = cursor.fetchall()

        if real_rows:
            real_df = pd.DataFrame(real_rows)
            real_df['is_corporate'] = real_df['user_type'].str.upper().isin(
                ['CORPORATE', '기업', '법인', 'BUSINESS']
            ).astype(int)
            real_df = real_df.drop(columns=['user_type'])
            real_df['age'] = (
                real_df['age'].astype(str)
                .str.replace('대', '').str.replace('세', '').str.strip()
            )
            real_df['age'] = pd.to_numeric(real_df['age'], errors='coerce').fillna(30).astype(int)
            merged_df = pd.concat([base_df, real_df], ignore_index=True)
            print(f"[추천] 기본 {len(base_df)}건 + 실제 구독 {len(real_rows)}건 병합 완료")
        else:
            merged_df = base_df
            print(f"[추천] 실제 구독 데이터 없음, 기본 데이터 {len(base_df)}건 사용")
    except Exception as e:
        merged_df = base_df
        print(f"[WARN] DB 구독 데이터 로드 실패, 기본 데이터만 사용: {e}")

    recommender_obj = ProductRecommender(merged_df)
except Exception as e:
    print(f"[WARN] 추천 모델 초기화 실패: {e}")
    recommender_obj = None


class AutoTaskRequest(BaseModel):
    user_id: int


class ChatRequest(BaseModel):
    user_id: int
    message: str


def get_min_level(level_str: str) -> int:
    try:
        return int(level_str.replace('LEVEL_', ''))
    except:
        return 1


def get_min_level_by_detail_type(task_detail_type: str) -> int:
    mapping = {
        # 빠른 업무 - lv.1
        '입금':               1,
        '출금':               1,
        '카드수령':            1,
        # 빠른 업무 - lv.2
        '이체':               2,
        '체크카드 발급':        2,
        '통장 비밀번호 변경':   2,
        '입출금 계좌개설':      2,
        # 상담 업무 - lv.2
        '적금':               2,
        '신용카드 발급':        2,
        '대출 상환':           2,
        # 상담 업무 - lv.3
        '예금':               3,
        '신용대출':            3,
        '전세자금대출':         3,
        '금융상품가입':         3,
        # 상담 업무 - lv.4
        '소상공인 대출':        4,
        '연금신청':            4,
        '주택담보대출':         4,
        # 기업·특수 - lv.3
        '법인카드 발급':        3,
        # 기업·특수 - lv.4
        '법인계좌 개설':        4,
        '기업대출':            4,
        '연체관리':            4,
        # 기업·특수 - lv.5
        '부도관리':            5,
    }
    return mapping.get(task_detail_type, 1)


def extract_user_features(cursor, user_id: int) -> dict:
    # recent_tx_count: account 를 통해 JOIN 해야 고객 본인의 거래 내역을 조회할 수 있음
    query = """
        SELECT
            u.age,
            u.user_type,
            COALESCE(
                (SELECT SUM(balance) FROM account WHERE user_id = u.id), 0
            ) AS total_balance,
            CASE
                WHEN EXISTS (SELECT 1 FROM loan WHERE user_id = u.id AND status = 'ACTIVE')
                THEN 1 ELSE 0
            END AS has_active_loan,
            (
                SELECT COUNT(*)
                FROM transaction_history th
                JOIN account a ON th.account_id = a.account_id
                WHERE a.user_id = u.id
                  AND th.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            ) AS recent_tx_count
        FROM user u
        WHERE u.id = %s
    """
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        raise ValueError("User not found")

    age_str = str(user_data['age']).replace('대', '').replace('세', '').strip() if user_data['age'] else '30'
    user_type_str = str(user_data['user_type']).upper() if user_data['user_type'] else ''

    return {
        "age":             int(age_str) if age_str.isdigit() else 30,
        "is_corporate":    1 if user_type_str in ('CORPORATE', '기업', '법인', 'BUSINESS') else 0,
        "total_balance":   int(user_data['total_balance']),
        "has_active_loan": int(user_data['has_active_loan']),
        "recent_tx_count": int(user_data['recent_tx_count']),
    }


def determine_task_details(pred: int, features: dict) -> dict:
    total_balance   = features['total_balance']
    has_active_loan = features['has_active_loan']
    recent_tx_count = features['recent_tx_count']
    is_corporate    = features['is_corporate']

    if pred == 0:
        if total_balance == 0:
            detail = "입출금 계좌개설"
        elif recent_tx_count > 10:
            detail = "이체"
        else:
            detail = "출금"
        return {
            "task_type": "빠른 업무", "assigned_level": "LEVEL_1",
            "processing_time": 5, "prefix": "A", "task_detail_type": detail,
        }

    elif pred == 1:
        if has_active_loan == 1:
            detail = "신용대출"
        elif total_balance >= 50_000_000:
            detail = "예금"
        else:
            detail = "적금"
        return {
            "task_type": "상담 업무", "assigned_level": "LEVEL_2",
            "processing_time": 10, "prefix": "B", "task_detail_type": detail,
        }

    else:
        if is_corporate == 1 and has_active_loan == 0:
            detail = "법인계좌 개설"
        elif is_corporate == 1 and has_active_loan == 1:
            detail = "기업대출"
        else:
            detail = "연체관리"
        return {
            "task_type": "기업 • 특수", "assigned_level": "LEVEL_3",
            "processing_time": 25, "prefix": "C", "task_detail_type": detail,
        }


@app.post("/py/auto-insert-task")
def auto_insert_task(req: AutoTaskRequest):
    if not model:
        raise HTTPException(status_code=500, detail="AI Model not loaded.")

    try:
        with get_db_cursor() as (conn, cursor):
            # 1. 피처 추출
            try:
                features = extract_user_features(cursor, req.user_id)
            except ValueError:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

            # 2. AI 예측 (피처 컬럼 순서 고정)
            input_df = pd.DataFrame([features])[FEATURE_COLUMNS]
            pred = int(model.predict(input_df)[0])

            # 기업 고객은 모델 예측과 무관하게 기업·특수(2)로 강제 배정
            if features['is_corporate'] == 1:
                pred = 2

            # 3. 업무 매핑
            details          = determine_task_details(pred, features)
            task_type        = details["task_type"]
            processing_time  = details["processing_time"]
            prefix           = details["prefix"]
            task_detail_type = details["task_detail_type"]
            min_level        = get_min_level_by_detail_type(task_detail_type)

            # assigned_level을 세부 업무 min_level 기준으로 산정
            assigned_level = f"LEVEL_{min_level}"

            # 4. 티켓 번호 생성 (FOR UPDATE 행 잠금 → 동시 요청 간 번호 중복 방지)
            cursor.execute(
                "SELECT ticket_number FROM task "
                "WHERE ticket_number LIKE %s ORDER BY task_id DESC LIMIT 1 FOR UPDATE",
                (f"{prefix}-%",)
            )
            last_ticket = cursor.fetchone()
            next_num = int(str(last_ticket['ticket_number']).split("-")[1]) + 1 if last_ticket else 1
            ticket_number = f"{prefix}-{next_num:03d}"

            # 5. 대기 인원 및 예상 대기 시간 계산
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM task WHERE task_type = %s AND status = 'WAITING'",
                (task_type,)
            )
            waiting_count = cursor.fetchone()['cnt']
            ranking = int(waiting_count) + 1

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM member WHERE level >= %s AND status = 1",
                (min_level,)
            )
            available_count = max(cursor.fetchone()['cnt'], 1)
            expected_waiting_time = int((waiting_count * processing_time) / available_count)

            # 6. 창구 직원 배정
            # 동일 고객의 기존 대기 task가 있으면 가장 높은 레벨 직원에게 모아서 배정
            member_id = None
            cursor.execute(
                "SELECT task_id, assigned_level FROM task WHERE user_id = %s AND status = 'WAITING'",
                (req.user_id,)
            )
            waiting_tasks = cursor.fetchall()

            if waiting_tasks:
                max_level = min_level
                task_ids = [t['task_id'] for t in waiting_tasks]
                for t in waiting_tasks:
                    lvl = get_min_level(t['assigned_level'])
                    if lvl > max_level:
                        max_level = lvl
                cursor.execute(
                    """
                    SELECT m.id FROM member m
                    LEFT JOIN (
                        SELECT member_id, COUNT(*) AS waiting_cnt
                        FROM task WHERE status = 'WAITING'
                        GROUP BY member_id
                    ) w ON m.id = w.member_id
                    WHERE m.level >= %s AND m.status = 1
                    ORDER BY COALESCE(w.waiting_cnt, 0) ASC, m.level ASC
                    LIMIT 1
                    """,
                    (max_level,)
                )
                member_row = cursor.fetchone()
                if not member_row:
                    cursor.execute(
                        "SELECT id FROM member WHERE status = 1 ORDER BY level DESC LIMIT 1"
                    )
                    member_row = cursor.fetchone()
                if member_row:
                    member_id = member_row['id']
                    fmt = ','.join(['%s'] * len(task_ids))
                    cursor.execute(
                        f"UPDATE task SET member_id = %s, updated_at = NOW() WHERE task_id IN ({fmt})",
                        [member_id] + task_ids
                    )
            else:
                cursor.execute(
                    """
                    SELECT m.id FROM member m
                    LEFT JOIN (
                        SELECT member_id, COUNT(*) AS waiting_cnt
                        FROM task WHERE status = 'WAITING'
                        GROUP BY member_id
                    ) w ON m.id = w.member_id
                    WHERE m.level >= %s AND m.status = 1
                    ORDER BY COALESCE(w.waiting_cnt, 0) ASC, m.level ASC
                    LIMIT 1
                    """,
                    (min_level,)
                )
                member_row = cursor.fetchone()
                if not member_row:
                    cursor.execute(
                        "SELECT id FROM member WHERE status = 1 ORDER BY level DESC LIMIT 1"
                    )
                    member_row = cursor.fetchone()
                if member_row:
                    member_id = member_row['id']

            # 7. DB Insert
            insert_query = """
                INSERT INTO task (
                    user_id, ticket_number, task_type, task_detail_type, assigned_level,
                    expected_waiting_time, status, member_id, ranking, created_at, updated_at, is_ai
                ) VALUES (%s, %s, %s, %s, %s, %s, 'WAITING', %s, %s, %s, %s, 1)
            """
            now = datetime.now()
            cursor.execute(insert_query, (
                req.user_id, ticket_number, task_type, task_detail_type, assigned_level,
                expected_waiting_time, member_id, ranking, now, now
            ))
            inserted_task_id = cursor.lastrowid
            conn.commit()

            # 8. 삽입된 task 조회 후 반환
            cursor.execute("SELECT * FROM task WHERE task_id = %s", (inserted_task_id,))
            new_task = cursor.fetchone()

            if new_task:
                new_task['created_at'] = new_task['created_at'].strftime('%Y-%m-%dT%H:%M:%S')
                new_task['updated_at'] = new_task['updated_at'].strftime('%Y-%m-%dT%H:%M:%S')

            return {"result": "SUCCESS", "taskResult": new_task}

    except HTTPException:
        raise
    except Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/py/chat")
async def chat_bot(req: ChatRequest):
    try:
        response_data = chatbot_service.get_chat_response(req.user_id, req.message)
        return {"result": "SUCCESS", **response_data}
    except Exception as e:
        return {
            "result": "FAILURE",
            "sender": "bot",
            "content": "현재 챗봇 서비스를 이용할 수 없습니다.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


@app.get("/py/recommend/{user_id}")
def get_user_recommendation(user_id: int):
    if recommender_obj is None:
        raise HTTPException(status_code=500, detail="추천 모델이 초기화되지 않았습니다.")

    try:
        with get_db_cursor() as (conn, cursor):
            cursor.execute("""
                SELECT
                    u.age,
                    u.user_type,
                    COALESCE((SELECT SUM(balance) FROM account WHERE user_id = u.id), 0) AS total_balance,
                    CASE WHEN EXISTS (SELECT 1 FROM loan WHERE user_id = u.id AND status = 'ACTIVE')
                    THEN 1 ELSE 0 END AS has_active_loan,
                    (
                        SELECT COUNT(*)
                        FROM transaction_history th
                        JOIN account a ON th.account_id = a.account_id
                        WHERE a.user_id = u.id
                          AND th.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
                    ) AS recent_tx_count
                FROM user u WHERE u.id = %s
            """, (user_id,))
            user_data = cursor.fetchone()

        if not user_data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        age_str = str(user_data['age']).replace('대', '').replace('세', '').strip() if user_data['age'] else '30'
        user_type_str = str(user_data['user_type']).upper() if user_data['user_type'] else ''
        user_profile = {
            "age":             int(age_str) if age_str.isdigit() else 30,
            "is_corporate":    1 if user_type_str in ('CORPORATE', '기업', '법인', 'BUSINESS') else 0,
            "total_balance":   int(user_data['total_balance']),
            "has_active_loan": int(user_data['has_active_loan']),
            "recent_tx_count": int(user_data['recent_tx_count']),
        }

        recommended_names = recommender_obj.get_recommendations(user_profile)

        products_list = []
        with get_db_cursor() as (conn, cursor):
            for name in recommended_names:
                cursor.execute("SELECT * FROM financial_product WHERE product_name = %s", (name,))
                product_data = cursor.fetchone()
                if product_data:
                    products_list.append({
                        "productId":         product_data['product_id'],
                        "productCategory":   product_data['product_category'],
                        "targetType":        product_data['target_type'],
                        "productName":       product_data['product_name'],
                        "baseInterestRate":  float(product_data['base_interest_rate']),
                        "maxInterestRate":   float(product_data['max_interest_rate']),
                        "minDurationMonths": product_data['min_duration_months'],
                        "maxDurationMonths": product_data['max_duration_months'],
                        "minAmount":         int(product_data['min_amount']) if product_data['min_amount'] is not None else None,
                        "maxAmount":         int(product_data['max_amount']) if product_data['max_amount'] is not None else None,
                        "description":       product_data['description'],
                        "isActive":          bool(product_data['is_active'])
                    })

        return {"result": "SUCCESS", "user_id": user_id, "products": products_list}

    except HTTPException:
        raise
    except RuntimeError:
        raise HTTPException(status_code=500, detail="DB 연결 불가")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
