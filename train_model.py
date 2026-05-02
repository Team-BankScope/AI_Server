import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import platform
import matplotlib.pyplot as plt
import seaborn as sns

print("2. 랜덤 포레스트 모델 학습 시작...")

# 1. 저장해둔 CSV 파일 불러오기
df_loaded = pd.read_csv('bank_customers_real.csv')

# 테스트해볼 피처 조합 (필요시 여기서 넣고 빼면서 테스트 가능)
SELECTED_FEATURES = [
    'age',
    'is_corporate',
    'total_balance',
    'has_active_loan',
    'recent_tx_count'
]

# 2. 데이터 분리
X = df_loaded[SELECTED_FEATURES]
y = df_loaded['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. 모델 하이퍼파라미터 세팅 및 학습
model = RandomForestClassifier(
    n_estimators=500,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=3,
    max_features='sqrt',
    criterion='entropy',
    random_state=42
)
model.fit(X_train, y_train)

# # 4. 정확도 확인
# y_train_pred = model.predict(X_train)
# y_test_pred = model.predict(X_test) # 기존의 y_pred 역할
#
# print(f"\n학습 데이터 정확도: {accuracy_score(y_train, y_train_pred) * 100:.2f}%")
# print(f"테스트 데이터 정확도(최종): {accuracy_score(y_test, y_test_pred) * 100:.2f}%")
#
# print("\n[상세 보고서]")
# print(classification_report(y_test, y_test_pred, target_names=['빠른업무(0)', '상담업무(1)', '특수업무(2)']))
#
# # 5. XAI: Feature Importance (설명 가능한 AI 파트)
# print("\nXAI: Feature Importance 분석 및 시각화 진행 중...")
#
# # 5-1. 한글 폰트 깨짐 방지 (내 컴퓨터 OS에 맞게 자동 세팅)
# if platform.system() == 'Windows':
#     plt.rc('font', family='Malgun Gothic') # 윈도우는 맑은 고딕
# elif platform.system() == 'Darwin':
#     plt.rc('font', family='AppleGothic')   # 맥은 애플 고딕
# plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지
#
# # 5-2. 중요도 데이터 추출 및 정렬
# feature_importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
#
# # 5-3. 그래프 그리기
# plt.figure(figsize=(10, 6))
# sns.barplot(x=feature_importances.values, y=feature_importances.index, palette='viridis')
# plt.title('Random Forest Feature Importance (어떤 데이터가 창구 분류에 가장 중요했을까?)')
# plt.xlabel('Importance (불순도 감소량)')
# plt.ylabel('Features')
# plt.tight_layout()
#
# # 5-4. 화면에 띄우는 대신 이미지 파일로 저장
# xai_filename = 'feature_importance_result.png'
# plt.savefig(xai_filename, dpi=300) # dpi=300은 고화질 저장을 의미함
# print(f"📸 찰칵! XAI 분석 그래프가 '{xai_filename}' 파일로 저장되었습니다!")
#
# # 만약 팝업창으로도 꼭 보고 싶다면
# # plt.show()
#
# # 6. 완성된 모델을 파일로 저장 (기존 파일명 매칭)
# model_filename = 'bank_model.pkl'
# joblib.dump(model, model_filename)
# print(f"\n학습된 모델을 '{model_filename}'로 저장 완료!")