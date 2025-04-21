from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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
