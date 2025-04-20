import traceback
from typing import Any, Dict, List
import httpx
from jaiger.configs import HttpConfig
from jaiger.models import Call, CallResult


class HttpClient:
    def __init__(self, config: HttpConfig) -> None:
        self._host = config.host
        self._port = config.port

    def call(
        self,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
        timeout: int = 10,
    ) -> CallResult:
        try:
            response = httpx.post(
                f'http://{self._host}:{self._port}/call',
                timeout=timeout,
                json=Call(
                    function=function,
                    args=args,
                    kwargs=kwargs
                ).model_dump()
            )

            return CallResult.model_validate(response.json())
        
        except Exception as e:
            raise RuntimeError(f'Call failed:\n'
                               f'{"".join(traceback.TracebackException.from_exception(e).format())}')
