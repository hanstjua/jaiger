import traceback
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Dict, List

from jaiger.ai.anthropic_model import AnthropicModel
from jaiger.ai.google_model import GoogleModel
from jaiger.ai.model import Model
from jaiger.ai.ollama_model import OllamaModel
from jaiger.ai.openai_model import OpenAIModel
from jaiger.configs import AiConfig
from jaiger.models import PromptResult
from jaiger.tool.tool_manager import ToolInfo


class AiManager:
    def __init__(self) -> None:
        self._ais: Dict[str, Model] = {}

        self._pool = ThreadPoolExecutor()

        self._logger = getLogger("jaiger")

    def ais(self) -> List[str]:
        return [name for name in self._ais]

    def add_ai(self, config: AiConfig) -> "AiManager":
        if config.name in self._ais:
            raise ValueError(f'AI "{config.name}" already exists.')

        if config.type == "google":
            model = GoogleModel(config)
        elif config.type == "anthropic":
            model = AnthropicModel(config)
        elif config.type == "openai":
            model = OpenAIModel(config)
        elif config.type == "ollama":
            model = OllamaModel(config)
        else:
            raise ValueError(f"Unsupported AI type {config.type}.")

        self._ais[config.name] = model

        return self

    def prompt(self, name: str, text: str) -> PromptResult:
        if name not in self._ais:
            raise ValueError(f'AI "{name}" does not exist.')

        return self._ais[name].prompt(text)

    def remove_ai(self, name: str) -> "AiManager":
        if name not in self._ais:
            raise ValueError(f'AI "{name}" does not exist.')

        del self._ais[name]

        return self

    def register_tools(self, tools: List[ToolInfo]) -> bool:
        futures = {
            name: self._pool.submit(ai.register_tools, tools)
            for name, ai in self._ais.items()
        }

        has_error = False
        for name, future in futures.items():
            try:
                future.result()
            except Exception as e:
                has_error = True
                message = "".join(
                    traceback.TracebackException.from_exception(e).format()
                )
                self._logger.error(f"Failed to register tools for {name}:\n{message}")

        return not has_error
