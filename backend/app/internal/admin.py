"""
Admin CRUD routes for grammar points, vocab items, and prompts.
All endpoints require is_admin=True on the authenticated user.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.dependencies import get_admin_user, get_db
from app.schemas import GrammarPointIn, PromptIn, VocabItemIn
from app.services import admin_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])


@router.get("/grammar-points")
def list_grammar_points(db_session: Session = Depends(get_db)):
    return admin_service.admin_list_grammar_points(db_session)


@router.get("/grammar-points/{grammar_point_id}")
def get_grammar_point(grammar_point_id: int, db_session: Session = Depends(get_db)):
    try:
        return admin_service.admin_get_grammar_point(db_session, grammar_point_id)
    except ServiceError as err:
        raise_http(err)


@router.post("/grammar-points", status_code=201)
def create_grammar_point(payload: GrammarPointIn, db_session: Session = Depends(get_db)):
    try:
        return admin_service.admin_create_grammar_point(db_session, payload)
    except ServiceError as err:
        raise_http(err)


@router.put("/grammar-points/{grammar_point_id}")
def update_grammar_point(
    grammar_point_id: int, payload: GrammarPointIn, db_session: Session = Depends(get_db)
):
    try:
        return admin_service.admin_update_grammar_point(db_session, grammar_point_id, payload)
    except ServiceError as err:
        raise_http(err)


@router.delete("/grammar-points/{grammar_point_id}", status_code=204)
def delete_grammar_point(grammar_point_id: int, db_session: Session = Depends(get_db)):
    try:
        admin_service.admin_delete_grammar_point(db_session, grammar_point_id)
    except ServiceError as err:
        raise_http(err)
    return Response(status_code=204)


@router.get("/vocab-items")
def list_vocab_items(db_session: Session = Depends(get_db)):
    return admin_service.admin_list_vocab_items(db_session)


@router.get("/vocab-items/{vocab_item_id}")
def get_vocab_item(vocab_item_id: int, db_session: Session = Depends(get_db)):
    try:
        return admin_service.admin_get_vocab_item(db_session, vocab_item_id)
    except ServiceError as err:
        raise_http(err)


@router.post("/vocab-items", status_code=201)
def create_vocab_item(payload: VocabItemIn, db_session: Session = Depends(get_db)):
    return admin_service.admin_create_vocab_item(db_session, payload)


@router.put("/vocab-items/{vocab_item_id}")
def update_vocab_item(
    vocab_item_id: int, payload: VocabItemIn, db_session: Session = Depends(get_db)
):
    try:
        return admin_service.admin_update_vocab_item(db_session, vocab_item_id, payload)
    except ServiceError as err:
        raise_http(err)


@router.delete("/vocab-items/{vocab_item_id}", status_code=204)
def delete_vocab_item(vocab_item_id: int, db_session: Session = Depends(get_db)):
    try:
        admin_service.admin_delete_vocab_item(db_session, vocab_item_id)
    except ServiceError as err:
        raise_http(err)
    return Response(status_code=204)


@router.get("/prompts")
def list_prompts(kind: str | None = None, db_session: Session = Depends(get_db)):
    return admin_service.admin_list_prompts(db_session, kind)


@router.get("/prompts/{prompt_id}")
def get_prompt(prompt_id: int, db_session: Session = Depends(get_db)):
    try:
        return admin_service.admin_get_prompt(db_session, prompt_id)
    except ServiceError as err:
        raise_http(err)


@router.post("/prompts", status_code=201)
def create_prompt(payload: PromptIn, db_session: Session = Depends(get_db)):
    try:
        return admin_service.admin_create_prompt(db_session, payload)
    except ServiceError as err:
        raise_http(err)


@router.put("/prompts/{prompt_id}")
def update_prompt(prompt_id: int, payload: PromptIn, db_session: Session = Depends(get_db)):
    try:
        return admin_service.admin_update_prompt(db_session, prompt_id, payload)
    except ServiceError as err:
        raise_http(err)


@router.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: int, db_session: Session = Depends(get_db)):
    try:
        admin_service.admin_delete_prompt(db_session, prompt_id)
    except ServiceError as err:
        raise_http(err)
    return Response(status_code=204)
