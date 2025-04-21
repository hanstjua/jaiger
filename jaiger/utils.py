import importlib
import re
from typing import Any, Dict, Literal, Type, Union, get_origin

from pydantic import BaseModel

from jaiger.tool import Tool


def get_tool_class(type: str) -> Type[Tool]:
    match = re.search("(.+)\.(.+)", type)
    if match is None:
        raise ValueError(f'Invalid tool type "{type}".')

    module_name = match.group(1)
    tool_class = match.group(2)

    mod = importlib.import_module(module_name)
    return getattr(mod, tool_class)


def _dispatch(t: type) -> Union[str, dict]:
    origin = get_origin(t)
    if origin is Union:
        return " | ".join((_dispatch(type) for type in t.__args__))
    elif origin is Literal:
        return " | ".join((_dispatch(value) for value in t.__args__))
    elif origin is list:
        return f"List[{_dispatch(t.__args__[0])}]"
    elif origin is dict:
        return f"Dict[{_dispatch(t.__args__[0])}, {_dispatch(t.__args__[1])}]"
    elif origin is None:
        if t is Any:
            return str(t)
        if issubclass(t, BaseModel):
            return get_type_schema(t)
        else:
            return t.__name__


def get_type_schema(model: Type[BaseModel]) -> Dict[str, Union[str, dict]]:
    return {name: _dispatch(type_) for name, type_ in model.__annotations__.items()}
