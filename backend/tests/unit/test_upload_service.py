import pytest
from app.services.upload_service import parse_contacts_file


def test_parse_csv_basic():
    csv_content = b"name,email,company,title\nJohn Doe,john@example.com,Google,Recruiter\nJane Smith,jane@example.com,Amazon,HRBP"
    contacts, cols, errors = parse_contacts_file(csv_content, "test.csv")
    assert len(contacts) == 2
    assert contacts[0]["name"] == "John Doe"
    assert contacts[0]["email"] == "john@example.com"
    assert contacts[0]["company"] == "Google"
    assert len(errors) == 0


def test_parse_csv_missing_email():
    csv_content = b"name,email\nJohn Doe,\nJane Smith,jane@example.com"
    contacts, cols, errors = parse_contacts_file(csv_content, "test.csv")
    assert len(contacts) == 1
    assert len(errors) == 1
    assert "jane@example.com" in contacts[0]["email"]


def test_parse_csv_invalid_email():
    csv_content = b"name,email\nJohn Doe,notanemail"
    contacts, cols, errors = parse_contacts_file(csv_content, "test.csv")
    assert len(contacts) == 0
    assert len(errors) == 1


def test_parse_csv_custom_columns():
    csv_content = b"name,email,company,title,location,team\nJohn,john@example.com,Google,HR,NYC,Engineering"
    contacts, cols, errors = parse_contacts_file(csv_content, "test.csv")
    assert len(contacts) == 1
    assert "location" in contacts[0]["extra_data"]
    assert contacts[0]["extra_data"]["location"] == "NYC"
    assert "team" in contacts[0]["extra_data"]


def test_parse_unsupported_format():
    with pytest.raises(ValueError, match="Unsupported file format"):
        parse_contacts_file(b"data", "test.txt")


def test_parse_missing_required_columns():
    csv_content = b"company,title\nGoogle,Recruiter"
    with pytest.raises(ValueError, match="Missing required columns"):
        parse_contacts_file(csv_content, "test.csv")
