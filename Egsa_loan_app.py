# -------------------------------
# streamlit_Egsa_loan_app.py
# Final Version – Oct 2025
# Includes: Loan App + Guarantee + Photo Upload + Admin Dashboard + Calculator
# -------------------------------

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta

# ---------- CONFIG ----------
DB_PATH = "loan_applications.db"
ADMIN_PASSWORD = "admin123"  # Change before deployment

# ---------- DB HELPERS ----------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            national_id TEXT,
            staff_status TEXT,
            monthly_salary REAL,
            loan_amount REAL,
            interest REAL,
            total_to_repay REAL,
            repayment_date TEXT,
            guarantor_name TEXT,
            guarantor_id TEXT,
            guarantor_phone TEXT,
            submitted_date TEXT,
            status TEXT DEFAULT 'Pending',
            admin_comment TEXT,
            notified INTEGER DEFAULT 0,
            support_letter BLOB,
            photo BLOB
        )
    """)
    conn.commit()
    return conn

def insert_application(conn, data: dict):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO applications
        (name, national_id, staff_status, monthly_salary, loan_amount, interest, total_to_repay,
         repayment_date, guarantor_name, guarantor_id, guarantor_phone, submitted_date, status,
         admin_comment, notified, support_letter, photo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data['name'], data['national_id'], data['staff_status'], data['monthly_salary'], data['loan_amount'],
        data['interest'], data['total_to_repay'], data['repayment_date'], data['guarantor_name'],
        data['guarantor_id'], data['guarantor_phone'], data['submitted_date'], "Pending", "", 0,
        data['support_letter'], data['photo']
    ))
    conn.commit()

def get_applications(conn, status=None):
    cur = conn.cursor()
    if status and status != "All":
        cur.execute("SELECT * FROM applications WHERE status = ? ORDER BY submitted_date DESC", (status,))
    else:
        cur.execute("SELECT * FROM applications ORDER BY submitted_date DESC")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(rows, columns=cols)

def update_status(conn, app_id, new_status, comment=""):
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = ?, admin_comment = ?, notified = 0 WHERE id = ?", 
                (new_status, comment, app_id))
    conn.commit()

def mark_notified(conn, app_id):
    cur = conn.cursor()
    cur.execute("UPDATE applications SET notified = 1 WHERE id = ?", (app_id,))
    conn.commit()

# ---------- SAFE RERUN ----------
def safe_rerun():
    st.session_state["refresh"] = True

if st.session_state.get("refresh"):
    st.session_state["refresh"] = False
    st.rerun()

# ---------- STREAMLIT PAGE ----------
st.set_page_config(page_title="Loan Application System", layout="wide")
conn = init_db()

st.title("Loan Application System (For EGSA Members)")

pages = ["Apply for Loan", "Admin Dashboard", "Loan Calculator"]
page = st.sidebar.selectbox("Go to", pages)

# -------------------------------
# 1️⃣ Loan Application Form
# -------------------------------
if page == "Apply for Loan":
    st.header("Loan Application Form")
    st.write("Fill out all required fields and submit your application.")

    with st.form("loan_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        national_id = st.text_input("National ID")
        staff_status = st.selectbox("Staff Status", ["Active", "Inactive", "Contractor", "Other"])
        monthly_salary = st.number_input("Monthly Salary", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        loan_amount = st.number_input("Loan Amount Requested", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        interest = st.number_input("Interest (amount or percent)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
        total_to_repay = st.number_input("Total to Repay", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        repayment_date = st.date_input("Repayment Date", value=date.today() + timedelta(days=30))
        guarantor_name = st.text_input("Guarantor Name")
        guarantor_id = st.text_input("Guarantor ID")
        guarantor_phone = st.text_input("Guarantor Phone")
        submitted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Uploads
        st.markdown("### Upload Documents")
        support_letter_file = st.file_uploader("Organization Support / Salary Letter (PDF or Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
        photo_file = st.file_uploader("Your Photo", type=['png', 'jpg', 'jpeg'])

        # Loan Guarantee Agreement
        st.subheader("Loan Guarantee and Borrower Agreement")
        st.markdown("""
I, the Guarantor, jointly and severally guarantee repayment of the Borrower’s loan, including interest and related charges.  
EGSA may recover the loan directly from the Guarantor if the Borrower defaults.  
This guarantee remains in effect until the loan is fully repaid.  
No delay or forbearance by EGSA shall waive any of its rights.
""")
        agree = st.checkbox("I have read and agree to the Loan Guarantee and Borrower Agreement")

        submitted = st.form_submit_button("Submit Application")

        if submitted:
            if not agree:
                st.error("You must agree to the Loan Guarantee and Borrower Agreement before submitting.")
            elif support_letter_file is None or photo_file is None:
                st.error("Please upload both support letter and photo.")
            else:
                data = dict(
                    name=name,
                    national_id=national_id,
                    staff_status=staff_status,
                    monthly_salary=monthly_salary,
                    loan_amount=loan_amount,
                    interest=interest,
                    total_to_repay=total_to_repay,
                    repayment_date=repayment_date.strftime("%Y-%m-%d"),
                    guarantor_name=guarantor_name,
                    guarantor_id=guarantor_id,
                    guarantor_phone=guarantor_phone,
                    submitted_date=submitted_date,
                    support_letter=support_letter_file.read(),
                    photo=photo_file.read()
                )
                insert_application(conn, data)
                st.success("✅ Application submitted successfully. Admin will review your documents.")

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
# 3️⃣ Loan Calculator
# -------------------------------
elif page == "Loan Calculator":
    st.subheader("📋 Loan Calculator (Dynamic Interest)")

    def determine_interest_rate(months):
        if months <= 3: return 20
        elif months <= 6: return 25
        elif months <= 9: return 30
        elif months <= 12: return 35
        elif months <= 36: return 40
        else: return 45

    col1, col2 = st.columns(2)
    with col1:
        loan_amount_calc = st.number_input("Loan Amount", min_value=0.0, step=100.0)
        duration = st.number_input("Duration (months)", min_value=1, step=1)
    with col2:
        interest_rate = determine_interest_rate(duration)
        monthly_rate = interest_rate / 100 / 12
        if loan_amount_calc > 0 and duration > 0:
            monthly_payment = (loan_amount_calc * monthly_rate * (1 + monthly_rate) ** duration) / ((1 + monthly_rate) ** duration - 1)
            total_payment = monthly_payment * duration
        else:
            monthly_payment, total_payment = 0.0, 0.0

        st.write(f"💰 **Interest Rate:** {interest_rate}%")
        st.write(f"📆 **Monthly Payment:** {monthly_payment:.2f}")
        st.write(f"💵 **Total Payment:** {total_payment:.2f}")
