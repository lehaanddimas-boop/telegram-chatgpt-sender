import os
import httpx

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings


BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


mcp = MCPServer("Telegram Sender")


@mcp.tool(
    name="send_message",
    description="Отправляет готовое текстовое сообщение в рабочий Telegram-чат."
)
async def send_message(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("Текст сообщения пустой")

    # Telegram ограничивает одно сообщение примерно 4096 символами.
    # Поэтому длинные сводки делим на части.
    parts = [
        text[i:i + 4000]
        for i in range(0, len(text), 4000)
    ]

    sent_message_ids = []

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

            sent_message_ids.append(
                data["result"]["message_id"]
            )

    return {
        "ok": True,
        "messages_sent": len(sent_message_ids),
        "message_ids": sent_message_ids,
    }


security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False
)


app = mcp.streamable_http_app(
    stateless_http=True,
    json_response=True,
    transport_security=security,
    host="0.0.0.0",
)
