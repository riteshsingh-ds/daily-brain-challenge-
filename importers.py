
import io
import re
import pandas as pd
import streamlit as st

from database import (
    add_question,
    get_db_connection
)


# Required CSV columns
REQUIRED_COLUMNS = [
    "subject",
    "topic",
    "difficulty",
    "question",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
    "explanation"
]

VALID_DIFFICULTIES = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard"
}

VALID_ANSWERS = {"A", "B", "C", "D"}


def clean_value(value):
    """Convert a cell value into a clean string."""

    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_dataframe(df):
    """Normalize column names and values."""

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    return df


def validate_dataframe(df):
    """
    Validate uploaded question data.

    Returns:
        valid_rows
        errors
    """

    df = normalize_dataframe(df.copy())

    errors = []

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        return [], [
            "Missing columns: " + ", ".join(missing_columns)
        ]

    valid_rows = []

    for index, row in df.iterrows():

        row_number = index + 2

        data = {
            col: clean_value(row[col])
            for col in REQUIRED_COLUMNS
        }

        # Check required fields
        empty_fields = [
            col for col in REQUIRED_COLUMNS
            if col not in ["topic", "explanation"]
            and not data[col]
        ]

        if empty_fields:
            errors.append(
                f"Row {row_number}: Empty fields - "
                + ", ".join(empty_fields)
            )
            continue

        # Validate difficulty
        difficulty = data["difficulty"].lower()

        if difficulty not in VALID_DIFFICULTIES:
            errors.append(
                f"Row {row_number}: Invalid difficulty."
            )
            continue

        data["difficulty"] = VALID_DIFFICULTIES[difficulty]

        # Validate correct answer
        correct = data["correct_option"].upper()

        if correct not in VALID_ANSWERS:
            errors.append(
                f"Row {row_number}: Correct answer must be A, B, C or D."
            )
            continue

        data["correct_option"] = correct

        # Check duplicate option text
        options = [
            data["option_a"],
            data["option_b"],
            data["option_c"],
            data["option_d"]
        ]

        if len(set(options)) != 4:
            errors.append(
                f"Row {row_number}: Answer options must be unique."
            )
            continue

        valid_rows.append(data)

    return valid_rows, errors


def find_existing_questions(rows):
    """Find questions already present in the database."""

    conn = get_db_connection()

    try:
        existing = {
            (
                row["subject"].strip().lower(),
                row["question"].strip().lower()
            )
            for row in conn.execute("""
                SELECT subject, question
                FROM questions
            """).fetchall()
        }

    finally:
        conn.close()

    new_rows = []
    duplicates = []

    for row in rows:

        key = (
            row["subject"].strip().lower(),
            row["question"].strip().lower()
        )

        if key in existing:
            duplicates.append(row["question"])
        else:
            new_rows.append(row)
            existing.add(key)

    return new_rows, duplicates


def import_question_rows(rows, admin_id):
    """Save validated questions into SQLite."""

    imported = 0
    failed = 0

    for row in rows:

        try:
            row["source"] = "Bulk Import"

            add_question(
                row,
                created_by=admin_id
            )

            imported += 1

        except Exception:
            failed += 1

    return imported, failed


def read_csv_file(uploaded_file):
    """Read uploaded CSV safely."""

    try:
        content = uploaded_file.getvalue()

        try:
            return pd.read_csv(
                io.BytesIO(content),
                encoding="utf-8-sig"
            )

        except UnicodeDecodeError:
            return pd.read_csv(
                io.BytesIO(content),
                encoding="latin-1"
            )

    except Exception as error:
        raise ValueError(
            f"Unable to read CSV file: {error}"
        )


def validate_google_sheet_url(url):
    """Convert a Google Sheets URL into a CSV export URL."""

    match = re.search(
        r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
        url
    )

    if not match:
        raise ValueError("Invalid Google Sheets URL.")

    sheet_id = match.group(1)

    gid_match = re.search(r"[?&]gid=(\d+)", url)

    gid = gid_match.group(1) if gid_match else "0"

    return (
        "https://docs.google.com/spreadsheets/d/"
        f"{sheet_id}/export?format=csv&gid={gid}"
    )


def read_google_sheet_csv(url):
    """
    Read a publicly accessible Google Sheet.

    The sheet must have viewer access enabled.
    """

    csv_url = validate_google_sheet_url(url)

    try:
        return pd.read_csv(csv_url)

    except Exception as error:
        raise ValueError(
            "Unable to read Google Sheet. "
            "Check its sharing permissions and URL. "
            f"Details: {error}"
        )


def process_import(df, admin_id):
    """Validate, deduplicate and import questions."""

    valid_rows, errors = validate_dataframe(df)

    new_rows, duplicates = find_existing_questions(
        valid_rows
    )

    imported, failed = import_question_rows(
        new_rows,
        admin_id
    )

    return {
        "total_rows": len(df),
        "valid_rows": len(valid_rows),
        "duplicates": len(duplicates),
        "imported": imported,
        "failed": failed,
        "errors": errors,
        "duplicate_questions": duplicates
    }


def render_importer():
    """Display the admin import interface."""

    st.subheader("📤 Import Questions")

    admin_id = st.session_state["user_id"]

    tab1, tab2 = st.tabs([
        "CSV Upload",
        "Google Sheets"
    ])

    with tab1:

        uploaded_file = st.file_uploader(
            "Upload question CSV",
            type=["csv"],
            key="question_csv"
        )

        if uploaded_file:

            try:
                df = read_csv_file(uploaded_file)

                st.write("### Preview")
                st.dataframe(
                    df.head(10),
                    use_container_width=True
                )

                valid_rows, errors = validate_dataframe(df)

                st.write(
                    f"Valid rows: {len(valid_rows)}"
                )

                if errors:
                    with st.expander(
                        f"Validation errors ({len(errors)})"
                    ):
                        for error in errors[:50]:
                            st.error(error)

                if st.button(
                    "Import CSV Questions",
                    use_container_width=True,
                    disabled=len(valid_rows) == 0
                ):

                    result = process_import(
                        df,
                        admin_id
                    )

                    st.success(
                        f"Imported: {result['imported']}"
                    )

                    st.info(
                        f"Duplicates: {result['duplicates']} | "
                        f"Failed: {result['failed']}"
                    )

            except Exception as error:
                st.error(str(error))

    with tab2:

        st.info(
            "For this option, your Google Sheet must be "
            "shared with 'Anyone with the link – Viewer'. "
            "Do not use private or confidential sheets."
        )

        sheet_url = st.text_input(
            "Google Sheets URL",
            placeholder="Paste your Google Sheets link"
        )

        if st.button(
            "Load Google Sheet",
            use_container_width=True
        ):

            if not sheet_url.strip():
                st.warning("Please enter a Google Sheets URL.")

            else:
                try:
                    df = read_google_sheet_csv(
                        sheet_url.strip()
                    )

                    st.session_state["sheet_preview"] = df

                    st.success("Google Sheet loaded!")
                    st.dataframe(
                        df.head(10),
                        use_container_width=True
                    )

                except Exception as error:
                    st.error(str(error))

        if "sheet_preview" in st.session_state:

            if st.button(
                "Import Google Sheet Questions",
                use_container_width=True
            ):

                result = process_import(
                    st.session_state["sheet_preview"],
                    admin_id
                )

                st.success(
                    f"Imported: {result['imported']}"
                )

                st.info(
                    f"Duplicates: {result['duplicates']} | "
                    f"Failed: {result['failed']}"
                )

                del st.session_state["sheet_preview"]
