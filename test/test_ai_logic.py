import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from ai_logic import get_stock_recommendation


class TestAiLogic(unittest.TestCase):
    @patch("ai_logic.Crew")
    @patch("ai_logic.Agent")
    @patch("ai_logic.Task")
    @patch("ai_logic.LLM")
    def test_get_stock_recommendation_structure(
        self, mock_llm, mock_task, mock_agent, mock_crew
    ):
        # Mocking the interaction
        mock_crew_instance = mock_crew.return_value
        # kickoff_async는 비동기 함수이므로 AsyncMock 사용
        mock_crew_instance.kickoff_async = AsyncMock(return_value="Test Report Result")

        # Execution
        result = asyncio.run(get_stock_recommendation())

        # Verify calls
        mock_crew.assert_called_once()
        mock_crew_instance.kickoff_async.assert_called_once()
        self.assertEqual(result, "Test Report Result")


if __name__ == "__main__":
    unittest.main()
