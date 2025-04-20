from typing import List

from anthropic import Anthropic
from anthropic.types.message import Message
from jaiger.ai.model import Model
from jaiger.configs import AiConfig
from jaiger.models import PromptResult


class AnthropicModel(Model):
    def __init__(self, config: AiConfig):
        self._model = config.model
        self._api_key = config.api_key

        self._client = Anthropic(api_key=self._api_key)
        self._messages_history: List[Message] = []

        super().__init__()

    def prompt(self, text: str) -> PromptResult:
        self._messages_history += [{"role": "user", "content": text}]
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=self._messages_history
        )

        return PromptResult.model_validate_json(response)
    