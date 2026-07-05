class QwenClient:
    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url

    def infer(self, prompt: str) -> str:
        raise NotImplementedError
