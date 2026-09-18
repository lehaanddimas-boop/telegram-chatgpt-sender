import os
import httpx

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

mcp = FastMCP(
    "Telegram Sender",
    stateless_http=True,
    json_response=True,
)


@mcp.tool(
    name="send_message",
    description=(
        "Отправляет готовое текстовое сообщение в рабочий Telegram-чат. "
        "Используй, когда пользователь явно просит отправить сообщение "
        "или когда запланированная сводка должна быть доставлена в рабочий чат."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=False,
    ),
)
async def send_message(text: str) -> dict:
    """Отправить сообщение в заранее настроенный рабочий Telegram-чат."""

    if not text or not text.strip():
        raise ValueError("Текст сообщения пустой")

    # Telegram ограничивает одно текстовое сообщение примерно 4096 символами.
    # Режем чуть раньше, чтобы длинная сводка тоже отправилась.
    parts = [
        text[i:i + 4000]
        for i in range(0, len(text), 4000)
    ]

    sent = []

    async with httpx.AsyncClient(timeout=30) as client:
        for part in parts:
            response = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": part,
                },
            )

            data = response.json()

            if not data.get("ok"):
                raise RuntimeError(
                    f"Telegram error: {data.get('description', 'unknown error')}"
                )

            sent.append(data["result"]["message_id"])

    return {
        "ok": True,
        "messages_sent": len(sent),
        "message_ids": sent,
    }


app = mcp.streamable_http_app()
