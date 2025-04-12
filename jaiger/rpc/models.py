from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RpcRequest(BaseModel):
    function: str
    args: Optional[List[Any]] = list()
    kwargs: Optional[Dict[str, Any]] = dict()

class RpcResponse(BaseModel):
    result: Any
    error: str
    