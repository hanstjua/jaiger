from jaiger.main import Jaiger


class SimpleApp:
    def __init__(self, config: str) -> None:
        self._jaiger = Jaiger(config)

    def __enter__(self):
        self._jaiger.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._jaiger.stop()

    def on_call(self, call):
        args = [repr(arg) for arg in call.args] + [
            f"{k}={repr(v)}" for k, v in call.kwargs.items()
        ]
        print(
            f"\n\033[93m> Calling {call.tool}.{call.function}({', '.join(args)})\033[0m"
        )

    def run(self):
        print(
            "\033[93m(* Welcome to simple jAIger AI app!\n"
            "Here are a few things it can do:\n"
            "1. Execute Python code.\n"
            "2. Create, modify and delete files.\n"
            'To exit, type "/exit" *)\033[0m\n'
        )

        query = input("[You]: (Type your query below)\n")
        while query != "/exit":
            answer = self._jaiger.prompt("my_ai", query, on_call=self.on_call)
            print(f"\n\033[93m[AI]:\n{answer}\033[0m\n")
            query = input("[You]:\n")


if __name__ == "__main__":
    from pathlib import Path

    with SimpleApp(Path(__file__).parent / "simple_app.json") as app:
        app.run()
