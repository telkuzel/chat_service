import json

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole


class GigaChatClient:

    def __init__(
        self,
        credentials: str,
        scope: str,
        model: str,
        verify_ssl_certs: bool = False,
        temperature: float = 0.7,
    ):
        self.client = GigaChat(
            credentials=credentials,
            scope=scope,
            model=model,
            verify_ssl_certs=verify_ssl_certs,
            temperature=temperature,
        )

    def ask(
        self,
        prompt: str,
    ) -> str:

        response = self.client.chat(
            Chat(
                messages=[
                    Messages(
                        role=MessagesRole.SYSTEM,
                        content=prompt,
                    )
                ]
            )
        )

        return response.choices[0].message.content

    def ask_json(
        self,
        prompt: str,
    ) -> dict:

        content = self.ask(prompt).strip()

        # Убираем markdown code fence
        if content.startswith("```"):
            lines = content.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        # На случай, если модель добавила текст
        # перед JSON.
        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                f"GigaChat не вернул JSON:\n{content}"
            )

        content = content[start:end + 1]

        try:
            return json.loads(content)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Некорректный JSON от GigaChat:\n{content}"
            ) from exc