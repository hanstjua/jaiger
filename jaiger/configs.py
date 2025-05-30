from typing import List, Literal, Optional

from pydantic import BaseModel


class RpcConfig(BaseModel):
    host: str
    port: int
    timeout: int = 10


class HttpConfig(BaseModel):
    host: str
    port: int
    timeout: int = 10


class ServerConfig(BaseModel):
    http: Optional[HttpConfig] = None
    rpc: Optional[RpcConfig] = None


class Settings(BaseModel):
    server: Optional[ServerConfig] = None


class ToolConfig(BaseModel):
    name: str
    type: str
    config: Optional[dict] = None


class AiConfig(BaseModel):
    name: str
    model: str
    type: Literal["openai", "google", "anthropic", "ollama"]
    api_key: str


class MainConfig(BaseModel):
    settings: Optional[Settings] = None
    tools: List[ToolConfig]
    ais: List[AiConfig]
