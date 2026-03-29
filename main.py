def main():
    """finance-bot 실행을 위한 진입점입니다."""
    print("🚀 금융 분석 봇(Finance Bot)을 시작합니다...")

    # bot.py를 별도 프로세스로 실행 (uv run bot.py)
    # 직접 import해서 실행할 수도 있지만, 별도 프로세스가 관리에 용이할 수 있음
    # 여기서는 간단하게 os.system 또는 subprocess를 사용하거나 bot.run()을 호출함

    # bot.py의 run()을 직접 호출하기 위해 bot 객체를 import함
    from bot import TOKEN, bot

    if not TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN을 찾을 수 없습니다. .env 파일을 확인하세요.")
        return

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
