from abc import ABC
import inspect
from typing import List, Optional
from docstring_parser import parse

from pydantic import BaseModel
from jaiger.configs import ToolConfig


class ToolParam(BaseModel):
    name: str
    type: str
    description: str
    optional: bool

class ToolReturns(BaseModel):
    type: str
    description: str

class ToolRaise(BaseModel):
    type: str
    description: str

class ToolSpec(BaseModel):
    name: str
    description: str
    params: List[ToolParam]
    returns: Optional[ToolReturns] = None
    raises: List[ToolRaise]


class Tool(ABC):
    def __init__(self, config: Optional[ToolConfig]) -> None:
        self._config = config

        self._specs = self._get_specs()

    def config(self) -> Optional[ToolConfig]:
        return self._config
    
    def specs(self) -> List[ToolSpec]:
        return self._specs
    
    def setup(self):
        pass

    def teardown(self):
        pass

    def _get_specs(self) -> List[ToolSpec]:
        base_methods = [
            self.config.__name__,
            self.specs.__name__,
            self.setup.__name__,
            self.teardown.__name__
        ]

        def is_public_method_of_child_class(member):
            return (
                (inspect.ismethod(member) or inspect.isfunction(member)) and
                member.__name__ not in base_methods and
                not member.__name__.startswith('_')
            )
        
        docstrings = (
            (name, parse(member.__doc__))
            for name, member in inspect.getmembers(
                self,
                predicate=is_public_method_of_child_class
            )
        )

        return [
            ToolSpec(
                name=name,
                description=self.__doc__,
                params=[
                    ToolParam(
                        name=param.arg_name,
                        type=param.type_name,
                        description=param.description,
                        optional=param.is_optional
                    )
                    for param in docstring.params
                ],
                returns=ToolReturns(
                    type=docstring.returns.type_name,
                    description=docstring.returns.description
                ) if docstring.returns else None,
                raises=[
                    ToolRaise(
                        type=raise_.type_name,
                        description=raise_.description
                    )
                    for raise_ in docstring.raises
                ]
            )
            for name, docstring in docstrings
        ]
