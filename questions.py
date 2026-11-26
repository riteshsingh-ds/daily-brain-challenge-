
# ==========================================
# DAILY BRAIN CHALLENGE
# Subject and Question Management
# ==========================================

from database import add_question, get_questions, get_subjects


# 1. SUBJECT CATALOGUE

SUBJECTS = {
    "Programming Languages": [
        "Python",
        "C",
        "C++",
        "Java",
        "JavaScript"
    ],

    "Data Science": [
        "Data Science Fundamentals",
        "NumPy",
        "Pandas",
        "Matplotlib",
        "Seaborn",
        "Data Cleaning",
        "Exploratory Data Analysis",
        "Data Visualization"
    ],

    "Artificial Intelligence": [
        "Artificial Intelligence Fundamentals",
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Generative AI",
        "Computer Vision",
        "Large Language Models"
    ],

    "Database and Backend": [
        "SQL",
        "MySQL",
        "DBMS",
        "PL/SQL",
        "MongoDB",
        "API Fundamentals"
    ],

    "Computer Science Core": [
        "Data Structures",
        "Algorithms",
        "Operating Systems",
        "Computer Networks",
        "Computer Organization",
        "Software Engineering",
        "Object-Oriented Programming"
    ],

    "Mathematics and Statistics": [
        "Linear Algebra",
        "Probability",
        "Statistics",
        "Calculus",
        "Discrete Mathematics"
    ],

    "Development and Tools": [
        "HTML",
        "CSS",
        "Git and GitHub",
        "Streamlit",
        "FastAPI",
        "Cloud Computing"
    ],

    "Career Preparation": [
        "Aptitude",
        "Logical Reasoning",
        "Technical Interviews",
        "Data Science Interviews",
        "Coding Interviews"
    ],

    "General Knowledge": [
        "Science",
        "Technology",
        "History",
        "Geography",
        "Current Affairs"
    ]
}


# 2. DIFFICULTY LEVELS

DIFFICULTIES = [
    "Easy",
    "Medium",
    "Hard"
]


# 3. SAMPLE QUESTION BANK
# These are starter questions.
# Admin can add more questions later.

SAMPLE_QUESTIONS = [

    # PYTHON

    {
        "subject": "Python",
        "topic": "Python Basics",
        "difficulty": "Easy",
        "question": "Which keyword is used to define a function in Python?",
        "option_a": "function",
        "option_b": "def",
        "option_c": "define",
        "option_d": "fun",
        "correct_option": "B",
        "explanation": "The def keyword is used to define a function in Python."
    },

    {
        "subject": "Python",
        "topic": "Data Types",
        "difficulty": "Easy",
        "question": "Which data type stores key-value pairs in Python?",
        "option_a": "List",
        "option_b": "Tuple",
        "option_c": "Dictionary",
        "option_d": "Set",
        "correct_option": "C",
        "explanation": "A dictionary stores data in key-value pairs."
    },

    # C++

    {
        "subject": "C++",
        "topic": "Basics",
        "difficulty": "Easy",
        "question": "Which symbol is used to end a statement in C++?",
        "option_a": ".",
        "option_b": ",",
        "option_c": ";",
        "option_d": ":",
        "correct_option": "C",
        "explanation": "C++ statements generally end with a semicolon."
    },

    # JAVA

    {
        "subject": "Java",
        "topic": "Basics",
        "difficulty": "Easy",
        "question": "Which keyword is used to create an object in Java?",
        "option_a": "class",
        "option_b": "new",
        "option_c": "this",
        "option_d": "static",
        "correct_option": "B",
        "explanation": "The new keyword creates an object in Java."
    },

    # SQL

    {
        "subject": "SQL",
        "topic": "SQL Basics",
        "difficulty": "Easy",
        "question": "Which SQL command retrieves data from a table?",
        "option_a": "INSERT",
        "option_b": "UPDATE",
        "option_c": "SELECT",
        "option_d": "DELETE",
        "correct_option": "C",
        "explanation": "SELECT is used to retrieve records from a database."
    },

    # DBMS

    {
        "subject": "DBMS",
        "topic": "Database Fundamentals",
        "difficulty": "Medium",
        "question": "Which key uniquely identifies each record in a table?",
        "option_a": "Foreign Key",
        "option_b": "Primary Key",
        "option_c": "Candidate Key",
        "option_d": "Composite Key",
        "correct_option": "B",
        "explanation": "A primary key uniquely identifies each row in a table."
    },

    # NUMPY

    {
        "subject": "NumPy",
        "topic": "Arrays",
        "difficulty": "Easy",
        "question": "Which function creates an array in NumPy?",
        "option_a": "np.array()",
        "option_b": "np.list()",
        "option_c": "np.create()",
        "option_d": "np.data()",
        "correct_option": "A",
        "explanation": "np.array() creates a NumPy array."
    },

    # PANDAS

    {
        "subject": "Pandas",
        "topic": "DataFrames",
        "difficulty": "Easy",
        "question": "Which Pandas function reads a CSV file?",
        "option_a": "pd.open_csv()",
        "option_b": "pd.read_csv()",
        "option_c": "pd.load_csv()",
        "option_d": "pd.csv()",
        "correct_option": "B",
        "explanation": "pd.read_csv() loads CSV data into a DataFrame."
    },

    # STATISTICS

    {
        "subject": "Statistics",
        "topic": "Descriptive Statistics",
        "difficulty": "Easy",
        "question": "Which measure represents the average of a dataset?",
        "option_a": "Median",
        "option_b": "Mode",
        "option_c": "Mean",
        "option_d": "Range",
        "correct_option": "C",
        "explanation": "The mean is calculated by dividing the sum of values by the number of values."
    },

    # MACHINE LEARNING

    {
        "subject": "Machine Learning",
        "topic": "ML Fundamentals",
        "difficulty": "Medium",
        "question": "Which algorithm is commonly used for classification?",
        "option_a": "Linear Regression",
        "option_b": "Logistic Regression",
        "option_c": "K-Means",
        "option_d": "PCA",
        "correct_option": "B",
        "explanation": "Logistic Regression is commonly used for classification tasks."
    },

    # DATA STRUCTURES

    {
        "subject": "Data Structures",
        "topic": "Stack",
        "difficulty": "Easy",
        "question": "Which principle does a stack follow?",
        "option_a": "FIFO",
        "option_b": "LIFO",
        "option_c": "Random Access",
        "option_d": "Priority Based",
        "correct_option": "B",
        "explanation": "A stack follows Last In, First Out."
    },

    # GENERATIVE AI

    {
        "subject": "Generative AI",
        "topic": "LLM Fundamentals",
        "difficulty": "Medium",
        "question": "What does LLM stand for?",
        "option_a": "Large Language Model",
        "option_b": "Linear Learning Machine",
        "option_c": "Language Logic Method",
        "option_d": "Large Learning Module",
        "correct_option": "A",
        "explanation": "LLM stands for Large Language Model."
    }
]


# 4. INITIALIZE SAMPLE QUESTIONS

def initialize_sample_questions():
    """
    Insert starter questions only when the database
    does not already contain questions.
    """

    existing_questions = get_questions(limit=1)

    if existing_questions:
        return

    for question in SAMPLE_QUESTIONS:
        add_question(
            question,
            created_by=None
        )


# 5. GET ALL AVAILABLE SUBJECTS

def get_all_subjects():
    """Return subjects that have active questions."""

    return get_subjects()


# 6. GET SUBJECT CATEGORIES

def get_subject_categories():
    """Return the complete subject catalogue."""

    return SUBJECTS


# 7. GET TOPICS FOR A CATEGORY

def get_topics(category):
    """Return topics under a selected category."""

    return SUBJECTS.get(category, [])


# 8. GET QUESTIONS

def fetch_questions(
    subject="All",
    difficulty="All",
    limit=10
):
    """Fetch randomized questions from the database."""

    return get_questions(
        subject=subject,
        difficulty=difficulty,
        limit=limit
    )


# 9. GET DIFFICULTY LEVELS

def get_difficulty_levels():
    return DIFFICULTIES


# 10. LOAD INITIAL QUESTIONS

initialize_sample_questions()
