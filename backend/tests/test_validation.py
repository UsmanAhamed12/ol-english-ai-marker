"""Request validation: the API must refuse bad input before it reaches the pipeline."""

import pytest
from pydantic import ValidationError

from app.schemas import KnowledgeIn, RegisterIn


def test_a_valid_registration_is_normalised():
    model = RegisterIn(email="  Teacher@School.LK ", password="Passw0rd1", full_name="Teacher")
    assert model.email == "teacher@school.lk"


def test_a_short_password_is_refused():
    with pytest.raises(ValidationError):
        RegisterIn(email="a@b.lk", password="short1")


def test_a_password_without_a_digit_is_refused():
    with pytest.raises(ValidationError):
        RegisterIn(email="a@b.lk", password="onlyletters")


def test_a_password_without_a_letter_is_refused():
    with pytest.raises(ValidationError):
        RegisterIn(email="a@b.lk", password="12345678")


def test_an_invalid_email_is_refused():
    with pytest.raises(ValidationError):
        RegisterIn(email="not-an-email", password="Passw0rd1")


def test_a_title_longer_than_the_schema_allows_is_refused():
    with pytest.raises(ValidationError):
        KnowledgeIn(title="x" * 201, kind="Syllabus", content="y" * 50)


def test_a_knowledge_source_must_declare_a_known_kind():
    with pytest.raises(ValidationError):
        KnowledgeIn(title="Syllabus 2024", kind="Spreadsheet", content="y" * 50)


def test_a_valid_knowledge_source_is_accepted():
    model = KnowledgeIn(title="Syllabus 2024", kind="Syllabus", content="Reading comprehension objectives")
    assert model.kind == "Syllabus"