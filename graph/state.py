import operator
from typing import Annotated, Any, Literal, TypedDict

# 현재 진행 단계를 관리하는 Literal 타입 정의
AnalysisStep = Literal["start", "market", "stock", "final", "done"]


class GraphState(TypedDict):
    """LangGraph 주식 분석 시스템의 상태(State)를 정의합니다."""

    user_query: str
    """사용자가 입력한 분석 요청 (예: "삼성전자 분석해줘")"""

    company_name: str
    """분석 대상 종목명 또는 키워드 (분석 과정에서 도출)"""

    market_summary: str
    """시장 분석 결과 및 주요 트랜드를 담는 문자열"""

    stock_candidates: Annotated[list[dict[str, Any]], operator.add]
    """분석 결과 도출된 후보 종목 리스트 (연산자: add를 통한 누적 관리)"""

    final_report: str
    """최종 투자 요약 리포트 (마크다운 형식)"""

    analysis_step: AnalysisStep
    """현재 시스템이 진행 중인 단계 (Enum-like Literal)"""

    retry_count: int
    """에러 발생 또는 데이터 부족 시 루프 제어를 위한 재시도 횟수"""

    errors: Annotated[list[str], operator.add]
    """시스템 실행 중 발생한 에러 로그 (연산자: add를 통한 누적 관리)"""
