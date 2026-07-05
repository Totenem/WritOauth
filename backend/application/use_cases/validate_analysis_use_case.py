from schemas.analysis import FeedbackCreate, FeedbackResponse


class ValidateAnalysisUseCase:
    def execute(self, analysis_id: int, data: FeedbackCreate) -> FeedbackResponse:
        raise NotImplementedError
