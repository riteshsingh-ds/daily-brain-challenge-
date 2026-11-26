
import time
import streamlit as st

from database import (
    get_questions,
    save_quiz_attempt
)


# ==========================================
# QUIZ CONFIGURATION
# ==========================================

QUIZ_OPTIONS = [5, 10, 15, 20]

QUIZ_DURATION_MINUTES = 5


# ==========================================
# START QUIZ
# ==========================================

def start_quiz(subject, difficulty, total_questions):
    """Generate a new quiz and initialize its session."""

    questions = get_questions(
        subject=subject,
        difficulty=difficulty,
        limit=total_questions
    )

    if not questions:
        return False, "No questions available for this selection."

    if len(questions) < total_questions:
        return False, (
            f"Only {len(questions)} questions are available. "
            f"Please select {len(questions)} or fewer."
        )

    st.session_state["current_quiz"] = questions
    st.session_state["quiz_answers"] = {}
    st.session_state["quiz_subject"] = subject
    st.session_state["quiz_difficulty"] = difficulty
    st.session_state["quiz_started_at"] = time.time()
    st.session_state["quiz_duration"] = (
        QUIZ_DURATION_MINUTES * 60
    )
    st.session_state["quiz_completed"] = False

    return True, "Quiz started successfully!"


# ==========================================
# TIMER
# ==========================================

def get_remaining_time():
    """Calculate remaining quiz time in seconds."""

    start_time = st.session_state.get(
        "quiz_started_at"
    )

    duration = st.session_state.get(
        "quiz_duration",
        QUIZ_DURATION_MINUTES * 60
    )

    if start_time is None:
        return 0

    elapsed = time.time() - start_time

    return max(0, int(duration - elapsed))


def format_time(seconds):
    """Convert seconds into MM:SS format."""

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    return f"{minutes:02d}:{remaining_seconds:02d}"


# ==========================================
# ANSWER MANAGEMENT
# ==========================================

def save_answer(question_id, selected_option):
    """Save or update a selected answer."""

    answers = st.session_state.get(
        "quiz_answers",
        {}
    )

    if selected_option is not None:
        answers[question_id] = selected_option
    else:
        answers.pop(question_id, None)

    st.session_state["quiz_answers"] = answers


def get_selected_answer(question_id):
    """Get the selected answer for a question."""

    return st.session_state.get(
        "quiz_answers",
        {}
    ).get(question_id)


# ==========================================
# SCORE CALCULATION
# ==========================================

def calculate_results():
    """Calculate quiz score and answer-level results."""

    questions = st.session_state.get(
        "current_quiz",
        []
    )

    answers = st.session_state.get(
        "quiz_answers",
        {}
    )

    results = []

    correct_count = 0

    for question in questions:

        question_id = question["id"]

        selected = answers.get(question_id)

        correct = question["correct_option"]

        is_correct = (
            selected is not None
            and selected.upper() == correct.upper()
        )

        if is_correct:
            correct_count += 1

        results.append({
            "question_id": question_id,
            "question_text": question["question"],
            "selected_option": selected,
            "correct_option": correct,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
            "option_a": question["option_a"],
            "option_b": question["option_b"],
            "option_c": question["option_c"],
            "option_d": question["option_d"]
        })

    total = len(questions)

    accuracy = (
        round((correct_count / total) * 100, 2)
        if total else 0
    )

    return {
        "total": total,
        "correct": correct_count,
        "incorrect": total - correct_count,
        "unanswered": sum(1 for item in results if item["selected_option"] is None),
        "accuracy": accuracy,
        "score": correct_count,
        "results": results
    }


# ==========================================
# SUBMIT QUIZ
# ==========================================

def submit_quiz():
    """Calculate results and save the completed attempt."""

    if st.session_state.get("quiz_completed"):
        return

    user_id = st.session_state.get("user_id")

    if not user_id:
        raise ValueError("Please log in before submitting a quiz.")

    result = calculate_results()

    questions = st.session_state.get(
        "current_quiz",
        []
    )

    answers_to_save = []

    for answer in result["results"]:
        answers_to_save.append({
            "question_id": answer["question_id"],
            "question_text": answer["question_text"],
            "selected_option": answer["selected_option"],
            "correct_option": answer["correct_option"]
        })

    elapsed = int(
        time.time()
        - st.session_state["quiz_started_at"]
    )

    attempt_id = save_quiz_attempt(
        user_id=user_id,
        subject=st.session_state["quiz_subject"],
        difficulty=st.session_state["quiz_difficulty"],
        answers=answers_to_save,
        time_taken=elapsed
    )

    result["attempt_id"] = attempt_id

    # Certificate eligibility: at least 20 questions and 70% accuracy.
    result["certificate"] = None
    if result["total"] >= 20 and result["accuracy"] >= 70:
        from database import create_certificate
        certificate = create_certificate(
            user_id=user_id,
            subject=st.session_state["quiz_subject"],
            attempt_id=attempt_id,
            total_questions=result["total"],
            correct_answers=result["correct"],
            accuracy=result["accuracy"]
        )
        result["certificate"] = certificate

    st.session_state["quiz_result"] = result
    st.session_state["quiz_completed"] = True

    return result


# ==========================================
# QUIZ INTERFACE
# ==========================================

def render_quiz():
    """Render the complete quiz interface."""

    questions = st.session_state.get(
        "current_quiz",
        []
    )

    if not questions:
        st.warning("No active quiz found.")
        return

    from streamlit_autorefresh import st_autorefresh

    remaining = get_remaining_time()

    # Refresh the interface every second.
    st_autorefresh(
        interval=1000,
        limit=None,
        key="quiz_timer_refresh"
    )

    st.title("🧠 Daily Brain Challenge")

    st.write(
        f"Subject: **{st.session_state['quiz_subject']}**"
    )

    st.write(
        f"Difficulty: **{st.session_state['quiz_difficulty']}**"
    )

    st.divider()

    if remaining <= 30:
        st.error(
            f"⏰ Time remaining: {format_time(remaining)}"
        )
    else:
        st.info(
            f"⏱️ Time remaining: {format_time(remaining)}"
        )

    if remaining <= 0:
        st.warning("Time is up! Submitting your quiz...")
        submit_quiz()
        st.rerun()

    total = len(questions)

    answers = st.session_state.get(
        "quiz_answers",
        {}
    )

    answered = len(answers)

    st.progress(answered / total)

    st.caption(
        f"Answered {answered} of {total} questions"
    )

    st.divider()

    for index, question in enumerate(questions):

        question_id = question["id"]

        st.markdown(
            f"### Question {index + 1}"
        )

        st.write(question["question"])

        options = {
            "A": question["option_a"],
            "B": question["option_b"],
            "C": question["option_c"],
            "D": question["option_d"]
        }

        selected = get_selected_answer(question_id)

        selected_index = (
            list(options.keys()).index(selected)
            if selected in options
            else None
        )

        choice = st.radio(
            "Select your answer:",
            options=list(options.keys()),
            format_func=lambda key: f"{key}. {options[key]}",
            index=selected_index,
            key=f"answer_{question_id}",
            label_visibility="collapsed"
        )

        save_answer(question_id, choice)

        st.divider()

    if st.button(
        "🚀 Submit Quiz",
        use_container_width=True
    ):

        submit_quiz()
        st.rerun()


# ==========================================
# RESULT PAGE
# ==========================================

def render_results():
    """Display final quiz results and explanations."""

    result = st.session_state.get("quiz_result")

    if not result:
        st.warning("No quiz results available.")
        return

    st.title("🏆 Quiz Results")

    st.metric(
        "Your Score",
        f"{result['score']} / {result['total']}"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Correct",
        result["correct"]
    )

    col2.metric(
        "Incorrect",
        result["incorrect"]
    )

    col3.metric(
        "Accuracy",
        f"{result['accuracy']}%"
    )

    st.progress(
        result["accuracy"] / 100
    )

    certificate = result.get("certificate")
    if certificate and certificate.get("status") == "valid":
        st.success("🏆 Congratulations! You qualified for a subject certificate.")
        st.info(f"Certificate ID: {certificate['certificate_id']} — open **My Certificates** to download it.")
    elif result["total"] >= 20 and result["accuracy"] < 70:
        st.warning("Certificate not earned yet. You need at least 70% accuracy.")

    if result["accuracy"] >= 80:
        st.success("Excellent work! Keep learning! 🎉")

    elif result["accuracy"] >= 50:
        st.info("Good effort! Keep practicing. 💪")

    else:
        st.warning("Don't give up! Review your mistakes and try again.")

    st.divider()

    st.subheader("📖 Answer Review")

    for index, answer in enumerate(result["results"]):

        with st.expander(
            f"Question {index + 1} - "
            f"{'Correct ✅' if answer['is_correct'] else 'Incorrect ❌'}"
        ):

            st.write(answer["question_text"])

            st.write(f"A. {answer['option_a']}")
            st.write(f"B. {answer['option_b']}")
            st.write(f"C. {answer['option_c']}")
            st.write(f"D. {answer['option_d']}")

            st.write(
                f"Your answer: {answer['selected_option'] or 'Not answered'}"
            )

            st.success(
                f"Correct answer: {answer['correct_option']}"
            )

            if answer["explanation"]:
                st.info(answer["explanation"])


# ==========================================
# RESET QUIZ
# ==========================================

def reset_quiz():
    """Clear quiz-specific session information."""

    keys = [
        "current_quiz",
        "quiz_answers",
        "quiz_subject",
        "quiz_difficulty",
        "quiz_started_at",
        "quiz_duration",
        "quiz_completed",
        "quiz_result"
    ]

    for key in keys:
        st.session_state.pop(key, None)
