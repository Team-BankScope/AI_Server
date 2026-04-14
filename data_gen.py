# import pandas as pd
# import numpy as np
#
# # 1. 실제 DB 구조(BankScope)에 맞춘 가상 데이터 생성 (1000명)
# np.random.seed(42)
# data_size = 1000
#
# data = {
#     # 1. user 테이블 (나이)
#     'age': np.random.randint(20, 80, data_size),
#
#     # 2. user 테이블 (기업 고객 여부, user_type='corporate')
#     'is_corporate': np.random.choice([0, 1], data_size, p=[0.9, 0.1]),
#
#     # 3. account 테이블 (전체 계좌 잔액 합계, 0원 ~ 1억원)
#     'total_balance': np.random.randint(0, 100000000, data_size),
#
#     # 4. loan 테이블 (진행 중인 대출 여부)
#     'has_active_loan': np.random.choice([0, 1], data_size, p=[0.8, 0.2]),
#
#     # 5. transaction_history 테이블 (최근 한 달 거래 건수)
#     'recent_tx_count': np.random.randint(0, 50, data_size)
# }
#
# df = pd.DataFrame(data)
#
#
# # 2. BankScope 비즈니스 룰에 맞춘 정답(Target) 할당 로직
# def assign_task(row):
#     # 1순위: 기업 고객이면 무조건 '기업 • 특수' (2)
#     if row['is_corporate'] == 1:
#         return 2
#
#         # 2순위: 대출이 있거나, 잔고가 5천만원 이상이거나, 65세 이상이면 '상담 업무' (1)
#     elif row['has_active_loan'] == 1 or row['total_balance'] >= 50000000 or row['age'] >= 65:
#         return 1
#
#         # 3순위: 그 외 일반 고객은 입출금 등 '빠른 업무' (0)
#     else:
#         return 0
#
#
# df['target_task'] = df.apply(assign_task, axis=1)
#
# # 3. CSV 파일로 저장
# df.to_csv('bank_customers_real.csv', index=False)
# print("실제 DB 기반 가상 데이터 생성 완료: bank_customers_real.csv")

import pandas as pd
import numpy as np

print("1. BankScope 가상 데이터 생성 중...")
np.random.seed(42)
data_size = 3000 # 학습 효율을 위해 3000으로 늘림.

# 피처(Feature) 데이터 생성
data = {
    'age': np.random.randint(20, 80, data_size),
    'is_corporate': np.random.choice([0, 1], data_size, p=[0.9, 0.1]),
    'total_balance': np.random.randint(0, 100000000, data_size),
    'has_active_loan': np.random.choice([0, 1], data_size, p=[0.8, 0.2]),
    'recent_tx_count': np.random.randint(0, 50, data_size)
}
df = pd.DataFrame(data)

def assign_task_probabilistic(row):
    # 기업 고객 (Target 2)
    if row['is_corporate'] == 1:
        # 기업 고객도 15% 확률로 단순 업무(0)를 볼 수 있도록 설계
        return np.random.choice([2, 0], p=[0.85, 0.15])

    # 상담 업무 (Target 1) - 대출보유, 고액잔고(5천만 이상), 고령층(65세 이상)
    elif row['has_active_loan'] == 1 or row['total_balance'] >= 50000000 or row['age'] >= 65:
        # 정석은 상담(1)이지만, 빠른 업무(0)나 기업창구(2)로 잘못 갈 확률도 부여 (학습용 노이즈)
        return np.random.choice([1, 0, 2], p=[0.75, 0.20, 0.05])

    # 빠른 업무 (Target 0) - 일반 고객
    else:
        # 보통은 빠른 업무(0)지만, 상담(1)으로 유도될 확률 15% 부여
        return np.random.choice([0, 1], p=[0.85, 0.15])

df['target'] = df.apply(assign_task_probabilistic, axis=1)
print(f"데이터 생성 완료! 총 {len(df)}건")

# 생성된 데이터 표 미리보기
df.head()