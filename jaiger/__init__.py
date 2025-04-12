import json
from logging.config import dictConfig
from pathlib import Path

from jaiger.configs import MainConfig


class Jaiger:
    def __init__(self, config: str) -> None:
        self._config_path = config
        
        # load config
        p = Path(config)
        if not p.is_file():
            raise FileNotFoundError(f'Failed to load config: {config}')
        
        self._config = MainConfig.model_validate(json.loads(p.read_text()))

        # configure logger
        dictConfig({
            'version': 1,
            'formatters': {
                'default': {
                    'format': '%(asctime)s %(levelname)s [%(name)s] %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'level': 'DEBUG'
                }
            },
            'loggers': {
                'jaiger': {
                    'level': 'INFO',
                    'handlers': ['console']
                }
            }
        })

        if self._config.settings.server.rpc:
            pass

        if self._config.settings.server.http:
            pass

    @property
    def config(self) -> dict:
        return self._config
