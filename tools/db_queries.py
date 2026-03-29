from typing import Any

import aiosqlite
import yaml


def get_db_path() -> str:
    """config.yaml에서 데이터베이스 경로를 가져옵니다."""
    try:
        with open("config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("db_path", "../../jjajang/data/naver/research.db3")
    except Exception:
        return "../../jjajang/data/naver/research.db3"


async def _execute_query(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    """일반화된 쿼리 실행 및 Dict 리스트 반환 유틸리티입니다."""
    db_path = get_db_path()
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        print(f"Database Query Error: {e}")
        return []


async def search_company_reports(keyword: str, limit: int = 5) -> list[dict[str, Any]]:
    """종목명 또는 리포트 제목으로 기업 리포트를 검색합니다."""
    query = """
        SELECT 종목명, 제목, 증권사, 등록일, 목표가, 투자의견, 요약
        FROM company
        WHERE 종목명 LIKE ? OR 제목 LIKE ?
        ORDER BY 등록일 DESC
        LIMIT ?
    """
    params = (f"%{keyword}%", f"%{keyword}%", limit)
    return await _execute_query(query, params)


async def get_market_trends(days: int = 7) -> list[dict[str, Any]]:
    """최근 N일간의 시장(market_info) 및 산업(industry) 트렌드를 통합 조회합니다."""
    # 두 테이블의 결과를 날짜순으로 통합 (UNION ALL)
    query = """
        SELECT 'market' as source, 제목, 증권사, 등록일, 요약
        FROM market_info
        WHERE 등록일 >= date('now', ?)
        UNION ALL
        SELECT 'industry' as source, 제목, 증권사, 등록일, 요약
        FROM industry
        WHERE 등록일 >= date('now', ?)
        ORDER BY 등록일 DESC
    """
    days_str = f"-{days} days"
    params = (days_str, days_str)
    return await _execute_query(query, params)


async def get_invest_reports(keyword: str, limit: int = 5) -> list[dict[str, Any]]:
    """투자 전략 및 거시적 리포트를 키워드로 검색합니다."""
    query = """
        SELECT 제목, 증권사, 등록일, 요약
        FROM invest
        WHERE 제목 LIKE ? OR 요약 LIKE ?
        ORDER BY 등록일 DESC
        LIMIT ?
    """
    params = (f"%{keyword}%", f"%{keyword}%", limit)
    return await _execute_query(query, params)
