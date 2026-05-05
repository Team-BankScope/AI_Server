import pandas as pd
import numpy as np

products = [
    'BankScope 첫거래 환영 예금', 'BankScope 프리미엄 정기예금', 'Scope 단기 안심 예금',
    'BankScope 시니어 플러스 예금', 'BankScope 직장인 우대 적금', 'Scope 청년 드림 적금',
    'BankScope 자유적립 적금', 'Scope 어린이 미래 적금', 'BankScope 목돈 마련 정기적금',
    'Scope 비상금 소액 대출', 'BankScope 직장인 신용 대출', 'BankScope 아파트 담보 대출',
    'Scope 청년 전세 대출', 'BankScope 사업자 운전자금 대출', 'Scope 새출발 서민 대출',
    'Scope 모바일 전용 예금', 'BankScope 복리 자산 예금', 'Scope 외화 달러 예금',
    'BankScope 법인 단기 예금', 'BankScope 반려동물 사랑 적금', 'Scope 결혼 준비 적금',
    'BankScope 여행 저금통 적금', 'Scope 재테크 챌린지 적금', 'BankScope 주택 청약 연계 적금',
    'BankScope 전문직 신용 대출', 'Scope 자동차 구매 대출', 'BankScope 대학생 학자금 대출',
    'Scope 리모델링 홈 대출', 'BankScope 법인 시설자금 대출', 'Scope 긴급 생활안정 대출'
]

np.random.seed(42)
data_size = 5000 

data = {
    'age': np.random.randint(20, 80, data_size),
    'is_corporate': np.random.choice([0, 1], data_size, p=[0.85, 0.15]), 
    'total_balance': np.random.randint(0, 100000000, data_size),
    'has_active_loan': np.random.choice([0, 1], data_size, p=[0.7, 0.3]),
    'recent_tx_count': np.random.randint(0, 50, data_size)
}
df = pd.DataFrame(data)


def assign_target(row):

    if row['is_corporate'] == 1:
        if row['total_balance'] > 50000000: 
            return 'BankScope 법인 시설자금 대출' 
        return 'BankScope 법인 단기 예금' 
    

    if row['age'] >= 55: 
        return 'BankScope 시니어 플러스 예금'
    if 19 <= row['age'] <= 34: 
        return 'Scope 청년 드림 적금'
    if row['has_active_loan'] == 1: 
        return 'BankScope 직장인 신용 대출' 
    
  
    return 'Scope 모바일 전용 예금'

df['target_product'] = df.apply(assign_target, axis=1)


df.to_csv('bank_data_2.csv', index=False)
print(f"DB 연동용 데이터 {data_size}건 생성 완료 (bank_data_2.csv)")