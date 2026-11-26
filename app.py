
import streamlit as st
import pandas as pd

from auth import (
    register_user,
    login_user,
    set_login_session,
    logout_user,
    is_logged_in,
    is_admin,
    get_current_user
)

from database import (
    get_subjects,
    get_questions,
    get_user_statistics,
    get_user_attempts,
    get_leaderboard
)

from questions import (
    SUBJECTS,
    DIFFICULTIES
)

from quiz_engine import (
    start_quiz,
    render_quiz,
    render_results,
    reset_quiz
)

from admin import admin_dashboard
from certificate_system import (
    render_my_certificates,
    render_certificate_verification,
    render_admin_certificates,
)


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Daily Brain Challenge",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# CUSTOM CSS
# ==========================================

def load_css():

    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(
            135deg,
            #0b1020 0%,
            #111a31 50%,
            #101827 100%
        );
        color: #f1f5f9;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }

    [data-testid="stSidebar"] {
        background: #101a2e;
        border-right: 1px solid #263550;
    }

    .hero {
        padding: 42px;
        border-radius: 22px;
        background: linear-gradient(
            120deg,
            #172c4e,
            #193c64,
            #164e63
        );
        border: 1px solid #31547a;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 42px;
        font-weight: 800;
        color: white;
    }

    .hero p {
        font-size: 17px;
        color: #dbeafe;
    }

    .section-heading {
        font-size: 25px;
        font-weight: 750;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .subject-card {
        background: #17243a;
        border: 1px solid #2c405e;
        padding: 20px;
        border-radius: 15px;
        min-height: 125px;
    }

    .subject-card h3 {
        color: #93c5fd;
        font-size: 18px;
    }

    .subject-card p {
        color: #cbd5e1;
        font-size: 13px;
    }

    .feature-card {
        background: #16243a;
        border: 1px solid #293e5d;
        padding: 22px;
        border-radius: 16px;
        min-height: 150px;
    }

    .feature-card h3 {
        color: #bfdbfe;
    }

    .muted-text {
        color: #a9b9cf;
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 650;
        min-height: 42px;
    }

    </style>
    """, unsafe_allow_html=True)


load_css()


# ==========================================
# ADMIN ACCOUNT BOOTSTRAP
# ==========================================

def create_initial_admin():
    """
    Optionally create an initial admin from Streamlit secrets.

    Configure [admin] in .streamlit/secrets.toml.
    This does not promote existing student accounts.
    """

    try:
        config = st.secrets.get("admin", {})

        username = config.get("username", "")
        email = config.get("email", "")
        password = config.get("password", "")

        if not all([username, email, password]):
            return

        from database import get_db_connection

        conn = get_db_connection()

        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        finally:
            conn.close()

        if existing is None:

            success, message = register_user(
                username,
                email,
                password
            )

            if success:
                conn = get_db_connection()

                try:
                    conn.execute("""
                        UPDATE users
                        SET role = 'admin'
                        WHERE username = ?
                    """, (username,))

                    conn.commit()

                finally:
                    conn.close()

    except Exception:
        # Admin secrets are optional.
        pass


create_initial_admin()


# ==========================================
# HOME PAGE
# ==========================================

def render_homepage():

    st.markdown("""
    <div class="hero">
        <h1>🧠 Daily Brain Challenge</h1>
        <p>
            Learn smarter. Practice daily. Improve continuously.
        </p>
        <p>
            Explore programming, Data Science, Artificial Intelligence,
            mathematics and computer science through interactive quizzes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])

    with col1:

        st.markdown("### Your Knowledge. Your Growth.")

        st.write(
            "Build strong technical foundations, test your skills "
            "and prepare for real-world challenges with daily practice."
        )

        st.markdown("""
        - 📚 Multiple technical subjects
        - 💻 Programming and coding concepts
        - 📊 Data Science and Machine Learning
        - 🤖 Artificial Intelligence and Generative AI
        - 🏆 Performance tracking and leaderboard
        """)

        if is_logged_in():

            if st.button(
                "Go to My Dashboard →",
                type="primary",
                use_container_width=True
            ):
                st.session_state["page"] = "Dashboard"
                st.rerun()

        else:

            if st.button(
                "Start Learning →",
                type="primary",
                use_container_width=True
            ):
                st.session_state["page"] = "Login / Register"
                st.rerun()

    with col2:

        st.image(
            "https://images.unsplash.com/photo-1507842217343-583bb7270b66",
            caption="A space for learning and discovery",
            use_container_width=True
        )

    st.markdown(
        '<div class="section-heading">Explore Learning Categories</div>',
        unsafe_allow_html=True
    )

    category_icons = {
        "Programming Languages": "💻",
        "Data Science": "📊",
        "Artificial Intelligence": "🤖",
        "Database and Backend": "🗄️",
        "Computer Science Core": "🧩",
        "Mathematics and Statistics": "📐",
        "Development and Tools": "🛠️",
        "Career Preparation": "🎯",
        "General Knowledge": "🌍"
    }

    categories = list(SUBJECTS.items())

    for start in range(0, len(categories), 3):

        cols = st.columns(3)

        for col, (category, topics) in zip(
            cols,
            categories[start:start + 3]
        ):

            with col:

                icon = category_icons.get(category, "📚")

                st.markdown(f"""
                <div class="subject-card">
                    <h3>{icon} {category}</h3>
                    <p>{len(topics)} learning topics</p>
                    <p>{", ".join(topics[:3])}...</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-heading">Why Daily Brain Challenge?</div>',
        unsafe_allow_html=True
    )

    feature_cols = st.columns(3)

    features = [
        (
            "📖 Learn",
            "Explore multiple subjects and strengthen your fundamentals."
        ),
        (
            "🧠 Practice",
            "Solve MCQs and test your knowledge with timed quizzes."
        ),
        (
            "📈 Improve",
            "Track your scores and identify areas for improvement."
        )
    ]

    for col, (heading, description) in zip(
        feature_cols,
        features
    ):

        with col:

            st.markdown(f"""
            <div class="feature-card">
                <h3>{heading}</h3>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# LOGIN AND REGISTRATION
# ==========================================

def render_auth_page():

    st.title("👋 Welcome to Daily Brain Challenge")

    login_tab, register_tab = st.tabs([
        "Login",
        "Create Account"
    ])

    with login_tab:

        st.subheader("Login to your account")

        with st.form("login_form"):

            username = st.text_input("Username")

            password = st.text_input(
                "Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if submitted:

                success, message, user_data = login_user(
                    username,
                    password
                )

                if success:

                    set_login_session(user_data)

                    st.success(message)
                    st.session_state["page"] = "Dashboard"
                    st.rerun()

                else:
                    st.error(message)

    with register_tab:

        st.subheader("Create your student account")

        with st.form("register_form"):

            new_username = st.text_input(
                "Choose Username"
            )

            email = st.text_input(
                "Email Address"
            )

            new_password = st.text_input(
                "Create Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submitted:

                if new_password != confirm_password:

                    st.error("Passwords do not match.")

                else:

                    success, message = register_user(
                        new_username,
                        email,
                        new_password
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)


# ==========================================
# STUDENT DASHBOARD
# ==========================================

def render_dashboard():

    user = get_current_user()

    if not user:
        return

    st.title(
        f"Welcome back, {user['username']}! 👋"
    )

    st.caption(
        "Your learning journey continues here."
    )

    stats = get_user_statistics(user["id"])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Quizzes Played",
        stats["total_quizzes"]
    )

    col2.metric(
        "Questions Attempted",
        stats["questions_attempted"]
    )

    col3.metric(
        "Correct Answers",
        stats["total_correct"]
    )

    col4.metric(
        "Average Accuracy",
        f"{stats['average_accuracy']}%"
    )

    st.divider()

    st.subheader("📊 Your Learning Performance")

    attempts = get_user_attempts(
        user["id"],
        limit=20
    )

    if attempts:

        df = pd.DataFrame(attempts)

        df = df.sort_values(
            "id",
            ascending=True
        )

        st.line_chart(
            df.set_index("created_at")["accuracy"],
            y_label="Accuracy (%)"
        )

        st.subheader("Recent Quiz Attempts")

        display_df = df[
            [
                "subject",
                "difficulty",
                "total_questions",
                "correct_answers",
                "accuracy",
                "created_at"
            ]
        ].copy()

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "You haven't attempted a quiz yet. "
            "Start your first challenge today!"
        )

    st.divider()

    if st.button(
        "🚀 Start a New Quiz",
        type="primary",
        use_container_width=True
    ):

        st.session_state["page"] = "Start Quiz"
        st.rerun()


# ==========================================
# QUIZ SELECTION PAGE
# ==========================================

def render_quiz_selection():

    st.title("🎯 Choose Your Challenge")

    available_subjects = get_subjects()

    if not available_subjects:

        st.warning(
            "No questions are available yet. "
            "Please contact the administrator."
        )

        return

    subject = st.selectbox(
        "Choose Subject",
        available_subjects
    )

    difficulty = st.selectbox(
        "Choose Difficulty",
        DIFFICULTIES
    )

    available_questions = get_questions(
        subject=subject,
        difficulty=difficulty,
        limit=1000
    )

    available_count = len(available_questions)

    st.info(
        f"Available questions: {available_count}"
    )

    question_options = [
        count
        for count in [5, 10, 15, 20]
        if count <= available_count
    ]

    if not question_options:

        st.warning(
            "At least 5 questions are required to start a quiz."
        )

        return

    total_questions = st.selectbox(
        "Number of Questions",
        question_options
    )

    st.caption(
        "Time limit: 5 minutes"
    )

    if st.button(
        "🚀 Start Quiz",
        type="primary",
        use_container_width=True
    ):

        success, message = start_quiz(
            subject,
            difficulty,
            total_questions
        )

        if success:

            st.session_state["page"] = "Quiz"
            st.rerun()

        else:
            st.error(message)


# ==========================================
# LEADERBOARD
# ==========================================

def render_leaderboard():

    st.title("🏆 Global Leaderboard")

    leaderboard = get_leaderboard(limit=20)

    if not leaderboard:

        st.info(
            "The leaderboard will appear after students "
            "complete their first quizzes."
        )

        return

    df = pd.DataFrame(leaderboard)

    df.insert(
        0,
        "Rank",
        range(1, len(df) + 1)
    )

    df = df.rename(columns={
        "username": "Student",
        "quizzes_played": "Quizzes",
        "total_correct": "Correct Answers",
        "average_accuracy": "Average Accuracy"
    })

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# OWNER PROFILE / ABOUT ME
# ==========================================

def render_owner_profile():
    """Compact founder profile displayed in the sidebar."""
    st.markdown(
        """
        <div style="
            background: linear-gradient(145deg, #172b49, #142238);
            border: 1px solid #30496b;
            border-radius: 15px;
            padding: 16px 14px;
            margin-top: 18px;
        ">
            <div style="font-size: 13px; color: #9fb7d5; letter-spacing: 1px;">
                ABOUT THE CREATOR
            </div>
            <div style="font-size: 18px; font-weight: 750; color: #ffffff; margin-top: 8px;">
                👨‍💻 Ritesh Kumar Singh
            </div>
            <div style="font-size: 13px; color: #93c5fd; margin-top: 3px;">
                Founder &amp; CEO
            </div>
            <hr style="border: 0; border-top: 1px solid #30496b; margin: 12px 0;">
            <div style="font-size: 13px; color: #d5deeb; line-height: 1.55;">
                CSE (Data Science) Student<br>
                Passionate about Data Science, AI/ML and building
                practical technology solutions.
            </div>
            <div style="
                display: inline-block;
                margin-top: 12px;
                padding: 5px 9px;
                border-radius: 20px;
                background: #1d493f;
                color: #86efac;
                font-size: 11px;
                font-weight: 650;
            ">
                Creator of Brain Challenge
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================
# MAIN APPLICATION
# ==========================================

def main():

    if "page" not in st.session_state:
        st.session_state["page"] = "Home"

    # Sidebar
    with st.sidebar:

        st.markdown("## 🧠 Brain Challenge")

        st.caption(
            "Learn • Practice • Improve"
        )

        st.divider()

        if is_logged_in():

            st.success(
                f"Logged in as {st.session_state['username']}"
            )

            if is_admin():
                st.caption("Role: Administrator")
            else:
                st.caption("Role: Student")

        pages = [
            "Home",
            "Dashboard",
            "Start Quiz",
            "Leaderboard"
        ]

        if is_logged_in() and not is_admin():
            pages.append("My Certificates")

        pages.append("Verify Certificate")

        if is_admin():
            pages.append("Admin Panel")

        if st.session_state.get("current_quiz") or st.session_state.get("quiz_completed"):
            pages.append("Quiz")

        if is_logged_in():
            pages.append("Logout")
        else:
            pages.append("Login / Register")

        current_page = st.session_state["page"]

        if current_page not in pages:
            current_page = "Home"

        selected_page = st.radio(
            "Navigation",
            pages,
            index=pages.index(current_page)
        )

        st.session_state["page"] = selected_page

        st.divider()
        render_owner_profile()

    # Public QR verification route. No login is required.
    query_certificate_id = st.query_params.get("verify")
    if query_certificate_id:
        render_certificate_verification(str(query_certificate_id))
        return

    # Page routing
    page = st.session_state["page"]

    # Active quiz takes priority over navigation.
    if (
        st.session_state.get("current_quiz")
        and not st.session_state.get("quiz_completed")
    ):

        if page != "Quiz":
            st.session_state["page"] = "Quiz"

        render_quiz()
        return

    if page == "Home":

        render_homepage()

    elif page == "Login / Register":

        render_auth_page()

    elif page == "Dashboard":

        if is_logged_in():
            render_dashboard()
        else:
            st.warning("Please log in first.")
            render_auth_page()

    elif page == "Start Quiz":

        if is_logged_in():
            render_quiz_selection()
        else:
            st.warning("Please log in first.")
            render_auth_page()

    elif page == "Quiz":

        if st.session_state.get("quiz_completed"):
            render_results()

            if st.button(
                "Start Another Quiz",
                type="primary",
                use_container_width=True
            ):

                reset_quiz()
                st.session_state["page"] = "Start Quiz"
                st.rerun()

        else:
            st.info("No active quiz. Start a new challenge.")
            st.session_state["page"] = "Start Quiz"
            st.rerun()

    elif page == "Leaderboard":

        render_leaderboard()

    elif page == "My Certificates":

        if is_logged_in():
            user = get_current_user()
            render_my_certificates(user["id"])
        else:
            st.warning("Please log in to view your certificates.")
            render_auth_page()

    elif page == "Verify Certificate":

        render_certificate_verification()

    elif page == "Admin Panel":

        if is_admin():
            admin_dashboard()
            st.divider()
            render_admin_certificates()
        else:
            st.error("Unauthorized access.")

    elif page == "Logout":

        logout_user()
        st.session_state["page"] = "Home"
        st.success("You have been logged out.")
        st.rerun()


if __name__ == "__main__":
    main()
