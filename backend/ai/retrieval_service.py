class RetrievalService:
    def retrieve(
        self, embedding: list[float], student_id: int, top_k: int
    ) -> list[str]:
        raise NotImplementedError
