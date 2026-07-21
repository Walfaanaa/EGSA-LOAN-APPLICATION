import streamlit as st
import pandas as pd
from database import get_connection


st.set_page_config(
    page_title="EGSA Loan Admin",
    layout="wide"
)


st.title("🏦 EGSA Loan Admin Dashboard")


# ============================
# ADMIN LOGIN
# ============================

if "admin_login" not in st.session_state:
    st.session_state.admin_login = False


if not st.session_state.admin_login:

    password = st.text_input(
        "Admin Password",
        type="password"
    )


    if st.button("Login"):

        if password == "admin123":

            st.session_state.admin_login = True
            st.success("Login successful")
            st.rerun()

        else:

            st.error("Wrong password")


    st.stop()



# ============================
# LOAD PENDING LOANS
# ============================


conn = get_connection()


query = """
SELECT
    loan_id,
    full_name,
    national_id,
    phone,
    loan_amount,
    monthly_payment,
    guarantor_name,
    support_letter,
    passport_photo,
    status,
    created_at

FROM loan_applications

ORDER BY created_at DESC
"""


df = pd.read_sql(
    query,
    conn
)


conn.close()



st.subheader("📋 Loan Applications")


if df.empty:

    st.info("No loan applications found")

else:

    st.dataframe(
        df,
        use_container_width=True
    )



# ============================
# APPROVAL SECTION
# ============================


st.divider()

st.subheader("Loan Decision")


loan_id = st.number_input(
    "Enter Loan ID",
    min_value=1,
    step=1
)



col1, col2 = st.columns(2)



with col1:

    if st.button("✅ Approve Loan"):


        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE loan_applications
            SET status='Approved'
            WHERE loan_id=%s
            """,
            (loan_id,)
        )


        conn.commit()

        cursor.close()
        conn.close()


        st.success(
            "Loan Approved Successfully"
        )

        st.rerun()



with col2:

    if st.button("❌ Reject Loan"):


        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE loan_applications
            SET status='Rejected'
            WHERE loan_id=%s
            """,
            (loan_id,)
        )


        conn.commit()

        cursor.close()
        conn.close()


        st.error(
            "Loan Rejected"
        )

        st.rerun()