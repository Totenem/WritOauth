from schemas.paper import BaselinePaperCreate, PaperResponse


class UploadBaselineUseCase:
    def execute(self, data: BaselinePaperCreate) -> PaperResponse:
        raise NotImplementedError
