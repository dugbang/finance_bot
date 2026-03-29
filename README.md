# 📊 Finance Bot (LangGraph AI 증권 분석 봇)

LangGraph와 Ollama(로컬 LLM)를 기반으로 하는 정밀 주식 분석 Discord 봇입니다.
시장 트렌드 분석, 종목별 증권사 리포트 스닝, 투자 전략 수립을 자동화하여 고퀄리티의 리포트를 제공합니다.

## 🚀 시작하기

### 1. 사전 준비 (Prerequisites)
- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (고속 패키지 매니저)
- [Ollama](https://ollama.com/) (로컬 LLM 서버: `minimax-m2.7:cloud` 모델 설치 권장)
- [Discord Bot Token](https://discord.com/developers/applications)

### 2. 설치 및 실행
```bash
# 리포지토리 클론 후 이동
cd finance_bot

# 가상환경 생성 및 의존성 설치
uv init

# 환경 변수 설정
cp .env.example .env
# .env 파일에 DISCORD_BOT_TOKEN 입력 필수

# 봇 실행
uv run main.py
```

## 🛠️ 주요 기능
- **시장 분석**: 최근 7일간의 시황 및 산업 트렌드 요약 (trends 3개, risks 2개)
- **종목 정밀 분석**: 특정 종목 리포트 검색 및 핵심 투자 근거 도출 (목표가, 투자의견 포함)
- **에이전틱 워크플로우**: 검색 결과 부족 시 3단계 자동 재시도 (LangGraph 기반)
- **실시간 알림**: 디스코드 중간 상태 업데이트 ("분석 중...", "보고서 작성 중...")
- **캐싱**: 동일 종목 재요청 시 1시간 동안 캐시 결과 즉각 전송

## ❓ 트러블슈팅 가이드

### 1. Ollama 연결 실패 (`Connection Error`)
- `ollama serve` 명령어가 백그라운드에서 실행 중인지 확인하세요.
- `.env`의 `OLLAMA_URL`이 `http://localhost:11434` (기본값)인지 확인하세요.
- 로컬 환경 외의 다른 서버(예: 192.168.0.x)인 경우 방화벽 설정을 체크하세요.

### 2. Discord 봇이 응답하지 않을 때
- 봇의 `TOKEN`이 올바르게 입력되었는지 확인하고, 봇이 서버에 초대되어 있는지 체크하세요.
- 봇 권한 중 `MESSAGE_CONTENT` 인텐트가 허용되어야 합니다.
- `setup_hook` 단계에서 명령어 동기화(`Synced slash commands`)를 확인하세요.

### 3. SQLite 락 (`database is locked`) 해결
- 동시에 여러 쿼리가 DB에 쓰기 작업을 시도할 때 발생할 수 있습니다.
- 이 프로젝트는 읽기 전용으로 설정되어 있으나, 다른 프로세스에서 쓰기 중일 수 있으니 DB 접근 권한을 확인하세요.
- `db_path`가 올바른 마운트 위치를 가리키고 있는지 체크하세요.

## 📅 라이선스
MIT License

> ⚠️ **면책 조항**: 본 봇이 제공하는 정보는 투자 권유가 아니며, 최종 투자 책임은 사용자 본인에게 있습니다.
