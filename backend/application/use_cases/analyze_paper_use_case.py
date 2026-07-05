from schemas.paper import AnalysisPaperCreate, PaperResponse


class AnalyzePaperUseCase:
    def execute(self, data: AnalysisPaperCreate) -> PaperResponse:
        raise NotImplementedError
