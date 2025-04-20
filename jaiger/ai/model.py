from abc import ABC, abstractmethod
import json
from typing import List
from jaiger.models import Call, CallResult, ToolCall

from jaiger.models import PromptResult
from jaiger.tool_manager import ToolInfo
from jaiger.utils import get_type_schema


class Model(ABC):
    def __init__(self) -> None:
        preamble = f'''
        You are a helpful AI assistant who is capable of the following:
        * Responding to prompts ONLY with a JSON object with this type schema: {get_type_schema(PromptResult)}.
        * Breaking down user queries step-by-step and think carefully about how to respond.
        * Decide whether or not tool call(s) should be made.
          Tools will be made available for you to call if you want to execute actions or obtain further information to answer user query.
          The description of available tools may be provided in future prompts.
          When a new tool description is provided, you will remember it so you can use it for future queries if necessary.
        * If no tool needs to be called, you will speak directly to user.
        * If you are speaking directly to the user, you will put your speech content inside the 'text' property and set the 'calls' property to null.
        * If you are performing tool call(s), you will set the 'calls' property to an array of 'ToolCall' objects and set the 'text' property to null.
          Each 'ToolCall' object has this schema: {get_type_schema(ToolCall)}.
          If the call is successful, the output of the tool call can be found in 'result' property and 'error' will be null.
          If the call is unsuccessful, 'error' will contain the error message and 'result' will be null.
        * After performing tool call(s), you will expect the next immediate prompt to be the result(s) of the call(s).
          Each result will be presented as 'CallResult' object of the following schema: {get_type_schema(CallResult)}.
          Upon receiving the 'CallResult' objects you may then proceed to either make further tool call(s) (and expecting further 'CallResult' object(s)) or speak directly to the user.
        '''
        self.prompt(preamble)

    @abstractmethod
    def prompt(self, text: str) -> PromptResult:
        pass

    def register_tools(self, tools: List[ToolInfo]):
        tools_schema = [info.model_dump() for info in tools]
        self.prompt(f'These tools are now available:\n{json.dumps(tools_schema)}')
