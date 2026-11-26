# 🧠 Daily Brain Challenge

### Learn. Practice. Challenge Yourself. Earn Certificates.

Daily Brain Challenge is an interactive educational quiz and skill assessment platform built with **Python and Streamlit**. It helps students practice technical subjects, evaluate their knowledge, track learning progress, and earn platform-issued achievement certificates.

## 🚀 Features

- **User Authentication** – Register and log in securely.
- **Multiple Subjects** – Practice Python, C, C++, Java, SQL, DBMS, Data Structures, Statistics, Data Science, Machine Learning, and more.
- **Interactive Quizzes** – Test your knowledge with subject-wise MCQ assessments.
- **Performance Tracking** – Review scores and monitor your progress.
- **Leaderboard** – Compare quiz performance with other learners.
- **Admin Panel** – Add, manage, and organize questions.
- **Bulk Question Import** – Import questions using supported CSV, Excel, JSON, and Google Sheets CSV formats.
- **Achievement Certificates** – Earn unique PDF certificates after meeting the assessment requirements.
- **QR-Based Verification** – Verify certificate authenticity through the platform.
- **Certificate Management** – View earned certificates and allow admins to manage or revoke them.

## 🎓 Certificate Eligibility

To qualify for a subject achievement certificate:

- Minimum score: **70%**
- Minimum assessment size: **20 questions**
- Each user receives a unique certificate for each qualifying subject.

Short practice quizzes remain available but do not qualify for certificates.

*These are platform-issued achievement certificates and are not government or university-accredited qualifications.*

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming |
| Streamlit | Web application interface |
| SQLite | Database |
| Pandas | Data handling |
| Plotly | Data visualization |
| ReportLab | PDF certificate generation |
| QR Code | Certificate verification |

## 💻 Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/daily-brain-challenge.git
cd daily-brain-challenge
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## 📁 Project Structure

```text
daily-brain-challenge/
│
├── app.py
├── database.py
├── auth.py
├── questions.py
├── admin.py
├── importers.py
├── quiz_engine.py
├── certificate_system.py
├── requirements.txt
├── README.md
│
└── assets/
    └── founder_signature.png
```

## 🔐 Database

The application uses SQLite to store user accounts, questions, quiz attempts, and certificates.

The database file `brain_challenge.db` is created automatically when the application initializes.

**Important:** Keep your database file safe. For production deployment with multiple users, configure persistent database storage.

## 👨‍💻 Founder

**Ritesh Kumar Singh**  
Founder & CEO – Daily Brain Challenge  
CSE (Data Science) Student

## 🎯 Project Vision

To make technical learning more engaging, accessible, and measurable by giving students a place to practice skills, evaluate their knowledge, and track their progress.

## ⭐ Support

If you find this project useful, consider giving the repository a star ⭐ on GitHub.

---

**Daily Brain Challenge — Learn Something New Every Day!**
