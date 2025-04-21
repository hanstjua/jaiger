from google.genai import Client

from jaiger.ai.model import Model
from jaiger.configs import AiConfig
from jaiger.models import PromptResult


class GoogleModel(Model):
    def __init__(self, config: AiConfig):
        self._model = config.model
        self._api_key = config.api_key

        self._client = Client(api_key=self._api_key)
        self._chat = self._client.chats.create(model=self._model)

        super().__init__()

    def prompt(self, text: str) -> PromptResult:
        response = self._chat.send_message(
            text, config={"response_mime_type": "application/json"}
        )

        return PromptResult.model_validate_json(response.text)
