import pandas as pd
import io
from typing import BinaryIO, Dict, List, Any, Tuple
from loguru import logger


REQUIRED_COLUMNS = {"name", "email"}
STANDARD_COLUMNS = {"name", "email", "company", "title"}


def parse_contacts_file(
    file_content: bytes,
    filename: str,
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Parse an Excel or CSV file and return contacts, column names, and errors.

    Returns:
        (contacts, all_columns, errors)
    """
    errors: List[str] = []
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    except Exception as e:
        raise ValueError(f"Failed to parse file: {e}")

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Check required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}. File must have: name, email")

    all_columns = list(df.columns)
    custom_columns = [col for col in all_columns if col not in STANDARD_COLUMNS]

    contacts: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed + header row

        name = str(row.get("name", "")).strip()
        email = str(row.get("email", "")).strip()

        if not name or name.lower() in ("nan", "none", ""):
            errors.append(f"Row {row_num}: Missing name, skipped")
            continue

        if not email or email.lower() in ("nan", "none", ""):
            errors.append(f"Row {row_num}: Missing email for {name}, skipped")
            continue

        # Basic email validation
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append(f"Row {row_num}: Invalid email '{email}' for {name}, skipped")
            continue

        company = str(row.get("company", "")).strip() if "company" in df.columns else ""
        if company.lower() in ("nan", "none"):
            company = ""

        title = str(row.get("title", "")).strip() if "title" in df.columns else ""
        if title.lower() in ("nan", "none"):
            title = ""

        # Collect custom column values
        extra_data: Dict[str, Any] = {}
        for col in custom_columns:
            val = row.get(col)
            if pd.notna(val):
                extra_data[col] = str(val).strip()

        contacts.append({
            "name": name,
            "email": email.lower(),
            "company": company or None,
            "title": title or None,
            "extra_data": extra_data,
        })

    logger.info(
        f"Parsed {len(contacts)} valid contacts from {filename} "
        f"({len(errors)} skipped, {len(custom_columns)} custom columns)"
    )
    return contacts, all_columns, errors
