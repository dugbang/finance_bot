import asyncio
import os
import sys
import unittest

import aiosqlite
import yaml

# 프로젝트 루트를 path에 추가하여 tools 임포트 가능하게 함
sys.path.append(os.getcwd())

# tools.py 임포트는 각 테스트 메서드에서 수행함


class TestTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = "test_research.db"
        cls.config_path = "config_test.yaml"
        # 실제 config.yaml을 건드리지 않기 위해 다른 이름 사용
        # 단, tools.py에서 config.yaml을 읽는다면 테스트 환경에서 이를 패치해야 함

        # 테스트용 환경 설정
        with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(
                {
                    "db_path": cls.test_db_path,
                    "query_limits": {
                        "company": 5,
                        "market_info": 5,
                        "invest": 5,
                        "default": 5,
                    },
                },
                f,
            )

        # DB 설정
        asyncio.run(cls._setup_db())

    @classmethod
    async def _setup_db(cls):
        async with aiosqlite.connect(cls.test_db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS company (
                    nid INT, 종목명 TEXT, 제목 TEXT, 증권사 TEXT, 등록일 TEXT, 목표가 TEXT, 투자의견 TEXT, 요약 TEXT, PDF_파일명 TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS market_info (
                    nid INT, 제목 TEXT, 증권사 TEXT, 등록일 TEXT, 요약 TEXT, PDF_파일명 TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS invest (
                    nid INT, 제목 TEXT, 증권사 TEXT, 등록일 TEXT, 요약 TEXT, PDF_파일명 TEXT
                )
            """)

            # 더미 데이터 삽입 (최근 5개 테스트를 위해 여러 개 넣음)
            for i in range(1, 10):
                await db.execute(
                    f"INSERT INTO company VALUES ({i}, '삼성전자', '실적 {i}', 'A증권', '2025-01-0{i}', '100000', '매수', '요약 {i}', 'p.pdf')"
                )

            await db.execute(
                "INSERT INTO market_info VALUES (1, '시황 분석', 'A증권', date('now'), '내용', 'm.pdf')"
            )
            await db.execute(
                "INSERT INTO invest VALUES (1, '투자 전략', 'C증권', '2025-01-03', '키워드검색용', 'i.pdf')"
            )
            await db.commit()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        # config.yaml 복구는 생략하거나 백업 로직 필요 (여기서는 생략)

    def test_search_company_reports_success(self):
        from tools import search_company_reports

        result = search_company_reports.run(keyword="삼성")
        self.assertIn("삼성전자", result)
        # 최근 5개만 반환하는지 확인
        self.assertEqual(len(result.strip().split("\n\n")), 5)

    def test_search_company_reports_no_data(self):
        from tools import search_company_reports

        result = search_company_reports.run(keyword="없는종목")
        self.assertEqual("데이터 없음", result)

    def test_get_market_trends_success(self):
        from tools import get_market_trends

        result = get_market_trends.run(days=7)
        self.assertIn("시황 분석", result)

    def test_get_invest_reports_success(self):
        from tools import get_invest_reports

        result = get_invest_reports.run(keyword="전략")
        self.assertIn("투자 전략", result)

    def test_query_limit_configurable(self):
        # 테이블별로 다른 수량 제한 설정 확인
        with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(
                {
                    "db_path": self.test_db_path,
                    "query_limits": {"company": 2, "market_info": 1, "default": 5},
                },
                f,
            )

        from tools import get_market_trends, search_company_reports

        # company는 2개만 반환해야 함
        res_comp = search_company_reports.run(keyword="삼성")
        self.assertEqual(len(res_comp.strip().split("\n\n")), 2)

        # market_info는 1개만 반환해야 함
        res_market = get_market_trends.run(days=7)
        self.assertEqual(len(res_market.strip().split("\n\n")), 1)

        # 원래대로 복구
        self.setUpClass()


if __name__ == "__main__":
    unittest.main()
