class ProfileEngine:
    def update_profile(self, student_id: int, paper_content: str) -> None:
        raise NotImplementedError

    def get_profile(self, student_id: int) -> dict:
        raise NotImplementedError
