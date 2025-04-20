from multiprocessing import Event
from multiprocessing.connection import Connection
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
from jaiger.configs import ToolConfig

from jaiger.tool import Tool


class Call(BaseModel):
    function: str
    args: List[Any] = list()
    kwargs: Dict[str, Any] = dict()

class CallResult(BaseModel):
    result: Any = None
    error: Optional[str] = None

class ToolCall(BaseModel):
    tool: str
    function: str
    args: List[Any] = list()
    kwargs: Dict[str, Any] = dict()

class PromptResult(BaseModel):
    text: Optional[str] = None
    calls: Optional[List[ToolCall]] = None
