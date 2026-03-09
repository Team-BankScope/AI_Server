import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# 1. 데이터 불러오기 (아까 만든 파일)
df = pd.read_csv('bank_customers.csv')

# 2. 학습할 재료(X)와 정답(y) 나누기
X = df.drop('target_task', axis=1) 
y = df['target_task']              

# 3. 훈련 데이터와 테스트 데이터 분리 (8:2 비율)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. 랜덤 포레스트 모델 생성 및 학습
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. 모델 평가 (AI가 얼마나 잘 맞추나?)
y_pred = model.predict(X_test)
print(f"✅ 모델 정확도: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\n[상세 보고서]")
print(classification_report(y_test, y_pred))

# 6. 학습된 모델 저장 (이 파일이 나중에 스프링과 연결할 '뇌'가 됩니다)
joblib.dump(model, 'bank_model.pkl')
print("\n💾 모델 저장 완료: bank_model.pkl")

# 7. 어떤 데이터가 가장 중요했는지 확인 (졸업작품 발표용 필살기)
feature_importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
print("\n[AI의 판단 근거 (중요도)]")
print(feature_importances)