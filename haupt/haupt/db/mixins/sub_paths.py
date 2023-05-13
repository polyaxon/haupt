class SubPathMixin:
    @property
    def subpath(self) -> str:
        raise NotImplementedError
