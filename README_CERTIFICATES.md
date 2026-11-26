# Daily Brain Challenge — Certificate System Update

## Eligibility
- Certificate assessment must contain at least **20 questions**.
- Student must achieve at least **70% accuracy**.
- Shorter practice quizzes continue to work but do not issue certificates.
- The first qualifying certificate per student and subject is stored. The database enforces one certificate per student/subject.

## Files in this update
- `app.py` — adds My Certificates, public Verify Certificate, and admin certificate management.
- `database.py` — adds the certificates table and CRUD helpers. Existing data is preserved; the table is created automatically when the app starts.
- `quiz_engine.py` — issues certificates automatically after an eligible completed quiz.
- `certificate_system.py` — creates the navy/gold landscape PDF, QR code, verification page, and admin revocation UI.
- `assets/founder_signature.png` — transparent crop of the signature image supplied by the owner.
- `requirements.txt` — adds ReportLab and QR-code dependencies.

## Install and run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Keep all Python files in the same project directory and keep the `assets` folder beside them. Do not delete your existing `brain_challenge.db` file; the new certificate table is added automatically.

## Configure the deployed verification URL
For a deployed Streamlit app, add this to `.streamlit/secrets.toml`:

```toml
[app]
base_url = "https://YOUR-DEPLOYED-APP-URL"
```

Replace the example with the exact public app URL. Alternatively set the `CERTIFICATE_BASE_URL` environment variable. Without this setting, generated QR codes use `http://localhost:8501`, which is suitable only for local testing.

## Admin controls
An authenticated admin sees the Certificate Management section on the Admin Panel. Admins can review issued records and revoke a certificate. A revoked certificate remains in the database and its verification page reports that it is revoked.

## Important
These are platform-issued skill achievement certificates. QR verification checks the Daily Brain Challenge database; it does not make the certificate a government-accredited or university-issued qualification. Protect the signature asset and admin credentials, and use persistent database storage when deploying publicly.
