class PromptBuilder:
    def build(
        self,
        fingerprint: dict,
        retrieved_samples: list[str],
        submitted_paper: str,
    ) -> str:
        raise NotImplementedError
