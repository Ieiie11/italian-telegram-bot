import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
WORDS_FILE = BASE_DIR / "words.json"
STATE_FILE = BASE_DIR / ".state.json"
TIMEZONE = "Europe/Rome"
ROME_TIMEZONE = ZoneInfo(TIMEZONE)


def load_words() -> dict[str, list[dict[str, str]]]:
    with WORDS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict) or not data:
        raise ValueError("words.json must contain at least one topic.")

    return data


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state: dict[str, Any]) -> None:
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def choose_topic(topics: list[str], last_topic: Optional[str]) -> str:
    if len(topics) == 1:
        return topics[0]

    candidates = [topic for topic in topics if topic != last_topic]
    return random.choice(candidates)


def choose_words(
    topic: str,
    words: list[dict[str, str]],
    previous_word_sets: list[list[str]],
    count: int = 5,
) -> list[dict[str, str]]:
    sample_size = min(count, len(words))
    previous_sets = {tuple(sorted(word_set)) for word_set in previous_word_sets}

    for _ in range(30):
        chosen = random.sample(words, sample_size)
        chosen_keys = tuple(sorted(item["italian"] for item in chosen))
        if chosen_keys not in previous_sets:
            return chosen

    return random.sample(words, sample_size)


def build_message(topic: str, words: list[dict[str, str]]) -> str:
    today = datetime.now(ROME_TIMEZONE).strftime("%Y-%m-%d")
    practice_word = random.choice(words)["italian"]
    translation_prompt = random.choice(
        [
            "我想用银行卡付款。",
            "我有一个预约。",
            "请给我收据。",
            "我需要寄一个包裹。",
            "药房在哪里？",
            "这张账单多少钱？",
        ]
    )

    lines = [
        f"🇮🇹 意大利语每日学习推送｜{today}",
        f"今日主题：{topic}",
        "",
    ]

    for index, item in enumerate(words, start=1):
        lines.extend(
            [
                f"{index}. {item['italian']}",
                f"中文：{item['chinese']}",
                f"例句：{item['example_it']}",
                f"翻译：{item['example_zh']}",
                "",
            ]
        )

    lines.extend(
        [
            "小练习：",
            f"1. 用「{practice_word}」造一个简单意大利语句子。",
            f"2. 翻译成意大利语：{translation_prompt}",
        ]
    )

    return "\n".join(lines)


def update_env_chat_id(chat_id: str) -> None:
    os.environ["TELEGRAM_CHAT_ID"] = chat_id

    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return

    lines = env_file.read_text(encoding="utf-8").splitlines()
    updated_lines = []
    found_chat_id = False

    for line in lines:
        if line.startswith("TELEGRAM_CHAT_ID="):
            updated_lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
            found_chat_id = True
        else:
            updated_lines.append(line)

    if not found_chat_id:
        updated_lines.append(f"TELEGRAM_CHAT_ID={chat_id}")

    env_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def send_telegram_message(text: str, chat_id: Optional[str] = None) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not target_chat_id:
        raise RuntimeError(
            "Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file."
        )

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": target_chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    response.raise_for_status()


def send_daily_lesson(chat_id: Optional[str] = None) -> None:
    all_words = load_words()
    state = load_state()

    topics = list(all_words.keys())
    topic = choose_topic(topics, state.get("last_topic"))
    selected_words = choose_words(topic, all_words[topic], state.get("history", {}).get(topic, []))
    message = build_message(topic, selected_words)

    send_telegram_message(message, chat_id=chat_id)

    history = state.setdefault("history", {})
    topic_history = history.setdefault(topic, [])
    topic_history.append([item["italian"] for item in selected_words])
    history[topic] = topic_history[-20:]

    state["last_topic"] = topic
    state["last_sent_at"] = datetime.now(ROME_TIMEZONE).isoformat(timespec="seconds")
    save_state(state)

    print(f"Sent daily Italian lesson for topic: {topic}")


def poll_telegram_messages() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Please set TELEGRAM_BOT_TOKEN in your .env file.")

    state = load_state()
    offset = state.get("last_update_id")
    params = {"timeout": 10}
    if offset is not None:
        params["offset"] = offset + 1

    response = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        params=params,
        timeout=20,
    )
    response.raise_for_status()

    updates = response.json().get("result", [])
    if not updates:
        return

    for update in updates:
        update_id = update.get("update_id")
        if update_id is not None:
            state["last_update_id"] = update_id

        message = update.get("message") or update.get("edited_message")
        if not message:
            continue

        text = message.get("text", "").strip()
        chat = message.get("chat", {})
        chat_id = chat.get("id")

        if text.startswith("/start") and chat_id:
            chat_id_text = str(chat_id)
            update_env_chat_id(chat_id_text)
            save_state(state)
            send_telegram_message("你好！意大利语学习机器人已启动。", chat_id=chat_id_text)
            send_daily_lesson(chat_id=chat_id_text)
            print("收到 /start，已发送测试推送。")
        elif text == "1" and chat_id:
            chat_id_text = str(chat_id)
            update_env_chat_id(chat_id_text)
            save_state(state)
            send_telegram_message(
                "收到，马上给你推送一组新的意大利语内容。",
                chat_id=chat_id_text,
            )
            send_daily_lesson(chat_id=chat_id_text)
            print("收到 1，已发送新的意大利语学习内容。")

    latest_state = load_state()
    if "last_update_id" in state:
        latest_state["last_update_id"] = state["last_update_id"]
    save_state(latest_state)


def main() -> None:
    load_dotenv(BASE_DIR / ".env")

    if os.getenv("SEND_ON_START", "").lower() in {"1", "true", "yes"}:
        send_daily_lesson()

    scheduler = BlockingScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_daily_lesson,
        CronTrigger(hour=9, minute=0, timezone=TIMEZONE),
        id="daily_italian_lesson",
        replace_existing=True,
    )
    scheduler.add_job(
        poll_telegram_messages,
        "interval",
        seconds=5,
        id="telegram_message_listener",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    print(f"Scheduler started. Daily push time: 09:00 ({TIMEZONE})")
    print("Send /start to your Telegram bot to receive a test push.")
    print("Send 1 to receive a new Italian lesson immediately.")
    scheduler.start()


if __name__ == "__main__":
    main()
