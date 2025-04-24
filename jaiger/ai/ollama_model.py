from typing import List

from ollama import Client, Message

from jaiger.ai.model import Model
from jaiger.configs import AiConfig
from jaiger.models import PromptResult


class OllamaModel(Model):
    def __init__(self, config: AiConfig) -> None:
        self._model = config.model

        self._client = Client() if config.api_key == "" else Client(config.api_key)
        self._messages_history: List[Message] = []

        super().__init__()

    def prompt(self, text: str) -> PromptResult:
        self._messages_history.append(Message(role="user", content=text))
        response = self._client.chat(
            model=self._model, messages=self._messages_history, format="json"
        )
        self._messages_history.append(response.message)

        return PromptResult.model_validate_json(response.message.content)
