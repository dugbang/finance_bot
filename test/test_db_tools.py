import asyncio
import os
import unittest

import aiosqlite
import yaml
from db_tools import query_finance_db


class TestDBTools(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_finance.db"
        self.config_path = "config.yaml"
        # config.yaml 백업 (있다면)
        self.original_config_content = None
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as f:
                self.original_config_content = f.read()

        # 테스트용 config.yaml 생성
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump({"db_path": self.test_db_path}, f)

        # 테스트용 DB 및 테이블 생성
        asyncio.run(self._setup_test_db())

    async def _setup_test_db(self):
        async with aiosqlite.connect(self.test_db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS invest (
                    nid INT, 제목 TEXT, 증권사 TEXT, 등록일 TEXT, 요약 TEXT, PDF_파일명 TEXT
                )
            """)
            await db.execute("""
                INSERT INTO invest (nid, 제목, 증권사, 등록일, 요약, PDF_파일명)
                VALUES (1, '테스트 제목', '테스트 증권사', '2024-03-26', '테스트 요약', 'test.pdf')
            """)
            await db.commit()

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        # config.yaml 복구
        if self.original_config_content is not None:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(self.original_config_content)

    def test_query_finance_db_success(self):
        query = "SELECT 제목 FROM invest WHERE nid = 1"
        result = asyncio.run(query_finance_db._arun(query=query))
        self.assertIn("테스트 제목", result)

    def test_query_finance_db_error(self):
        query = "SELECT * FROM non_existent_table"
        result = asyncio.run(query_finance_db._arun(query=query))
        self.assertIn("Error", result)


if __name__ == "__main__":
    unittest.main()
