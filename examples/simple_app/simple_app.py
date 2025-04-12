from jaiger import Jaiger


class SimpleApp:
    def __init__(self, config: str) -> None:
        self._jaiger = Jaiger(config)

if __name__ == '__main__':
    app = SimpleApp('simple_app.json')
