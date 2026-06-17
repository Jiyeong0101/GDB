# MyRPG DB Scenario Project

## 실행 순서

### 1. MariaDB 실행
cd C:\Bitnami\wampstack-8.1.2-0\mariadb\bin
mysqld.exe --console

### 2. DB 초기화
mysql -uroot -pbitnami mysql < sql/create_db.sql
mysql -urpg -prpg MyRPG < sql/RPG.sql
mysql -urpg -prpg MyRPG < sql/populate_rpg.sql
mysql -urpg -prpg MyRPG < sql/populate_project_scenario.sql

### 3. 서버 실행
cd server
python main.py
http://127.0.0.1:8000/docs

### 4. 클라이언트 실행
cd client
streamlit run client.py

## 주요 시나리오
회원가입/로그인 → 캐릭터 생성 → 첫 전투 훈련 → 슬라임 처치 → 레벨업 → NPC 퀘스트 수락 → 고블린 전투 → 마나 포션 사용 → 보상 지급 → 전투 기록 확인

## 가상환경 생성
파일경로로 이동
python -m venv venv
venv\Scripts\activate.bat

## 필요한 라이브러리 설치
pip install fastapi uvicorn sqlalchemy pymysql pydantic
pip install streamlit