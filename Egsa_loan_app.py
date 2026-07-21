import streamlit as st
import sqlite3
import pandas as pd

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="EGSA Loan Management System",
    page_icon="💰",
    layout="wide"
)

DB_NAME = "loan_applications.db"

ADMIN_PASSWORD = "admin123"

# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():

    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# =====================================================
# CREATE TABLE
# =====================================================

def init_db():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT,

        national_id TEXT,

        phone TEXT,

        staff_status TEXT,

        monthly_salary REAL,

        loan_amount REAL,

        duration INTEGER,

        interest_rate REAL,

        interest_amount REAL,

        monthly_payment REAL,

        total_payment REAL,

        repayment_date TEXT,

        loan_end_date TEXT,

        guarantor_name TEXT,

        guarantor_id TEXT,

        guarantor_phone TEXT,

        support_letter BLOB,

        photo BLOB,

        submitted_date TEXT,

        status TEXT DEFAULT 'Pending',

        admin_comment TEXT,

        notified INTEGER DEFAULT 0

    )
    """)

    conn.commit()

    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

conn = init_db()

# =====================================================
# LOAN FUNCTIONS
# =====================================================

def determine_interest_rate(months):

    if months <= 3:
        return 20

    elif months <= 6:
        return 25

    elif months <= 9:
        return 30

    elif months <= 12:
        return 35

    elif months <= 36:
        return 40

    else:
        return 45


def calculate_loan(amount, months):

    rate = determine_interest_rate(months)

    if amount <= 0:
        return rate, 0, 0, 0

    monthly_rate = rate / 100 / 12

    monthly_payment = (
        amount *
        monthly_rate *
        (1 + monthly_rate) ** months
    ) / (
        (1 + monthly_rate) ** months - 1
    )

    total_payment = monthly_payment * months

    interest_amount = total_payment - amount

    return (
        rate,
        interest_amount,
        monthly_payment,
        total_payment
    )


# =====================================================
# SAVE APPLICATION
# =====================================================

def save_application(data):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO applications(

            full_name,
            national_id,
            phone,
            staff_status,
            monthly_salary,
            loan_amount,
            duration,
            interest_rate,
            interest_amount,
            monthly_payment,
            total_payment,
            repayment_date,
            loan_end_date,
            guarantor_name,
            guarantor_id,
            guarantor_phone,
            support_letter,
            photo,
            submitted_date,
            status,
            admin_comment,
            notified

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,
            ?,?,?,?,?,?,?,?,?,?,
            ?,?

        )
    """, (

        data["full_name"],
        data["national_id"],
        data["phone"],
        data["staff_status"],
        data["monthly_salary"],
        data["loan_amount"],
        data["duration"],
        data["interest_rate"],
        data["interest_amount"],
        data["monthly_payment"],
        data["total_payment"],
        data["repayment_date"],
        data["loan_end_date"],
        data["guarantor_name"],
        data["guarantor_id"],
        data["guarantor_phone"],
        data["support_letter"],
        data["photo"],
        data["submitted_date"],
        "Pending",
        "",
        0

    ))

    conn.commit()
    conn.close()


# =====================================================
# GET APPLICATIONS
# =====================================================

def get_applications(status="All"):

    conn = get_connection()

    query = """
        SELECT *
        FROM applications
    """

    params = ()

    if status != "All":

        query += " WHERE status=?"

        params = (status,)

    query += " ORDER BY submitted_date DESC"

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


# =====================================================
# UPDATE STATUS
# =====================================================

def update_status(application_id, status, comment):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

        UPDATE applications

        SET

            status=?,
            admin_comment=?

        WHERE id=?

    """,

    (

        status,
        comment,
        application_id

    ))

    conn.commit()

    conn.close()


# =====================================================
# DELETE APPLICATION
# =====================================================

def delete_application(application_id):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(

        "DELETE FROM applications WHERE id=?",

        (application_id,)

    )

    conn.commit()

    conn.close()


# =====================================================
# SIDEBAR MENU
# =====================================================

st.sidebar.title("💰 EGSA Loan System")

page = st.sidebar.radio(

    "Select Menu",

    [

        "Apply for Loan",

        "Admin Dashboard",

        "Loan Calculator"

    ]

)


# =====================================================
# APPLY FOR LOAN
# =====================================================

if page == "Apply for Loan":

    st.title("💰 EGSA Loan Application")

    st.write("Complete all information below.")

# =====================================================
# ADMIN DASHBOARD
# =====================================================

elif page == "Admin Dashboard":

    st.title("📊 EGSA Loan Admin Dashboard")




# =====================================================
# LOAN CALCULATOR
# =====================================================

elif page == "Loan Calculator":

    st.title("🧮 Loan Calculator")

