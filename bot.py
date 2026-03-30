import asyncio
import os
import time

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# 환경 변수 로드 (내부 모듈 임포트 전 실행)
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

from graph.workflow import app  # noqa: E402

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True


class FinanceBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 슬래시 명령어 동기화
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


bot = FinanceBot()


cache = {}
CACHE_DURATION = 3600  # 1시간


async def send_report_chunks(ctx_or_interaction, result: str):
    """결과 보고서가 2000자를 초과할 경우 나누어서 전송합니다."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    target = ctx_or_interaction.followup if is_interaction else ctx_or_interaction

    if len(result) <= 2000:
        await target.send(result)
    else:
        chunks = [result[i : i + 1900] for i in range(0, len(result), 1900)]
        for chunk in chunks:
            await target.send(chunk)


async def run_workflow(ticker: str, initial_state: dict, msg_obj, edit_func):
    """LangGraph 워크플로우를 실행하고 중간 상태를 업데이트하며 최종 상태를 반환합니다."""
    final_state = {}
    async with asyncio.timeout(600):
        async for step in app.astream(initial_state):
            # 각 노드 완료 시 상태 메시지 업데이트
            if "market" in step:
                await edit_func(
                    message_id=msg_obj.id,
                    content=f"✅ 시장 트렌드 분석 완료\n📊 **{ticker}** 종목 상세 리포트 스닝 중...",
                )
            elif "stock" in step:
                await edit_func(
                    message_id=msg_obj.id,
                    content="✅ 시장 및 종목 분석 완료\n📝 최종 종합 보고서 작성 중...",
                )

            # 마지막 상태 저장
            for _, value in step.items():
                final_state = value
    return final_state


async def handle_langgraph_analysis(ctx_or_interaction, ticker: str):
    """LangGraph 워크플로우를 실행하고 캐시를 고려하여 Discord로 결과를 전송합니다."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)

    if ticker in cache:
        cached_data = cache[ticker]
        if time.time() - cached_data["timestamp"] < CACHE_DURATION:
            msg = f"📌 **{ticker}**에 대한 최근 1시간 이내의 분석 결과가 있습니다. (캐시 사용)"
            if is_interaction:
                await ctx_or_interaction.response.send_message(msg)
            else:
                await ctx_or_interaction.send(msg)
            await send_report_chunks(ctx_or_interaction, cached_data["report"])
            return

    # 0. 초기 응답 및 상태 메시지 전송
    status_msg = f"🔍 **{ticker}** 분석을 시작합니다... (최대 10분 소요)"

    if is_interaction:
        await ctx_or_interaction.response.send_message(status_msg)
        followup = ctx_or_interaction.followup
        edit_func = followup.edit_message
        msg_obj = await ctx_or_interaction.original_response()
    else:
        msg_obj = await ctx_or_interaction.send(status_msg)
        edit_func = msg_obj.edit

    # 초기 상태 설정
    initial_state = {
        "user_query": f"{ticker}에 대해 분석해줘",
        "company_name": ticker,
        "retry_count": 0,
        "stock_candidates": [],
        "errors": [],
    }

    try:
        # 1. 워크플로우 실행
        final_state = await run_workflow(ticker, initial_state, msg_obj, edit_func)

        # 2. 최종 결과 전송
        result = final_state.get("final_report", "⚠️ 보고서를 생성하지 못했습니다.")

        if result and "⚠️" not in result:
            cache[ticker] = {"report": result, "timestamp": time.time()}

        await send_report_chunks(ctx_or_interaction, result)

    except TimeoutError:
        error_text = "⚠️ 분석 시간이 10분을 초과하여 중단되었습니다."
        target = ctx_or_interaction.followup if is_interaction else ctx_or_interaction
        await target.send(error_text)
    except Exception as e:
        error_text = f"❌ 분석 중 오류가 발생했습니다: {str(e)}"
        target = ctx_or_interaction.followup if is_interaction else ctx_or_interaction
        await target.send(error_text)


@bot.tree.command(
    name="analyze", description="LangGraph를 사용하여 종목을 정밀 분석합니다."
)
@app_commands.describe(ticker="분석할 종목명 (예: 삼성전자)")
async def analyze_slash(interaction: discord.Interaction, ticker: str):
    await handle_langgraph_analysis(interaction, ticker)


@bot.command(name="analyze")
async def analyze_prefix(ctx, ticker: str):
    await handle_langgraph_analysis(ctx, ticker)


@bot.tree.command(name="test", description="봇의 응답 기능을 테스트합니다.")
async def test_slash(interaction: discord.Interaction):
    await interaction.response.send_message("✅ LangGraph 봇이 정상 작동 중입니다!")


if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in .env file.")
    else:
        bot.run(TOKEN)
