"# AI_Server" 
pip 명령어를 찾을 수 없다는 에러가 발생했네요. 현재 프로젝트 폴더에 venv (가상 환경) 폴더가 있는 것으로 보입니다. 가상 환경을 활성화하거나 pip3를 사용해야 합니다.
터미널에서 아래 명령어들을 순서대로 실행해 보세요.
1. 가상 환경 활성화 (Mac 기준)
Shell Script
source venv/bin/activate
(터미널 프롬프트 앞에 (venv)가 나타나면 성공입니다.)
2. 패키지 설치 가상 환경이 활성화된 상태에서 다시 설치 명령어를 실행해 주세요.
Shell Script
pip install fastapi uvicorn pydantic pandas scikit-learn joblib
(만약 가상 환경을 사용하지 않으신다면 pip3 install ... 로 실행해 보세요.)
3. 서버 실행 설치가 완료되면 서버를 실행합니다.
Shell Script
uvicorn main:app --reload
이제 http://127.0.0.1:8000/docs에 접속하여 API를 테스트해 보실 수 있습니다!


