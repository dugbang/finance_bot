import asyncio
import unittest

from ai_logic import get_stock_recommendation


class TestAiLogicIntegration(unittest.TestCase):
    """실제 Ollama 서버와 통신하는 통합 테스트 케이스입니다."""

    def test_get_stock_recommendation_real_call(self):
        # 실제 CrewAI 수행 (네트워크 통신 발생)
        # 이 테스트는 서버가 켜져 있어야 하며 시간이 다소 소요될 수 있습니다.
        try:
            # # note; 중간에 멈추는 증상이 발생하여 일단 주석처리함
            # raise Exception('중간에 멈추는 증상이 발생하여 실행하지 않음.')
            result = asyncio.run(get_stock_recommendation())
            print(f"\n[통합 테스트 결과]\n{result}")

            # 최소한의 결과 검증 (문자열이고 비어있지 않아야 함)
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)

        except Exception as e:
            self.fail(f"Ollama 서버 통신 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    unittest.main()
