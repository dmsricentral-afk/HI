"""
database.py
SQLite storage for the Payroll Processing System.

Schema redesigned to match a real retail-store salary master
(reference: RANAYA salary master workbook) rather than a generic
CTC-breakup model. Three tables:

  employees     - master data per employee (rates, statutory numbers)
  monthly_pay   - the variable inputs entered every month per employee
                  (attendance + all incentive/fine amounts for that month)
  payroll_runs  - the computed, saved result of a payroll run
"""

import sqlite3
import os
import hashlib
import binascii
import secrets

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payroll.db")

# ---------------------------------------------------------------
# Default login seeded on first run (change it via the in-app
# "Change Password" screen right after your first login).
# ---------------------------------------------------------------
DEFAULT_USERNAME = "hr"
DEFAULT_PASSWORD = "hr@123"
DEFAULT_ROLE = "HR Manager"
PBKDF2_ITERATIONS = 200_000


def get_connection():
    # timeout: how long sqlite3 waits (retrying) for a lock before raising
    # "database is locked" - default is 5s, bumped here since this app
    # opens a fresh connection per call and can be hit by brief external
    # locks (antivirus/OneDrive scanning the file, etc).
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA busy_timeout = 20000")
    # WAL: readers no longer block the writer (and vice versa), which is
    # the main fix for "database is locked" under this app's pattern of
    # many short-lived connections. Cheap to set on every connect - it's
    # a no-op once already applied to the db file.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            designation TEXT,
            section TEXT,               -- department / counter / section
            date_of_joining TEXT,
            pf_number TEXT,
            esi_number TEXT,
            bank_name TEXT,
            account_number TEXT,
            state TEXT DEFAULT 'Tamil Nadu',   -- drives Professional Tax slab
            pf_applicable INTEGER NOT NULL DEFAULT 1,
            esi_applicable INTEGER NOT NULL DEFAULT 1,
            basic_salary REAL NOT NULL DEFAULT 0,
            vc_per_day REAL NOT NULL DEFAULT 0,     -- "V C" per-day rate
            sa_per_day REAL NOT NULL DEFAULT 0,      -- "S A" per-day rate
            ta_per_day REAL NOT NULL DEFAULT 0,      -- travel allowance per day
            c_per_day_amt REAL NOT NULL DEFAULT 0,   -- calendar incentive per day rate
            weekly_offs REAL NOT NULL DEFAULT 4,     -- used to default payable days/month
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_pay (
            mp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            month TEXT NOT NULL,          -- format YYYY-MM

            -- attendance
            payable_days REAL NOT NULL DEFAULT 0,
            present_days REAL NOT NULL DEFAULT 0,
            leave_days REAL NOT NULL DEFAULT 0,
            absent_days REAL NOT NULL DEFAULT 0,
            c_p_d REAL NOT NULL DEFAULT 0,        -- calendar-scheme present days

            -- incentives (all optional, default 0)
            gold_incentive REAL NOT NULL DEFAULT 0,
            silver_incentive REAL NOT NULL DEFAULT 0,
            diamond_incentive REAL NOT NULL DEFAULT 0,
            sales_incentive REAL NOT NULL DEFAULT 0,
            chit_incentive REAL NOT NULL DEFAULT 0,
            mor_lun_incentive REAL NOT NULL DEFAULT 0,
            crm_incentive REAL NOT NULL DEFAULT 0,
            ew_hours_incentive REAL NOT NULL DEFAULT 0,
            uniform_return_amt REAL NOT NULL DEFAULT 0,
            urd_incentive REAL NOT NULL DEFAULT 0,
            lms REAL NOT NULL DEFAULT 0,
            bonus REAL NOT NULL DEFAULT 0,
            other_incentive REAL NOT NULL DEFAULT 0,

            -- fines / deductions
            morning_late_deduction REAL NOT NULL DEFAULT 0,
            lunch_late_deduction REAL NOT NULL DEFAULT 0,
            permission_deduction REAL NOT NULL DEFAULT 0,
            uniform_deposit REAL NOT NULL DEFAULT 0,
            advance REAL NOT NULL DEFAULT 0,
            other_deduction REAL NOT NULL DEFAULT 0,

            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            UNIQUE(emp_id, month)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payroll_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            per_day_salary REAL,
            lop_days REAL,
            ew_days REAL,
            ewd_incentive REAL,
            gross_salary REAL,
            calendar_incentive REAL,
            vc_value REAL,
            sa_value REAL,
            ta_value REAL,
            total_addition REAL,
            absent_penalty REAL,
            ew_deduction REAL,
            pf_employee REAL,
            esi_employee REAL,
            professional_tax REAL,
            income_tax REAL,
            total_deduction REAL,
            net_salary REAL,
            generated_on TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            UNIQUE(emp_id, month)
        )
    """)

    # New, standalone module: daily attendance marking. Independent of
    # monthly_pay - nothing existing reads or writes this table. The
    # Monthly Pay tab can optionally pull a summary from it via
    # get_month_attendance_summary(), but manual entry keeps working
    # exactly as before regardless of whether this table has data.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_attendance (
            att_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            att_date TEXT NOT NULL,     -- format YYYY-MM-DD
            status TEXT NOT NULL,       -- P=Present A=Absent L=Leave W=Week Off H=Holiday
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            UNIQUE(emp_id, att_date)
        )
    """)

    # New, standalone module: employee documents (photo, Aadhaar, PAN,
    # other ID proofs). Independent of every other table except a link
    # back to the employee it belongs to.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employee_documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL,        -- Photo / Aadhaar Card / PAN Card / Other ID Proof
            label TEXT,                    -- optional free-text note (e.g. "Driving License")
            file_path TEXT NOT NULL,       -- path relative to the app folder
            original_filename TEXT,
            uploaded_on TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
    """)

    # ---- Users (login + password change module) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            must_change_password INTEGER NOT NULL DEFAULT 0
        )
    """)
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        salt, pwd_hash = _hash_password(DEFAULT_PASSWORD)
        cur.execute(
            "INSERT INTO users (username, role, salt, password_hash, must_change_password) "
            "VALUES (?, ?, ?, ?, 1)",
            (DEFAULT_USERNAME, DEFAULT_ROLE, salt, pwd_hash),
        )

    # ---- Migration: PF/ESI wage-base override columns on employees ----
    # Added so the exact PF/ESI wage base your company actually uses (which
    # may differ from a plain Basic/Gross figure - see README) can be
    # entered per employee instead of guessed. Leave at 0 to fall back to
    # the standard basis (Basic Salary for PF, Total Addition for ESI).
    cur.execute("PRAGMA table_info(employees)")
    existing_cols = {row[1] for row in cur.fetchall()}
    if "pf_wage" not in existing_cols:
        cur.execute("ALTER TABLE employees ADD COLUMN pf_wage REAL NOT NULL DEFAULT 0")
    if "esi_wage" not in existing_cols:
        cur.execute("ALTER TABLE employees ADD COLUMN esi_wage REAL NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()


# ---------------- Password hashing (used by users table) ----------------

def _hash_password(password: str, salt_hex: str = None):
    salt = binascii.unhexlify(salt_hex) if salt_hex else secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return binascii.hexlify(salt).decode(), binascii.hexlify(pwd_hash).decode()


def _verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    _, computed = _hash_password(password, salt_hex)
    return secrets.compare_digest(computed, expected_hash_hex)


# ---------------- Users / auth ----------------

def get_user(username: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def verify_login(username: str, password: str):
    """Returns the user dict (with role) on success, or None on failure."""
    user = get_user((username or "").strip())
    if not user:
        return None
    if _verify_password(password or "", user["salt"], user["password_hash"]):
        return user
    return None


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Verifies old_password, then sets new_password. Returns False if the
    old password didn't match (nothing is changed in that case)."""
    user = get_user(username)
    if not user or not _verify_password(old_password or "", user["salt"], user["password_hash"]):
        return False
    salt, pwd_hash = _hash_password(new_password)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET salt=?, password_hash=?, must_change_password=0 WHERE username=?",
        (salt, pwd_hash, username),
    )
    conn.commit()
    conn.close()
    return True


# ---------------- Employee CRUD ----------------

EMP_FIELDS = [
    "emp_code", "name", "designation", "section", "date_of_joining",
    "pf_number", "esi_number", "bank_name", "account_number", "state",
    "basic_salary", "vc_per_day", "sa_per_day", "ta_per_day",
    "c_per_day_amt", "weekly_offs", "pf_applicable", "esi_applicable",
    "pf_wage", "esi_wage",
]


def _emp_values(data: dict):
    return (
        data["emp_code"], data["name"], data.get("designation", ""),
        data.get("section", ""), data.get("date_of_joining", ""),
        data.get("pf_number", ""), data.get("esi_number", ""),
        data.get("bank_name", ""), data.get("account_number", ""),
        data.get("state", "Tamil Nadu"),
        float(data.get("basic_salary", 0) or 0),
        float(data.get("vc_per_day", 0) or 0),
        float(data.get("sa_per_day", 0) or 0),
        float(data.get("ta_per_day", 0) or 0),
        float(data.get("c_per_day_amt", 0) or 0),
        float(data.get("weekly_offs", 4) or 0),
        int(data.get("pf_applicable", 1)), int(data.get("esi_applicable", 1)),
        float(data.get("pf_wage", 0) or 0),
        float(data.get("esi_wage", 0) or 0),
    )


def add_employee(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO employees ({', '.join(EMP_FIELDS)})
        VALUES ({', '.join(['?'] * len(EMP_FIELDS))})
    """, _emp_values(data))
    conn.commit()
    emp_id = cur.lastrowid
    conn.close()
    return emp_id


def update_employee(emp_id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    set_clause = ', '.join(f"{f}=?" for f in EMP_FIELDS)
    cur.execute(f"UPDATE employees SET {set_clause} WHERE emp_id=?",
                _emp_values(data) + (emp_id,))
    conn.commit()
    conn.close()


def deactivate_employee(emp_id: int):
    conn = get_connection()
    conn.execute("UPDATE employees SET active=0 WHERE emp_id=?", (emp_id,))
    conn.commit()
    conn.close()


def reactivate_employee(emp_id: int):
    conn = get_connection()
    conn.execute("UPDATE employees SET active=1 WHERE emp_id=?", (emp_id,))
    conn.commit()
    conn.close()


def get_all_employees(active_only=True):
    conn = get_connection()
    if active_only:
        rows = conn.execute("SELECT * FROM employees WHERE active=1 ORDER BY name").fetchall()
    else:
        rows = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_employee(emp_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- Monthly pay input ----------------

MONTHLY_FIELDS = [
    "payable_days", "present_days", "leave_days", "absent_days", "c_p_d",
    "gold_incentive", "silver_incentive", "diamond_incentive", "sales_incentive",
    "chit_incentive", "mor_lun_incentive", "crm_incentive", "ew_hours_incentive",
    "uniform_return_amt", "urd_incentive", "lms", "bonus", "other_incentive",
    "morning_late_deduction", "lunch_late_deduction", "permission_deduction",
    "uniform_deposit", "advance", "other_deduction",
]


def upsert_monthly_pay(emp_id: int, month: str, data: dict):
    conn = get_connection()
    values = [float(data.get(f, 0) or 0) for f in MONTHLY_FIELDS]
    cols = ', '.join(MONTHLY_FIELDS)
    placeholders = ', '.join(['?'] * len(MONTHLY_FIELDS))
    update_clause = ', '.join(f"{f}=excluded.{f}" for f in MONTHLY_FIELDS)
    conn.execute(f"""
        INSERT INTO monthly_pay (emp_id, month, {cols})
        VALUES (?, ?, {placeholders})
        ON CONFLICT(emp_id, month) DO UPDATE SET {update_clause}
    """, [emp_id, month] + values)
    conn.commit()
    conn.close()


def get_monthly_pay(emp_id: int, month: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM monthly_pay WHERE emp_id=? AND month=?", (emp_id, month)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- Payroll runs ----------------

RUN_FIELDS = [
    "per_day_salary", "lop_days", "ew_days", "ewd_incentive", "gross_salary",
    "calendar_incentive", "vc_value", "sa_value", "ta_value", "total_addition",
    "absent_penalty", "ew_deduction", "pf_employee", "esi_employee",
    "professional_tax", "income_tax", "total_deduction", "net_salary",
]


def save_payroll_run(emp_id: int, month: str, result: dict, generated_on: str):
    conn = get_connection()
    values = [result[f] for f in RUN_FIELDS]
    cols = ', '.join(RUN_FIELDS)
    placeholders = ', '.join(['?'] * len(RUN_FIELDS))
    update_clause = ', '.join(f"{f}=excluded.{f}" for f in RUN_FIELDS)
    conn.execute(f"""
        INSERT INTO payroll_runs (emp_id, month, {cols}, generated_on)
        VALUES (?, ?, {placeholders}, ?)
        ON CONFLICT(emp_id, month) DO UPDATE SET {update_clause}, generated_on=excluded.generated_on
    """, [emp_id, month] + values + [generated_on])
    conn.commit()
    conn.close()


def get_payroll_runs_for_month(month: str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT pr.*, e.name, e.emp_code, e.section
        FROM payroll_runs pr JOIN employees e ON pr.emp_id = e.emp_id
        WHERE pr.month=? ORDER BY e.name
    """, (month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_payroll_runs_for_month_with_bank_details(month: str):
    """Same as get_payroll_runs_for_month, but also carries the employee
    fields the Accounts department needs to actually disburse salaries
    (bank name, account number, PF/ESI numbers, designation). Used by
    salary_payable_export.py."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT pr.*,
               e.name, e.emp_code, e.section, e.designation,
               e.bank_name, e.account_number, e.pf_number, e.esi_number
        FROM payroll_runs pr JOIN employees e ON pr.emp_id = e.emp_id
        WHERE pr.month=? ORDER BY e.name
    """, (month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_payroll_history(emp_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM payroll_runs WHERE emp_id=? ORDER BY month DESC", (emp_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- Summaries (Dashboard) ----------------

def get_month_totals(month: str):
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*) as headcount,
               COALESCE(SUM(total_addition), 0) as gross,
               COALESCE(SUM(pf_employee), 0) as pf,
               COALESCE(SUM(esi_employee), 0) as esi,
               COALESCE(SUM(professional_tax), 0) as pt,
               COALESCE(SUM(income_tax), 0) as tax,
               COALESCE(SUM(total_deduction), 0) as total_deduction,
               COALESCE(SUM(net_salary), 0) as net
        FROM payroll_runs WHERE month=?
    """, (month,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_designation_totals(active_only: bool = True):
    """Headcount (+ basic-salary totals) grouped by designation, from the
    employees master table directly - so it's available even before any
    payroll has been run for a month. Blank designations are grouped
    under 'Unspecified'. Ordered by headcount, largest first."""
    conn = get_connection()
    where = "WHERE active=1" if active_only else ""
    rows = conn.execute(f"""
        SELECT COALESCE(NULLIF(TRIM(designation), ''), 'Unspecified') as designation,
               COUNT(*) as headcount,
               COALESCE(SUM(basic_salary), 0) as total_basic,
               COALESCE(AVG(basic_salary), 0) as avg_basic
        FROM employees
        {where}
        GROUP BY COALESCE(NULLIF(TRIM(designation), ''), 'Unspecified')
        ORDER BY headcount DESC, designation ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_section_totals(month: str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT COALESCE(NULLIF(e.section, ''), 'Unassigned') as section,
               COUNT(*) as headcount,
               COALESCE(SUM(pr.total_addition), 0) as gross,
               COALESCE(SUM(pr.net_salary), 0) as net
        FROM payroll_runs pr JOIN employees e ON pr.emp_id = e.emp_id
        WHERE pr.month=?
        GROUP BY section
        ORDER BY gross DESC
    """, (month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- Daily Attendance (new module) ----------------
# Independent of monthly_pay. Nothing existing depends on this table -
# it only feeds an optional "Load From Attendance" convenience button
# on the Monthly Pay tab.

ATTENDANCE_STATUSES = {
    "P": "Present",
    "A": "Absent",
    "L": "Leave",
    "W": "Week Off",
    "H": "Holiday",
}


def mark_attendance(emp_id: int, att_date: str, status: str):
    """Set (or overwrite) one employee's status for one date."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO daily_attendance (emp_id, att_date, status)
        VALUES (?, ?, ?)
        ON CONFLICT(emp_id, att_date) DO UPDATE SET status=excluded.status
    """, (emp_id, att_date, status))
    conn.commit()
    conn.close()


def clear_attendance(emp_id: int, att_date: str):
    """Remove a single day's record (used when a cell is set back to
    'Not Marked')."""
    conn = get_connection()
    conn.execute("DELETE FROM daily_attendance WHERE emp_id=? AND att_date=?",
                 (emp_id, att_date))
    conn.commit()
    conn.close()


def bulk_mark_attendance(att_date: str, status_by_emp: dict):
    """status_by_emp: {emp_id: status_code}. Upserts one date for many
    employees in a single transaction - used by the Daily Register view.
    Employees mapped to an empty status ('') have their record cleared
    instead (so un-marking a day actually removes it)."""
    conn = get_connection()
    cur = conn.cursor()
    for emp_id, status in status_by_emp.items():
        if status:
            cur.execute("""
                INSERT INTO daily_attendance (emp_id, att_date, status)
                VALUES (?, ?, ?)
                ON CONFLICT(emp_id, att_date) DO UPDATE SET status=excluded.status
            """, (emp_id, att_date, status))
        else:
            cur.execute("DELETE FROM daily_attendance WHERE emp_id=? AND att_date=?",
                        (emp_id, att_date))
    conn.commit()
    conn.close()


def get_attendance_for_date(att_date: str) -> dict:
    """Returns {emp_id: status_code} for every employee with a marked
    record on att_date."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT emp_id, status FROM daily_attendance WHERE att_date=?", (att_date,)
    ).fetchall()
    conn.close()
    return {r["emp_id"]: r["status"] for r in rows}


def get_attendance_for_month(emp_id: int, month: str) -> dict:
    """Returns {day_number(int): status_code} for one employee/month."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT att_date, status FROM daily_attendance WHERE emp_id=? AND att_date LIKE ?",
        (emp_id, f"{month}-%")
    ).fetchall()
    conn.close()
    result = {}
    for r in rows:
        day = int(r["att_date"][-2:])
        result[day] = r["status"]
    return result


def get_month_attendance_summary(emp_id: int, month: str):
    """Aggregates a month's daily_attendance rows into the counts the
    Monthly Pay tab's fields need. payable_days = every marked day that
    isn't a week-off (present + leave + absent + holiday), matching the
    'days owed' convention used elsewhere in the app.
    Returns None if nothing has been marked yet for this employee/month -
    callers should leave manual entry untouched in that case."""
    day_map = get_attendance_for_month(emp_id, month)
    if not day_map:
        return None
    present = sum(1 for s in day_map.values() if s == "P")
    leave = sum(1 for s in day_map.values() if s == "L")
    absent = sum(1 for s in day_map.values() if s == "A")
    week_off = sum(1 for s in day_map.values() if s == "W")
    holiday = sum(1 for s in day_map.values() if s == "H")
    payable = present + leave + absent + holiday
    return {
        "present_days": present, "leave_days": leave, "absent_days": absent,
        "week_off_days": week_off, "holiday_days": holiday,
        "payable_days": payable, "days_marked": len(day_map),
    }


# ---------------- Employee Documents (new module) ----------------
# Photo / Aadhaar / PAN / other ID proofs. Independent of every other
# table; file bytes live on disk (see main.py's DOCS_DIR), only the
# path and metadata are stored here.

DOCUMENT_TYPES = ["Photo", "Aadhaar Card", "PAN Card", "Other ID Proof"]


def add_employee_document(emp_id: int, doc_type: str, label: str, file_path: str,
                           original_filename: str, uploaded_on: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO employee_documents
            (emp_id, doc_type, label, file_path, original_filename, uploaded_on)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (emp_id, doc_type, label or "", file_path, original_filename, uploaded_on))
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id


def get_documents_for_employee(emp_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM employee_documents WHERE emp_id=? ORDER BY uploaded_on DESC",
        (emp_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM employee_documents WHERE doc_id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_employee_document(doc_id: int):
    """Removes the DB record only - callers should delete the underlying
    file on disk themselves (see main.py) before or after calling this."""
    conn = get_connection()
    conn.execute("DELETE FROM employee_documents WHERE doc_id=?", (doc_id,))
    conn.commit()
    conn.close()


def get_document_counts_for_employees() -> dict:
    """Returns {emp_id: document_count} for every employee that has at
    least one uploaded document - used to show a quick indicator."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT emp_id, COUNT(*) as cnt FROM employee_documents GROUP BY emp_id"
    ).fetchall()
    conn.close()
    return {r["emp_id"]: r["cnt"] for r in rows}
