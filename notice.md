# 가상 환경 실행 및 모델 학습 가이드

터미널을 새로 열거나 재시작하면 파이썬 가상 환경이 꺼지게 되어 `pandas` 등의 모듈을 찾을 수 없다는 에러가 발생합니다.

## 1. 패키지 설치 (최초 1회)

```bash
pip install -r requirements.txt
```

## 2. 가상 환경 활성화 (필수)

이미 만들어진 가상 환경(`.venv`)을 켜주기만 하면 됩니다.

**Windows:**
```bash
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

> **성공 확인 방법:**
> 터미널 입력창 맨 앞에 `(.venv)`가 나타나면 가상 환경이 정상적으로 켜진 것입니다.

<br>

## 3. 창구 배정 AI 모델 학습

가상 환경이 켜진 상태에서 아래 명령어를 실행합니다.

```bash
python RF.py
```

> 학습이 완료되면 `bank_model.pkl` 파일이 생성되며, 모델 정확도와 상세 보고서가 출력됩니다.
> 정확도 85% 미만이면 모델이 저장되지 않습니다.

## 4. 서버 실행

```bash
uvicorn main:app --reload --port 8000
```