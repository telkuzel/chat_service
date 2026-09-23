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

    def ask(self, prompt: str) -> str:

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

    def ask_json(self, prompt: str) -> dict:

        content = self.ask(prompt)

        content = content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        return json.loads(content)