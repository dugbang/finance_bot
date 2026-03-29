from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    analyze_market,
    analyze_stocks,
    finalize_report,
    should_retry_or_proceed,
)
from graph.state import GraphState


def create_app():
    """LangGraph 노드들을 조립하여 실행 가능한 워크플로우 앱을 생성합니다."""
    # 1. StateGraph 초기화 (GraphState 기반)
    workflow = StateGraph(GraphState)

    # 2. 노드 등록 (함수와 노드 이름 매핑)
    workflow.add_node("market", analyze_market)
    workflow.add_node("stock", analyze_stocks)
    workflow.add_node("finalize", finalize_report)

    # 3. 엣지 연결 (워크플로우 흐름 정의)
    # 시작점 -> 시장 분석 노드
    workflow.add_edge(START, "market")

    # 시장 분석 -> 종목 분석 노드
    workflow.add_edge("market", "stock")

    # 종목 분석 -> (조건부 분기) -> 재시도 또는 최종 보고서
    workflow.add_conditional_edges(
        "stock",
        should_retry_or_proceed,
        {
            "analyze_stocks": "stock",  # 재시도 시 다시 stock 노드로
            "finalize": "finalize",  # 성공 시 finalize 노드로
        },
    )

    # 최종 보고서 -> 종료
    workflow.add_edge("finalize", END)

    # 4. 그래프 컴파일
    return workflow.compile()


# 실행 가능한 앱 인스턴스 생성
app = create_app()
