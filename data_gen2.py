import pandas as pd
import numpy as np


products = [
    'BankScope 첫거래 환영 예금', 'BankScope 프리미엄 정기예금', 'Scope 단기 안심 예금',
    'BankScope 시니어 플러스 예금', 'BankScope 직장인 우대 적금', 'Scope 청년 드림 적금',
    'BankScope 자유적립 적금', 'Scope 어린이 미래 적금', 'BankScope 목돈 마련 정기적금',
    'Scope 비상금 소액 대출'
]

np.random.seed(42)
data_size = 5000 


data = {
    'age': np.random.randint(20, 80, data_size),
    'is_corporate': np.random.choice([0, 1], data_size, p=[0.9, 0.1]),
    'total_balance': np.random.randint(0, 100000000, data_size),
    'has_active_loan': np.random.choice([0, 1], data_size, p=[0.8, 0.2]),
    'recent_tx_count': np.random.randint(0, 50, data_size)
}
df = pd.DataFrame(data)


def assign_target(row):
    if row['age'] >= 55: return 'BankScope 시니어 플러스 예금'
    elif row['is_corporate'] == 1: return 'BankScope 프리미엄 정기예금'
    elif 19 <= row['age'] <= 34: return 'Scope 청년 드림 적금'
    elif row['has_active_loan'] == 1: return 'Scope 비상금 소액 대출'
    return np.random.choice(products)

df['target_product'] = df.apply(assign_target, axis=1)


df.to_csv('bank_data_2.csv', index=False)
print(f"총 {data_size}명의 데이터가 'bank_data_2.csv'에 저장되었습니다.")