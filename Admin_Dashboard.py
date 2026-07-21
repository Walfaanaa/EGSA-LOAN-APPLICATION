import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime


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


    if st.button("🔐 Login"):

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

WHERE status='Pending'

ORDER BY created_at DESC
"""


df = pd.read_sql(
    query,
    conn
)


conn.close()



st.subheader("📋 Pending Loan Applications")


if df.empty:

    st.info(
        "No pending loan applications"
    )

    st.stop()



st.dataframe(
    df,
    use_container_width=True
)



# ============================
# SELECT LOAN
# ============================


st.divider()

st.subheader("🔎 Review Loan")


selected_id = st.selectbox(
    "Select Loan ID",
    df["loan_id"].tolist()
)



selected_loan = df[
    df["loan_id"] == selected_id
].iloc[0]



st.write(
    f"""
### Applicant Information

**Name:** {selected_loan['full_name']}

**National ID:** {selected_loan['national_id']}

**Phone:** {selected_loan['phone']}


### Loan Information

**Amount:** {selected_loan['loan_amount']:,.2f} ETB

**Monthly Payment:** {selected_loan['monthly_payment']:,.2f} ETB


### Guarantor

**Name:** {selected_loan['guarantor_name']}

"""
)



# ============================
# DECISION
# ============================


col1, col2 = st.columns(2)



with col1:

    if st.button(
        "✅ Approve Loan",
        use_container_width=True
    ):


        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE loan_applications

            SET 
                status='Approved'

            WHERE loan_id=%s
            """,
            (
                selected_id,
            )
        )


        conn.commit()

        cursor.close()
        conn.close()


        st.success(
            "Loan Approved Successfully"
        )

        st.rerun()



with col2:

    if st.button(
        "❌ Reject Loan",
        use_container_width=True
    ):


        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE loan_applications

            SET 
                status='Rejected'

            WHERE loan_id=%s
            """,
            (
                selected_id,
            )
        )


        conn.commit()

        cursor.close()
        conn.close()


        st.error(
            "Loan Rejected"
        )

        st.rerun()
