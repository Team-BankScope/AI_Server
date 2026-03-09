import pandas as pd
import numpy as np

# 1. 가상 데이터 생성 (1000명)
np.random.seed(42)
data_size = 1000

data = {
    'age': np.random.randint(20, 80, data_size), # 연령대
    'is_vip': np.random.choice([0, 1], data_size, p=[0.9, 0.1]), # VIP 여부
    'app_search_loan': np.random.randint(0, 10, data_size), # 최근 앱 대출 검색 횟수
    'fx_history': np.random.choice([0, 1], data_size, p=[0.8, 0.2]), # 최근 외환 거래 이력
    'visit_count_month': np.random.randint(0, 5, data_size) # 월 평균 방문 횟수
}

df = pd.DataFrame(data)

# 2. 아주 간단한 '정답(Label)' 로직 만들기
# 앱 검색이 많으면 대출(1), 외환 이력이 있으면 외환(2), 나머지는 일반(0)
def assign_task(row):
    if row['app_search_loan'] > 5: return 1 # 대출
    if row['fx_history'] == 1: return 2     # 외환
    return 0                                # 일반 입출금

df['target_task'] = df.apply(assign_task, axis=1)

# 3. CSV 파일로 저장
df.to_csv('bank_customers.csv', index=False)
print("가상 데이터 생성 완료: bank_customers.csv")