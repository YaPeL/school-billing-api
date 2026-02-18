from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.dal.repos.sqlalchemy_invoice_repo import SQLAlchemyInvoiceRepo
from app.dal.repos.sqlalchemy_payment_repo import SQLAlchemyPaymentRepo
from app.dal.repos.sqlalchemy_school_repo import SQLAlchemySchoolRepo
from app.dal.repos.sqlalchemy_student_repo import SQLAlchemyStudentRepo
from app.db.session import get_db
from app.schemas.auth import UserClaims
from app.services.ports import InvoiceRepo, PaymentRepo, SchoolRepo, StudentRepo
from app.services.use_cases import GetSchoolStatement, GetStudentStatement, ListInvoicePayments

bearer_scheme = HTTPBearer(auto_error=False)


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserClaims:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_error()

    try:
        return decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise _auth_error() from exc


async def require_admin(current_user: Annotated[UserClaims, Depends(get_current_user)]) -> UserClaims:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_school_repo(session: Annotated[Session, Depends(get_db)]) -> SchoolRepo:
    return SQLAlchemySchoolRepo(session)


async def get_student_repo(session: Annotated[Session, Depends(get_db)]) -> StudentRepo:
    return SQLAlchemyStudentRepo(session)


async def get_invoice_repo(session: Annotated[Session, Depends(get_db)]) -> InvoiceRepo:
    return SQLAlchemyInvoiceRepo(session)


async def get_payment_repo(session: Annotated[Session, Depends(get_db)]) -> PaymentRepo:
    return SQLAlchemyPaymentRepo(session)


async def get_student_statement_uc(
    student_repo: Annotated[StudentRepo, Depends(get_student_repo)],
    invoice_repo: Annotated[InvoiceRepo, Depends(get_invoice_repo)],
    payment_repo: Annotated[PaymentRepo, Depends(get_payment_repo)],
) -> GetStudentStatement:
    return GetStudentStatement(student_repo=student_repo, invoice_repo=invoice_repo, payment_repo=payment_repo)


async def get_school_statement_uc(
    school_repo: Annotated[SchoolRepo, Depends(get_school_repo)],
    student_repo: Annotated[StudentRepo, Depends(get_student_repo)],
    invoice_repo: Annotated[InvoiceRepo, Depends(get_invoice_repo)],
    payment_repo: Annotated[PaymentRepo, Depends(get_payment_repo)],
) -> GetSchoolStatement:
    return GetSchoolStatement(
        school_repo=school_repo,
        student_repo=student_repo,
        invoice_repo=invoice_repo,
        payment_repo=payment_repo,
    )


async def get_list_invoice_payments_uc(
    invoice_repo: Annotated[InvoiceRepo, Depends(get_invoice_repo)],
    payment_repo: Annotated[PaymentRepo, Depends(get_payment_repo)],
) -> ListInvoicePayments:
    return ListInvoicePayments(invoice_repo=invoice_repo, payment_repo=payment_repo)
