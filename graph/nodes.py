import logging
import time
from typing import Literal

from langchain_ollama import ChatOllama

from graph.state import GraphState
from tools import get_market_trends, search_company_reports

# 로깅 설정
logger = logging.getLogger("finance_bot.nodes")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ChatOllama 설정
llm = ChatOllama(
    model="minimax-m2.7:cloud",
    base_url="http://localhost:11434",
    temperature=0.1,
    num_ctx=4096,  # 컨텍스트 창 명시적 설정
)


def truncate_text(text: str, max_length: int = 1500) -> str:
    """텍스트가 너무 길 경우 절단하고 말줄임표를 추가합니다."""
    if len(text) <= max_length:
        return text
    logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
    return text[:max_length] + "... (이하 생략)"


async def analyze_market(state: GraphState) -> GraphState:
    """LangGraph의 첫 번째 노드: 최근 시장 트렌드와 리스크를 분석합니다."""
    start_time = time.time()
    logger.info("Entering analyze_market node")

    # 1. 도구를 사용하여 시장 트렌드 데이터 조회 (최근 7일)
    try:
        retrieved_data = await get_market_trends(days=7)
        if not retrieved_data:
            data_str = "조회된 최근 시황 데이터가 없습니다."
        else:
            # 개별 항목 요약 절단 및 전체 데이터 양 제한 (최신 순 5개만 사용 권장)
            items = []
            for item in retrieved_data[:7]:  # 최근 7개 항목으로 제한
                items.append(
                    f"[{item.get('등록일')}] {item.get('제목')}: {truncate_text(str(item.get('요약', '')))}"
                )
            data_str = "\n".join(items)
            data_str = truncate_text(
                data_str, 3000
            )  # 전체 시장 분석 데이터 3000자 제한

    except Exception as e:
        logger.error(f"Error in analyze_market data retrieval: {str(e)}")
        return {
            "errors": [f"시장 데이터 조회 실패: {str(e)}"],
            "analysis_step": "stock",
        }

    # 2. Ollama에게 분석 요청
    prompt = f"""
    다음 시장 리포트 데이터를 분석하여 트렌드 3가지와 리스크 2가지를 추출하세요.
    반드시 한국어로 답변하고, 마크다운 불릿 리스트 형식을 사용하세요.

    [데이터]
    {data_str}
    """

    try:
        response = await llm.ainvoke(prompt)
        market_summary = response.content
        logger.info(f"Market analysis completed in {time.time() - start_time:.2f}s")
        return {"market_summary": market_summary, "analysis_step": "stock"}

    except Exception as e:
        logger.error(f"Error in analyze_market LLM call: {str(e)}")
        return {
            "errors": [f"시장 분석 LLM 호출 실패: {str(e)}"],
            "analysis_step": "stock",
        }


async def analyze_stocks(state: GraphState) -> GraphState:
    """LangGraph의 두 번째 노드: 특정 종목의 리포트를 상세 분석합니다."""
    start_time = time.time()
    user_query = state.get("user_query", "")
    current_retry = state.get("retry_count", 0)
    logger.info(f"Entering analyze_stocks node (retry: {current_retry})")

    # 1. 사용자 질문에서 종목명 추출
    company_name = state.get("company_name", "")
    if not company_name or current_retry > 0:
        extract_prompt = f"다음 문장에서 분석 대상인 주식 종목명만 한 단어로 추출하세요. 없으면 'None'이라고 답하세요.\n문장: {user_query}"
        res = await llm.ainvoke(extract_prompt)
        company_name = res.content.strip()

    # 2. 종목 리포트 검색
    search_keyword = company_name
    if current_retry == 1:
        search_keyword = company_name + " "
    elif current_retry >= 2:
        search_keyword = company_name[:-1] if len(company_name) > 1 else company_name

    reports = await search_company_reports(search_keyword)

    # 3. 데이터가 없는 경우 처리
    if not reports or reports == "데이터 없음":
        logger.warning(f"No reports found for {search_keyword}")
        return {
            "errors": [
                f"'{search_keyword}'에 대한 종목 데이터 없음 (시도: {current_retry + 1})"
            ],
            "retry_count": 1,
        }

    # 4. 데이터가 있는 경우 상세 분석
    # reports는 List[Dict]이므로 요약 정보만 추출하여 길이를 제한함
    formatted_reports = []
    for r in reports[:2]:  # 가장 관련성 높은 리포트 2개만 사용
        content = f"제목: {r.get('제목')}\n증권사: {r.get('증권사')}\n요약: {truncate_text(str(r.get('요약', '')), 2000)}"
        formatted_reports.append(content)

    data_str = "\n---\n".join(formatted_reports)

    analysis_prompt = f"""
    다음 종목 리포트 데이터를 분석하여 '투자의견, 목표가, 핵심 근거'를 추출하세요.
    반드시 한국어로 요약하고, 마크다운 형식으로 작성하세요.

    [데이터]
    {data_str}
    """

    try:
        response = await llm.ainvoke(analysis_prompt)
        analysis_result = {"ticker": company_name, "analysis": response.content}
        logger.info(
            f"Stock analysis for {company_name} completed in {time.time() - start_time:.2f}s"
        )
        return {
            "stock_candidates": [analysis_result],
            "analysis_step": "final",
            "company_name": company_name,
        }
    except Exception as e:
        logger.error(f"Error in analyze_stocks LLM call: {str(e)}")
        return {
            "errors": [f"종목 상세 분석 중 오류: {str(e)}"],
            "analysis_step": "final",
        }


def should_retry_or_proceed(state: GraphState) -> Literal["analyze_stocks", "finalize"]:
    """분석 결과 데이터 부족 시 재시도 여부를 결정하는 조건부 분기 함수입니다."""
    retry_count = state.get("retry_count", 0)
    candidates = state.get("stock_candidates", [])

    if not candidates and retry_count < 3:
        logger.info(f"Retrying stock analysis (count: {retry_count})")
        return "analyze_stocks"

    logger.info("Proceeding to finalize_report")
    return "finalize"


async def finalize_report(state: GraphState) -> GraphState:
    """LangGraph의 마지막 노드: 시장 및 종목 분석 결과를 종합하여 최종 보고서를 생성합니다."""
    start_time = time.time()
    logger.info("Entering finalize_report node")
    market_summary = state.get("market_summary", "시장 분석 데이터가 없습니다.")
    stock_candidates = state.get("stock_candidates", [])
    company_name = state.get("company_name", "해당 종목")

    stock_info_str = ""
    if not stock_candidates:
        stock_info_str = "상세 종목 분석 데이터를 찾을 수 없어 분석이 불가능합니다."
    else:
        for candidate in stock_candidates:
            stock_info_str += (
                f"- {candidate.get('ticker')}: {candidate.get('analysis')}\n"
            )

    prompt = f"""
    다음 데이터를 종합하여 상세한 투자 보고서를 작성하세요. 상업적이고 전문적인 톤을 유지하세요.
    데이터에 없는 정보는 절대로 생성하지 마세요 (할루시네이션 방지).

    [시장 분석]
    {truncate_text(market_summary, 1500)}

    [종목 분석]
    {truncate_text(stock_info_str, 2000)}

    [출력 형식]
    ## 📈 {company_name} 투자 보고서
    - 💡 투자 의견: [데이터에 기반한 Buy/Hold/Sell 중 선택]
    - 🎯 목표가: [데이터에 명시된 가격]
    - 📌 선정 근거: [3가지 핵심 포인트 요약]
    - ⚠️ 리스크 요인: [데이터 기반 1가지 이상]
    - 📚 데이터 출처: [참조된 증권사 또는 리포트 제목]

    > ⚠️ 면책 조항: 본 내용은 참고용이며, 모든 투자 책임은 사용자에게 있습니다.
    """

    try:
        response = await llm.ainvoke(prompt)
        final_report = response.content
        if "면책 조항" not in final_report:
            final_report += "\n\n> ⚠️ 면책 조항: 본 내용은 참고용이며, 모든 투자 책임은 사용자에게 있습니다."

        logger.info(
            f"Final report generation completed in {time.time() - start_time:.2f}s"
        )
        return {"final_report": final_report, "analysis_step": "done"}
    except Exception as e:
        logger.error(f"Error in finalize_report: {str(e)}")
        return {"errors": [f"최종 보고서 생성 실패: {str(e)}"], "analysis_step": "done"}
