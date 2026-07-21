import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta

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
# DATABASE
# =====================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


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


conn = init_db()

# =====================================================
# FUNCTIONS
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

    monthly_rate = rate / 100 / 12

    if amount <= 0:

        return rate,0,0,0

    monthly_payment = (

        amount

        * monthly_rate

        * (1 + monthly_rate) ** months

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

    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?

    )

    """,(

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
# SIDEBAR
# =====================================================

page = st.sidebar.selectbox(

    "Menu",

    [

        "Apply for Loan",

        "Admin Dashboard",

        "Loan Calculator"

    ]

)

# =====================================================
# LOAN APPLICATION
# =====================================================

if page=="Apply for Loan":

    st.title("💰 EGSA Loan Application")

    st.write("Complete all information below.")

    # -----------------------------
    # Personal Information
    # -----------------------------

    st.subheader("Personal Information")

    full_name = st.text_input("Full Name")

    national_id = st.text_input("National ID")

    phone = st.text_input("Phone Number")

    staff_status = st.selectbox(
        "Staff Status",
        [
            "Permanent",
            "Contract",
            "Temporary",
            "Other"
        ]
    )

    monthly_salary = st.number_input(
        "Monthly Salary",
        min_value=0.0,
        step=100.0
    )


    st.divider()


    # -----------------------------
# Loan Information
# -----------------------------

st.subheader("Loan Information")


loan_amount = st.number_input(
    "Loan Amount",
    min_value=0.0,
    value=0.0,
    step=100.0,
    key="loan_amount_input"
)


duration = st.number_input(
    "Loan Duration (Months)",
    min_value=1,
    max_value=60,
    value=12,
    step=1,
    key="loan_duration_input"
)


# Convert values
loan_amount = float(loan_amount)
duration = int(duration)


# Calculate Loan
interest_rate, interest_amount, monthly_payment, total_payment = calculate_loan(
    loan_amount,
    duration
)


st.success(
    f"Interest Rate : {interest_rate}%"
)


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "Interest Amount",
        f"{interest_amount:,.2f} ETB"
    )


    st.metric(
        "Monthly Payment",
        f"{monthly_payment:,.2f} ETB"
    )


with col2:

    st.metric(
        "Loan Amount",
        f"{loan_amount:,.2f} ETB"
    )


    st.metric(
        "Total Repayment",
        f"{total_payment:,.2f} ETB"
    )


# -----------------------------
# Loan Eligibility Check
# -----------------------------

max_payment = monthly_salary * 0.40


if monthly_salary > 0:

    if monthly_payment <= max_payment:

        st.success(
            "✅ Eligible for Loan"
        )

    else:

        st.error(
            f"❌ Monthly payment exceeds 40% of salary. "
            f"Maximum allowed: {max_payment:,.2f} ETB"
        )


# -----------------------------
# Repayment Date
# -----------------------------

repayment_date = st.date_input(
    "Repayment Start Date",
    value=date.today()+timedelta(days=30)
)
    st.divider()


    # -----------------------------
    # Guarantor
    # -----------------------------

    st.subheader("Guarantor")


    guarantor_name = st.text_input(
        "Guarantor Name"
    )


    guarantor_id = st.text_input(
        "Guarantor National ID"
    )


    guarantor_phone = st.text_input(
        "Guarantor Phone"
    )


    st.divider()


    # -----------------------------
    # Documents
    # -----------------------------

    st.subheader("Upload Documents")


    support_letter = st.file_uploader(
        "Support Letter",
        type=["pdf","jpg","jpeg","png"]
    )


    photo = st.file_uploader(
        "Passport Photo",
        type=["jpg","jpeg","png"]
    )


    st.divider()


    agree = st.checkbox(
        "I agree with the Loan Guarantee Agreement."
    )


    submit = st.button(
        "Submit Application"
    )


    if submit:


        if not agree:

            st.error(
                "Please accept the agreement."
            )


        elif support_letter is None:

            st.error(
                "Upload support letter."
            )


        elif photo is None:

            st.error(
                "Upload passport photo."
            )


        elif monthly_payment > max_payment:

            st.error(
                "Loan is not eligible."
            )


        else:


            data={

                "full_name":full_name,

                "national_id":national_id,

                "phone":phone,

                "staff_status":staff_status,

                "monthly_salary":monthly_salary,

                "loan_amount":loan_amount,

                "duration":duration,

                "interest_rate":interest_rate,

                "interest_amount":interest_amount,

                "monthly_payment":monthly_payment,

                "total_payment":total_payment,

                "repayment_date":repayment_date.strftime("%Y-%m-%d"),

                "guarantor_name":guarantor_name,

                "guarantor_id":guarantor_id,

                "guarantor_phone":guarantor_phone,

                "support_letter":support_letter.read(),

                "photo":photo.read(),

                "submitted_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            }


            save_application(data)


            st.success(
                "🎉 Loan application submitted successfully."
            )
        st.divider()

        st.subheader("Guarantor")

        guarantor_name = st.text_input("Guarantor Name")

        guarantor_id = st.text_input("Guarantor National ID")

        guarantor_phone = st.text_input("Guarantor Phone")

        st.divider()

        st.subheader("Upload Documents")

        support_letter = st.file_uploader(

            "Support Letter",

            type=["pdf","jpg","jpeg","png"]

        )

        photo = st.file_uploader(

            "Passport Photo",

            type=["jpg","jpeg","png"]

        )

        st.divider()

        agree = st.checkbox(

            "I agree with the Loan Guarantee Agreement."

        )

        submit = st.form_submit_button(

            "Submit Application"

        )

        if submit:

            if not agree:

                st.error("Please accept the agreement.")

            elif support_letter is None:

                st.error("Upload support letter.")

            elif photo is None:

                st.error("Upload passport photo.")

            elif monthly_payment>max_payment:

                st.error("Loan is not eligible.")

            else:

                data={

                    "full_name":full_name,

                    "national_id":national_id,

                    "phone":phone,

                    "staff_status":staff_status,

                    "monthly_salary":monthly_salary,

                    "loan_amount":loan_amount,

                    "duration":duration,

                    "interest_rate":interest_rate,

                    "interest_amount":interest_amount,

                    "monthly_payment":monthly_payment,

                    "total_payment":total_payment,

                    "repayment_date":repayment_date.strftime("%Y-%m-%d"),

                    "guarantor_name":guarantor_name,

                    "guarantor_id":guarantor_id,

                    "guarantor_phone":guarantor_phone,

                    "support_letter":support_letter.read(),

                    "photo":photo.read(),

                    "submitted_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                }

                save_application(data)

                st.success("🎉 Loan application submitted successfully.")

# -------------------------------
# 2️⃣ Admin Dashboard
# -------------------------------
elif page == "Admin Dashboard":
    st.header("Admin Dashboard")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        pw = st.text_input("Enter admin password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("Logged in as admin.")
                st.rerun()
            else:
                st.error("Wrong password.")
        st.stop()

    # Admin View
    col1, col2 = st.columns([3,1])
    with col1:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Approved", "Rejected"])
    with col2:
        if st.button("Refresh"):
            safe_rerun()

    df = get_applications(conn, status_filter)
    st.write(f"Total applications: {len(df)}")

    if df.empty:
        st.info("No applications found.")
    else:
        # Exclude binary columns (prevent Unicode errors)
        safe_df = df.drop(columns=['support_letter', 'photo'], errors='ignore')

        st.dataframe(
            safe_df.style.format({
                'monthly_salary': '{:,.2f}',
                'loan_amount': '{:,.2f}',
                'total_to_repay': '{:,.2f}'
            }),
            height=300
        )

        selected = st.selectbox("Select Application ID to manage", options=df['id'].tolist())
        app_row = df[df['id'] == selected].iloc[0]

        st.subheader(f"Application ID: {selected} — {app_row['name']}")
        st.write("**Submitted:**", app_row['submitted_date'])
        st.write("**National ID:**", app_row['national_id'])
        st.write("**Staff status:**", app_row['staff_status'])
        st.write("**Monthly salary:**", app_row['monthly_salary'])
        st.write("**Loan amount:**", app_row['loan_amount'])
        st.write("**Interest:**", app_row['interest'])
        st.write("**Total to repay:**", app_row['total_to_repay'])
        st.write("**Repayment date:**", app_row['repayment_date'])
        st.write("**Guarantor:**", app_row['guarantor_name'], "| ID:", app_row['guarantor_id'], "| Phone:", app_row['guarantor_phone'])
        st.write("**Status:**", app_row['status'])
        st.write("**Admin comment:**", app_row['admin_comment'] if app_row['admin_comment'] else "-")

        st.markdown("---")
        st.subheader("Uploaded Documents")
        if app_row['support_letter']:
            st.download_button(
                label="📄 Download Support Letter",
                data=app_row['support_letter'],
                file_name=f"support_letter_{selected}.pdf"
            )
        if app_row['photo']:
            st.image(app_row['photo'], caption="Applicant Photo", use_column_width=True)

        # Approve / Reject / Delete
        colA, colB, colC = st.columns(3)
        with colA:
            approve_comment = st.text_area("Comment before Approve", value="")
            if st.button("Approve"):
                update_status(conn, selected, "Approved", approve_comment)
                mark_notified(conn, selected)
                st.success("✅ Application Approved")
                safe_rerun()
        with colB:
            reject_comment = st.text_area("Comment before Reject", value="")
            if st.button("Reject"):
                update_status(conn, selected, "Rejected", reject_comment)
                mark_notified(conn, selected)
                st.warning("❌ Application Rejected")
                safe_rerun()
        with colC:
            if st.button("Delete Application"):
                cur = conn.cursor()
                cur.execute("DELETE FROM applications WHERE id = ?", (selected,))
                conn.commit()
                st.info("🗑️ Application Deleted")
                safe_rerun()

        csv = safe_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"applications_{status_filter}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# -------------------------------
with st.form("loan_form"):

    full_name = st.text_input("Full Name")

    national_id = st.text_input("National ID")

    phone = st.text_input("Phone Number")

    staff_status = st.selectbox(
        "Staff Status",
        [
            "Permanent",
            "Contract",
            "Temporary",
            "Other"
        ]
    )

    monthly_salary = st.number_input(
        "Monthly Salary",
        min_value=0.0,
        step=100.0
    )

    submitted = st.form_submit_button(
        "Submit Application"
    )
