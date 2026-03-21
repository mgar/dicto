"""Raised by service layer; routers translate to HTTPException."""

from fastapi import HTTPException


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def raise_http(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error
