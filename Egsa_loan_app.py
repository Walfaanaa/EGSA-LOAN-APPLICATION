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
# GET APPLICATIONS
# =====================================================

def get_applications(conn, status=None):

    cur = conn.cursor()

    if status and status != "All":

        cur.execute(
            """
            SELECT *
            FROM applications
            WHERE status = ?
            ORDER BY submitted_date DESC
            """,
            (status,)
        )

    else:

        cur.execute(
            """
            SELECT *
            FROM applications
            ORDER BY submitted_date DESC
            """
        )


    rows = cur.fetchall()

    columns = [
        description[0]
        for description in cur.description
    ]


    df = pd.DataFrame(
        rows,
        columns=columns
    )


    return df


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

if page == "Apply for Loan":

    st.title("💰 EGSA Loan Application")

    st.write("Complete all information below.")


    # -----------------------------
    # Personal Information
    # -----------------------------

    st.subheader("Personal Information")


    full_name = st.text_input(
        "Full Name"
    )


    national_id = st.text_input(
        "National ID"
    )


    phone = st.text_input(
        "Phone Number"
    )


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
        step=100.0
    )


    duration = st.number_input(
        "Loan Duration (Months)",
        min_value=1,
        max_value=60,
        value=12
    )


    interest_rate, interest_amount, monthly_payment, total_payment = calculate_loan(
        loan_amount,
        duration
    )


    st.success(
        f"Interest Rate : {interest_rate}%"
    )


    col1,col2 = st.columns(2)


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

max_payment = float(monthly_salary) * 0.40


if monthly_salary > 0:

    if monthly_payment <= max_payment:

        st.success(
            f"✅ Eligible for Loan\n\n"
            f"Maximum allowed monthly payment: {max_payment:,.2f} ETB"
        )

    else:

        st.error(
            f"❌ Loan is not eligible.\n\n"
            f"Monthly payment: {monthly_payment:,.2f} ETB\n"
            f"Maximum allowed: {max_payment:,.2f} ETB"
        )

    # -----------------------------
    # Repayment Date
    # -----------------------------

    repayment_date = st.date_input(
        "Repayment Start Date",
        value=date.today()+timedelta(days=30)
    )


    from dateutil.relativedelta import relativedelta


    loan_end_date = repayment_date + relativedelta(
        months=int(duration)
    )


    st.info(
        f"📅 Loan End Date: {loan_end_date.strftime('%Y-%m-%d')}"
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


            data = {

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
# -------------------------------
# -------------------------------
# 2️⃣ Admin Dashboard
# -------------------------------

elif page == "Admin Dashboard":

    st.header("📊 EGSA Loan Admin Dashboard")


    # -----------------------------
    # Admin Login
    # -----------------------------

    if "logged_in" not in st.session_state:

        st.session_state.logged_in = False



    if not st.session_state.logged_in:


        password = st.text_input(
            "Admin Password",
            type="password"
        )


        if st.button("🔐 Login"):


            if password == ADMIN_PASSWORD:


                st.session_state.logged_in = True

                st.success(
                    "✅ Admin Login Successful"
                )

                st.rerun()


            else:

                st.error(
                    "❌ Invalid Password"
                )


        st.stop()



    # -----------------------------
    # Filter
    # -----------------------------


    col1,col2 = st.columns([3,1])


    with col1:

        status_filter = st.selectbox(

            "Application Status",

            [
                "All",
                "Pending",
                "Approved",
                "Rejected"
            ]

        )


    with col2:

        if st.button("🔄 Refresh"):

            st.rerun()



    # -----------------------------
    # Get Applications
    # -----------------------------


    df = get_applications(
        conn,
        status_filter
    )


    st.info(
        f"Total Applications: {len(df)}"
    )



    if df.empty:


        st.warning(
            "No loan applications found."
        )



    else:


        # Hide uploaded files

        safe_df = df.drop(

            columns=[
                "support_letter",
                "photo"
            ],

            errors="ignore"

        )



        st.subheader(
            "📋 Loan Applications"
        )


        st.dataframe(

            safe_df.style.format({

                "monthly_salary":"{:,.2f}",

                "loan_amount":"{:,.2f}",

                "interest_amount":"{:,.2f}",

                "monthly_payment":"{:,.2f}",

                "total_payment":"{:,.2f}"

            }),

            use_container_width=True,

            height=400

        )



        # -----------------------------
        # Select Applicant
        # -----------------------------


        selected = st.selectbox(

            "Select Application",

            options=df["id"].tolist()

        )


        app_row = df[

            df["id"] == selected

        ].iloc[0]



        st.divider()


        st.subheader(
            f"📄 Application ID: {selected}"
        )



        col1,col2 = st.columns(2)



        with col1:


            st.write(
                "👤 Name:",
                app_row["full_name"]
            )


            st.write(
                "🆔 National ID:",
                app_row["national_id"]
            )


            st.write(
                "📞 Phone:",
                app_row["phone"]
            )


            st.write(
                "👷 Staff Status:",
                app_row["staff_status"]
            )


            st.write(
                "💰 Salary:",
                f"{app_row['monthly_salary']:,.2f} ETB"
            )



        with col2:


            st.write(
                "💵 Loan Amount:",
                f"{app_row['loan_amount']:,.2f} ETB"
            )


            st.write(
                "📆 Duration:",
                f"{app_row['duration']} Months"
            )


            st.write(
                "📈 Interest Rate:",
                f"{app_row['interest_rate']}%"
            )


            st.write(
                "💸 Interest Amount:",
                f"{app_row['interest_amount']:,.2f} ETB"
            )


            st.write(
                "📅 Monthly Payment:",
                f"{app_row['monthly_payment']:,.2f} ETB"
            )



        st.write(

            "💰 Total Repayment:",

            f"{app_row['total_payment']:,.2f} ETB"

        )



        st.write(

            "🗓 Start Date:",

            app_row["repayment_date"]

        )



        if "loan_end_date" in df.columns:


            st.write(

                "🏁 End Date:",

                app_row["loan_end_date"]

            )



        st.divider()



        # -----------------------------
        # Guarantor
        # -----------------------------


        st.subheader(
            "🤝 Guarantor Information"
        )


        st.write(

            "Name:",

            app_row["guarantor_name"]

        )


        st.write(

            "National ID:",

            app_row["guarantor_id"]

        )


        st.write(

            "Phone:",

            app_row["guarantor_phone"]

        )



        st.divider()



        # -----------------------------
        # Documents
        # -----------------------------


        st.subheader(
            "📂 Documents"
        )


        if app_row["support_letter"]:


            st.download_button(

                "📄 Download Support Letter",

                data=app_row["support_letter"],

                file_name=f"support_letter_{selected}.pdf"

            )



        if app_row["photo"]:


            st.image(

                app_row["photo"],

                caption="Applicant Photo",

                width=250

            )



        st.divider()



        # -----------------------------
        # Approval Control
        # -----------------------------


        colA,colB,colC = st.columns(3)



        with colA:


            approve_comment = st.text_area(
                "Approval Comment"
            )


            if st.button("✅ Approve Loan"):


                update_status(

                    conn,

                    selected,

                    "Approved",

                    approve_comment

                )


                st.success(
                    "Loan Approved"
                )


                st.rerun()



        with colB:


            reject_comment = st.text_area(
                "Reject Comment"
            )


            if st.button("❌ Reject Loan"):


                update_status(

                    conn,

                    selected,

                    "Rejected",

                    reject_comment

                )


                st.warning(
                    "Loan Rejected"
                )


                st.rerun()



        with colC:


            if st.button("🗑 Delete Application"):


                cur = conn.cursor()


                cur.execute(

                    "DELETE FROM applications WHERE id=?",

                    (selected,)

                )


                conn.commit()


                st.success(
                    "Deleted Successfully"
                )


                st.rerun()



        # -----------------------------
        # Export
        # -----------------------------


        csv = safe_df.to_csv(

            index=False

        ).encode("utf-8")



        st.download_button(

            "⬇️ Download Excel/CSV Report",

            data=csv,

            file_name=f"EGSA_Loan_Report_{datetime.now().strftime('%Y%m%d')}.csv",

            mime="text/csv"

        )
