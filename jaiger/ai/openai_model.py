import os
from typing import Optional

from openai import OpenAI
from openai.types.responses import Response
from jaiger.ai.model import Model
from jaiger.configs import AiConfig
from jaiger.models import PromptResult


class OpenAIModel(Model):
    def __init__(self, config: AiConfig) -> None:
        self._model = config.model
        self._api_key = config.api_key

        os.environ['OPENAI_API_KEY'] = self._api_key

        self._client = OpenAI()
        self._last_response: Optional[Response] = None

        super().__init__()

    def prompt(self, text: str) -> PromptResult:
        if self._last_response is None:
            self._last_response = self._client.responses.create(
                model=self._model,
                input=text
            )
        else:
            self._last_response = self._client.responses.create(
                model=self._model,
                previous_response_id=self._last_response.id,
                input=[{'role': 'user', 'content': text}]
            )

        return PromptResult.model_validate_json(self._last_response.output_text)
