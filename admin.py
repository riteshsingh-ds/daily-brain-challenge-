
import streamlit as st
import pandas as pd
import json
from io import BytesIO

from auth import require_admin
from database import (
    add_question,
    get_db_connection,
    get_questions,
    get_subjects,
    get_admin_statistics,
    deactivate_question
)
from questions import SUBJECTS, DIFFICULTIES


def admin_header():
    st.title("🛡️ Admin Control Center")
    st.caption("Manage questions, subjects and learning content.")


def question_form():
    st.subheader("➕ Add New Question")

    subject_options = sorted({
        topic
        for topics in SUBJECTS.values()
        for topic in topics
    })

    with st.form("add_question_form", clear_on_submit=True):

        subject = st.selectbox(
            "Select Subject",
            subject_options
        )

        topic = st.text_input(
            "Topic",
            placeholder="Example: Python Loops"
        )

        difficulty = st.selectbox(
            "Difficulty",
            DIFFICULTIES
        )

        question = st.text_area(
            "Question",
            placeholder="Enter your MCQ question..."
        )

        st.markdown("**Answer Options**")

        col1, col2 = st.columns(2)

        with col1:
            option_a = st.text_input("Option A")
            option_b = st.text_input("Option B")

        with col2:
            option_c = st.text_input("Option C")
            option_d = st.text_input("Option D")

        correct_option = st.selectbox(
            "Correct Answer",
            ["A", "B", "C", "D"]
        )

        explanation = st.text_area(
            "Explanation",
            placeholder="Explain why this answer is correct..."
        )

        submitted = st.form_submit_button(
            "Save Question",
            use_container_width=True
        )

        if submitted:

            required_fields = [
                subject,
                question,
                option_a,
                option_b,
                option_c,
                option_d
            ]

            if not all(value.strip() for value in required_fields):
                st.error("Please complete all required fields.")

            else:
                data = {
                    "subject": subject,
                    "topic": topic,
                    "difficulty": difficulty,
                    "question": question.strip(),
                    "option_a": option_a.strip(),
                    "option_b": option_b.strip(),
                    "option_c": option_c.strip(),
                    "option_d": option_d.strip(),
                    "correct_option": correct_option,
                    "explanation": explanation.strip(),
                    "source": "Admin"
                }

                try:
                    question_id = add_question(
                        data,
                        created_by=st.session_state["user_id"]
                    )

                    st.success(
                        f"Question saved successfully! ID: {question_id}"
                    )

                except Exception as error:
                    st.error(f"Unable to save question: {error}")


def question_manager():
    st.subheader("📚 Question Bank Manager")

    subjects = ["All"] + get_subjects()
    difficulties = ["All"] + DIFFICULTIES

    col1, col2 = st.columns(2)

    with col1:
        selected_subject = st.selectbox(
            "Filter by Subject",
            subjects,
            key="admin_subject_filter"
        )

    with col2:
        selected_difficulty = st.selectbox(
            "Filter by Difficulty",
            difficulties,
            key="admin_difficulty_filter"
        )

    questions = get_questions(
        subject=selected_subject,
        difficulty=selected_difficulty,
        limit=1000
    )

    if not questions:
        st.info("No questions found.")
        return

    search = st.text_input(
        "🔍 Search questions",
        placeholder="Search question text..."
    )

    if search:
        questions = [
            q for q in questions
            if search.lower() in q["question"].lower()
            or search.lower() in q["subject"].lower()
            or search.lower() in (q["topic"] or "").lower()
        ]

    st.write(f"**Total matching questions: {len(questions)}**")

    for q in questions:

        with st.expander(
            f"#{q['id']} | {q['subject']} | {q['difficulty']} | {q['question'][:65]}"
        ):

            st.write(q["question"])

            st.write(f"A. {q['option_a']}")
            st.write(f"B. {q['option_b']}")
            st.write(f"C. {q['option_c']}")
            st.write(f"D. {q['option_d']}")

            st.success(
                f"Correct Answer: {q['correct_option']}"
            )

            if q["explanation"]:
                st.caption(q["explanation"])

            if st.button(
                "Deactivate Question",
                key=f"deactivate_{q['id']}"
            ):

                deactivate_question(q["id"])

                st.success("Question deactivated.")
                st.rerun()


def _normalise_import_dataframe(df):
    """Normalize uploaded question data into the platform's CSV column format."""
    df.columns = [str(column).strip().lower() for column in df.columns]

    # Accept common alternate column names.
    aliases = {
        "answer": "correct_option",
        "correct_answer": "correct_option",
        "option a": "option_a",
        "option b": "option_b",
        "option c": "option_c",
        "option d": "option_d",
        "explanation_text": "explanation",
    }
    df = df.rename(columns={column: aliases.get(column, column) for column in df.columns})

    required = [
        "subject", "topic", "difficulty", "question",
        "option_a", "option_b", "option_c", "option_d",
        "correct_option", "explanation"
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))

    df = df[required].fillna("")
    for column in required:
        df[column] = df[column].astype(str).str.strip()
    return df


def _read_uploaded_questions(uploaded_file):
    filename = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(BytesIO(raw), encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(BytesIO(raw), encoding="latin-1")
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(BytesIO(raw))
    elif filename.endswith(".json"):
        payload = json.loads(raw.decode("utf-8-sig"))
        if isinstance(payload, dict):
            payload = payload.get("questions", [])
        if not isinstance(payload, list):
            raise ValueError("JSON must contain a list of questions or a 'questions' list.")
        df = pd.DataFrame(payload)
    else:
        raise ValueError("Unsupported file type. Upload CSV, XLSX, XLS or JSON.")

    return _normalise_import_dataframe(df)


def _validate_import_dataframe(df):
    valid_rows = []
    errors = []
    seen = set()
    allowed_difficulties = {str(item).lower() for item in DIFFICULTIES}

    for index, row in df.iterrows():
        row_number = index + 2
        item = row.to_dict()

        required_text = [
            "subject", "difficulty", "question",
            "option_a", "option_b", "option_c", "option_d"
        ]
        missing = [field for field in required_text if not item[field]]
        if missing:
            errors.append(f"Row {row_number}: missing {', '.join(missing)}")
            continue

        answer = item["correct_option"].upper()
        if answer not in {"A", "B", "C", "D"}:
            errors.append(f"Row {row_number}: correct_option must be A, B, C or D")
            continue

        if item["difficulty"].lower() not in allowed_difficulties:
            errors.append(
                f"Row {row_number}: difficulty must be one of {', '.join(DIFFICULTIES)}"
            )
            continue

        option_values = [item[f"option_{letter}"].casefold() for letter in "abcd"]
        if len(set(option_values)) != 4:
            errors.append(f"Row {row_number}: all four options must be different")
            continue

        duplicate_key = (item["subject"].casefold(), item["question"].casefold())
        if duplicate_key in seen:
            errors.append(f"Row {row_number}: duplicate question in this upload")
            continue
        seen.add(duplicate_key)

        item["correct_option"] = answer
        # Store difficulty using the platform's canonical spelling.
        item["difficulty"] = next(
            value for value in DIFFICULTIES
            if value.lower() == item["difficulty"].lower()
        )
        valid_rows.append(item)

    return valid_rows, errors


def _import_question_records(records):
    imported = 0
    skipped = 0
    user_id = st.session_state.get("user_id")

    for item in records:
        # Check existing active questions to avoid importing the same question twice.
        conn = get_db_connection()
        try:
            existing = conn.execute(
                """
                SELECT id FROM questions
                WHERE lower(subject) = lower(?)
                  AND lower(question) = lower(?)
                  AND is_active = 1
                LIMIT 1
                """,
                (item["subject"], item["question"])
            ).fetchone()
        finally:
            conn.close()

        if existing:
            skipped += 1
            continue

        data = dict(item)
        data["source"] = "Bulk Import"
        add_question(data, created_by=user_id)
        imported += 1

    return imported, skipped


def import_section():
    st.subheader("📤 Bulk Question Import")
    st.caption("Upload a question file or import questions from a public Google Sheet.")

    required_columns = [
        "subject", "topic", "difficulty", "question",
        "option_a", "option_b", "option_c", "option_d",
        "correct_option", "explanation"
    ]

    template_df = pd.DataFrame(columns=required_columns)
    st.download_button(
        "⬇️ Download CSV Template",
        data=template_df.to_csv(index=False).encode("utf-8"),
        file_name="brain_challenge_questions_template.csv",
        mime="text/csv",
        use_container_width=False
    )

    file_tab, sheets_tab = st.tabs(["📁 Upload Question File", "📊 Google Sheets"])

    with file_tab:
        uploaded_file = st.file_uploader(
            "Choose a question file",
            type=["csv", "xlsx", "json"],
            help="Supported formats: CSV, Excel (.xlsx), and JSON."
        )

        if uploaded_file is not None:
            try:
                dataframe = _read_uploaded_questions(uploaded_file)
                valid_records, errors = _validate_import_dataframe(dataframe)

                st.write("**Preview**")
                st.dataframe(dataframe, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                col1.metric("Valid questions", len(valid_records))
                col2.metric("Validation errors", len(errors))

                if errors:
                    with st.expander("View validation errors", expanded=True):
                        for message in errors:
                            st.error(message)

                if valid_records and st.button(
                    "Import Valid Questions",
                    type="primary",
                    key="import_uploaded_questions"
                ):
                    imported, skipped = _import_question_records(valid_records)
                    st.success(
                        f"Import complete: {imported} added, {skipped} existing duplicates skipped."
                    )
                    st.rerun()

            except Exception as error:
                st.error(f"Unable to read this file: {error}")

    with sheets_tab:
        st.info(
            "The Google Sheet must be accessible to anyone with the link as a viewer. "
            "Private sheets require Google authentication and are not supported by this importer."
        )
        sheet_url = st.text_input(
            "Google Sheets URL",
            placeholder="https://docs.google.com/spreadsheets/d/..."
        )

        if st.button("Load Google Sheet", key="load_google_sheet"):
            if not sheet_url.strip():
                st.warning("Please paste a Google Sheets URL.")
            elif "docs.google.com/spreadsheets" not in sheet_url:
                st.error("Please enter a valid Google Sheets URL.")
            else:
                try:
                    import re
                    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
                    if not match:
                        raise ValueError("Could not find the spreadsheet ID in this URL.")

                    sheet_id = match.group(1)
                    gid_match = re.search(r"(?:\?|&)gid=(\d+)", sheet_url)
                    gid = gid_match.group(1) if gid_match else "0"
                    csv_url = (
                        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
                        f"?format=csv&gid={gid}"
                    )

                    sheet_df = _normalise_import_dataframe(pd.read_csv(csv_url))
                    valid_records, errors = _validate_import_dataframe(sheet_df)

                    st.session_state["pending_sheet_records"] = valid_records
                    st.session_state["pending_sheet_df"] = sheet_df
                    st.session_state["pending_sheet_errors"] = errors
                    st.success(f"Loaded {len(sheet_df)} rows from Google Sheets.")

                except Exception as error:
                    st.error(f"Could not load Google Sheet: {error}")

        if "pending_sheet_df" in st.session_state:
            st.write("**Google Sheet Preview**")
            st.dataframe(
                st.session_state["pending_sheet_df"],
                use_container_width=True,
                hide_index=True
            )
            records = st.session_state.get("pending_sheet_records", [])
            errors = st.session_state.get("pending_sheet_errors", [])
            col1, col2 = st.columns(2)
            col1.metric("Valid questions", len(records))
            col2.metric("Validation errors", len(errors))

            if errors:
                with st.expander("View validation errors"):
                    for message in errors:
                        st.error(message)

            if records and st.button(
                "Import Google Sheet Questions",
                type="primary",
                key="import_google_sheet_questions"
            ):
                imported, skipped = _import_question_records(records)
                st.success(
                    f"Import complete: {imported} added, {skipped} existing duplicates skipped."
                )
                for key in [
                    "pending_sheet_records", "pending_sheet_df", "pending_sheet_errors"
                ]:
                    st.session_state.pop(key, None)
                st.rerun()


def admin_dashboard():
    require_admin()

    admin_header()

    stats = get_admin_statistics()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Students", stats["total_students"])
    col2.metric("Questions", stats["total_questions"])
    col3.metric("Quiz Attempts", stats["total_attempts"])
    col4.metric("Admins", stats["total_admins"])

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "➕ Add Question",
        "📚 Manage Questions",
        "📤 Bulk Import"
    ])

    with tab1:
        question_form()

    with tab2:
        question_manager()

    with tab3:
        import_section()
