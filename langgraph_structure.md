# 🏗️ LangGraph 주식 분석 시스템 구조 제안

LangGraph의 상태(`State`) 정의와 함께 프로젝트의 유지보수성을 극대화할 수 있는 디렉토리 구조를 제안합니다.

## 1. 제안하는 디렉토리 구조 (LangGraph 스타일)

```bash
finance_bot/
├── graph/                # LangGraph 관련 핵심 로직
│   ├── __init__.py
│   ├── state.py          # [작성 완료] 상태(GraphState) 정의
│   ├── nodes.py          # 각 노드(함수)별 비동기 로직 (Ollama, SQL 조회 등)
│   └── workflow.py       # StateGraph 생성 및 엣지(흐름) 정의
├── data/                 # 데이터 처리 및 DB 관련 (db_tools.py, tools.py)
├── bot.py                # Discord 인터페이스 및 메시지 핸들러
├── config.yaml           # 공통 설정 파일 (모델, DB 경로 등)
└── .env                  # 환경 변수 (토큰, API 키)
```

## 2. GraphState 구성 및 특징

현재 `graph/state.py`에 적용된 주요 특징은 다음과 같습니다.

| 필드명 | 타입 | 특징 |
| :--- | :--- | :--- |
| `user_query` | `str` | 사용자 질문 원본 |
| `stock_candidates` | `Annotated[list[dict], add]` | `operator.add`를 통해 각 노드 데이터의 누적 업데이트 가능 |
| `analysis_step` | `Literal` | 'start', 'market' 등 현재 진행 상태를 명시적으로 관리 |
| `errors` | `Annotated[list[str], add]` | 여러 단계에서 발생한 경고나 에러를 리스트로 합산 보관 |

## 3. 향후 구현 가이드 (Async 기반)

Ollama 로컬 서버(localhost:11434)와 Discord 연동을 고려한 비동기 노드 예시입니다.

### Nodes (graph/nodes.py)
```python
import ollama
from graph.state import GraphState

async def analyze_market_node(state: GraphState) -> GraphState:
    # 1. tools.py에서 데이터 조회
    # 2. Ollama에 분석 요청 (asyncio.to_thread 또는 aiohttp 활용)
    # 3. 상태 업데이트 (market_summary 등)
    return {
        "market_summary": "시장 동향 분석 완료...",
        "analysis_step": "market"
    }
```

### Workflow (graph/workflow.py)
```python
from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import analyze_market_node, ...

workflow = StateGraph(GraphState)
workflow.add_node("analyze_market", analyze_market_node)
# ... 엣지 추가
workflow.set_entry_point("analyze_market")
app = workflow.compile()
```

이 구조는 각 노드가 독립적으로 작동하므로 디버깅이 쉬우며, Discord 봇에서 `app.ainvoke()`를 통해 간단하게 호출할 수 있는 장점이 있습니다.
