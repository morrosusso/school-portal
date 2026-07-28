# School Management Portal

A Django-based school management portal for a combined Upper Basic &
Senior Secondary School (built for The Gambia). Role-based logins for
Principal, Vice Principals, Senior Teachers, Teachers, Bursar,
Secretary, IT Support, Librarian, Non-Teaching Staff, Parents,
Students, and Cluster Monitors.

## What's included (Phase 1)

- **Accounts** — one custom login model shared by every role, with
  automatic admin-permission flagging.
- **Admissions** — public application form. The moment staff mark an
  application **Accepted**, a Student record + auto-generated
  **Student ID** (`SCH-<year>-<4-digit sequence>`) + login account
  are created automatically. No manual step needed.
- **Academics** — departments, subjects, classes/streams (7A–12F),
  teacher assignments, timetable slots (with clash detection).
- **Assessment** —
  - Teachers enter CA + exam scores per class, or **bulk-upload
    grades via CSV** (`student_id, subject_code, ca_score,
    exam_score` — see *CSV grade upload* below).
  - **Termly report cards**: students (and their parents) can
    download their own report as a PDF, once staff mark it
    *Published*.
  - **Official transcripts**: downloadable **only** by staff whose
    role carries admin permission (Principal, Vice Principals,
    Senior Teachers, Secretary, IT Support) — students and parents
    cannot download transcripts, by design.
- **Finance** — fee types, invoices, payments, balance view for
  students/parents, overview for Bursar/Principal.
- **Library** — book catalog, borrow/return tracking.
- **Communication** — role-targeted notice board.
- **Role-based dashboards** for every user category.

## Not yet included (flagged for a later phase)

These are large enough that bolting them on properly needs their own
design pass rather than a rushed version:
- Native mobile app
- SMS gateway integration for parent alerts
- Automatic timetable-generation algorithm (current version is
  manual entry + clash detection)
- MoBSE-formatted cluster export
- Two-factor authentication (`django-otp` drops in cleanly when you're ready)
- Field-level encryption at rest (`django-cryptography` for specific fields)

## CSV grade upload (for teachers)

Instead of typing scores one by one, a teacher can go to
**Upload Grades (CSV)** and upload a file shaped like this:

```csv
student_id,subject_code,ca_score,exam_score
SCH-2026-0001,MATH101,32,55
SCH-2026-0002,MATH101,28,49
```

- `student_id` must match an existing Student ID exactly.
- `subject_code` must match a Subject's code (set these up under
  Academics → Subjects in `/admin/`).
- `ca_score` is out of 40, `exam_score` is out of 60 (change the
  split in `assessment/models.py` if your school uses a different
  weighting).
- A plain **Teacher** can only upload scores for subjects they are
  assigned to teach (via Teacher Assignments). **Senior Teachers,
  Vice Principals, and the Principal** can upload for any subject.
- After upload you get a row-by-row report (saved / failed + why),
  and every upload is logged (`Assessment → Result upload logs` in
  `/admin/`) so mistakes can be traced back.

## Running it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env if you want

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — public home page and admission form.
Visit `http://127.0.0.1:8000/admin/` to log in as your superuser and
set up Departments, Subjects, Classes, Academic Session/Term, and
Teacher Assignments before onboarding real staff.

### Recommended first-time setup order (in `/admin/`)

1. **Academic Session** (e.g. `2025/2026`, tick "is current")
2. **Term** (First/Second/Third Term for that session, tick "is current")
3. **Departments** (Science, Languages & Humanities, Business & ICT, etc.)
4. **Subjects** (with short codes — these are what CSV uploads match on)
5. **School Classes** (7A–12F as needed)
6. Create staff logins — either in `/admin/` directly, or once you
   have one admin-permission account logged into the portal, use the
   **Add Staff** page in the navbar.
7. **Teacher Assignments** — link each teacher to their subject(s)
   and class(es); this drives both the timetable and CSV-upload
   permission checks.

## Deploying to Render (free tier)

1. Push this folder to a GitHub repository.
2. On Render: **New → Web Service**, connect the repo.
3. Build Command: `./build.sh`
   Start Command: `gunicorn school_portal.wsgi:application`
4. Add a free **PostgreSQL** instance on Render, copy its *Internal
   Database URL*.
5. Set these Environment Variables on the web service:
   - `SECRET_KEY` — generate one, e.g. `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `your-app-name.onrender.com`
   - `DATABASE_URL` = (the Postgres Internal Database URL from step 4)
   - `SCHOOL_NAME`, `SCHOOL_ADDRESS`, `SCHOOL_MOTTO`, `CURRENT_SESSION` — customize as needed
6. Deploy. Render runs `build.sh` (installs deps, collects static
   files, runs migrations) automatically on every push.
7. Once live, open a **Shell** tab on the Render service and run:
   `python manage.py createsuperuser`

The same codebase runs unchanged locally (SQLite, DEBUG on) and on
Render (Postgres, DEBUG off) — it switches based on environment
variables only, never code changes.

## Project structure

```
school_portal/
├── school_portal/     # settings, root urls
├── accounts/          # custom User, roles, staff/parent profiles
├── students/          # applications, students, auto-ID signal
├── academics/          # departments, subjects, classes, timetable
├── assessment/         # results, report cards, transcripts, CSV upload
├── finance/            # fees, invoices, payments
├── library_mgmt/       # book catalog, borrowing
├── communication/      # notice board
├── core/                # dashboard router, home page
├── templates/           # shared templates (base, dashboards, login)
├── static/css/          # shared stylesheet
├── requirements.txt
├── Procfile / build.sh / runtime.txt   # Render deployment
└── .env.example
```
