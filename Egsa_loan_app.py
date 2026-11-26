import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import mysql.connector
import pandas as pd
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="EGSA2025 | Short-Term Loan Management",
    page_icon="💰",
    layout="wide"
)

st.title("💰 EGSA2025 Short-Term Loan Management")
st.caption("Loan Registration | Loan History | Status Management")


# ============================================================
# 2. SYSTEM CONFIGURATION
# ============================================================
DEFAULT_FROM_ACCOUNT = "1000724673337"
LOCAL_TZ = ZoneInfo("Africa/Addis_Ababa")

LOAN_LEVELS = {
    "Level 1": {"amount": 5000, "rate": 5, "days": 15},
    "Level 2": {"amount": 10000, "rate": 5, "days": 20},
    "Level 3": {"amount": 15000, "rate": 10, "days": 30},
    "Level 4": {"amount": 25000, "rate": 15, "days": 60},
    "Level 5": {"amount": 50000, "rate": 25, "days": 90},
    "Level 6": {"amount": 100000, "rate": 15, "days": 180},
}

STATUS_OPTIONS = [
    "In Progress",
    "Completed",
    "Overdue",
    "Cancelled"
]

# ============================================================
# 3. TIDB DATABASE CONNECTION
# ============================================================
def get_db_connection():

    config = st.secrets["tidb"]

    connection_args = {
        "host": config["host"],
        "port": int(config.get("port", 4000)),
        "user": config["user"],
        "password": config["password"],
        "database": "lottery_db",
        "connection_timeout": 20,
        "autocommit": False,
        "ssl_disabled": False,
        "ssl_verify_cert": config.get("ssl_verify_cert", False),
        "ssl_verify_identity": config.get("ssl_verify_identity", False),
    }

    if config.get("ssl_ca"):
        connection_args["ssl_ca"] = config["ssl_ca"]

    return mysql.connector.connect(**connection_args)


TABLE_NAME = "`EGSA2025_short_term_loan`"


# ============================================================
# 4. LOAN ID GENERATION
# ============================================================
def generate_loan_id(from_account, business_date, loan_type):

    date_part = business_date.strftime("%Y%m%d")

    return (
        f"{from_account}_"
        f"{date_part}_"
        f"IN_PROGRESS_"
        f"{loan_type.upper().replace(' ', '_')}"
    )


# ============================================================
# 5. SAVE NEW LOAN
# ============================================================
def save_loan(loan_data):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        sql = f"""
            INSERT INTO {TABLE_NAME} (
                loan_id,
                loan_type,
                business_date,
                disbursed_amount,
                interest_rate,
                interest_amount,
                collection_amount,
                from_account,
                to_account,
                due_date,
                phone_no,
                status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """

        values = (
            loan_data["loan_id"],
            loan_data["loan_type"],
            loan_data["business_date"],
            loan_data["disbursed_amount"],
            loan_data["interest_rate"],
            loan_data["interest_amount"],
            loan_data["collection_amount"],
            loan_data["from_account"],
            loan_data["to_account"],
            loan_data["due_date"],
            loan_data["phone_no"],
            loan_data["status"]
        )

        cursor.execute(sql, values)
        connection.commit()

        return True, "Loan successfully registered!"

    except mysql.connector.IntegrityError as error:

        if connection:
            connection.rollback()

        return False, f"Duplicate or integrity error: {error}"

    except Exception as error:

        if connection:
            connection.rollback()

        return False, str(error)

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ============================================================
# 6. LOAD LOAN HISTORY
# ============================================================
def load_loans():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        sql = f"""
            SELECT
                loan_id,
                loan_type,
                business_date,
                disbursed_amount,
                interest_rate,
                interest_amount,
                collection_amount,
                from_account,
                to_account,
                due_date,
                phone_no,
                status
            FROM {TABLE_NAME}
            ORDER BY business_date DESC
            LIMIT 1000
        """

        cursor.execute(sql)

        records = cursor.fetchall()

        return pd.DataFrame(records), None

    except Exception as error:

        return pd.DataFrame(), str(error)

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ============================================================
# 7. UPDATE LOAN STATUS
# ============================================================
def update_loan_status(loan_id, new_status):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        sql = f"""
            UPDATE {TABLE_NAME}
            SET status = %s
            WHERE loan_id = %s
        """

        cursor.execute(sql, (new_status, loan_id))

        if cursor.rowcount == 0:

            connection.rollback()

            return False, "Loan ID not found."

        connection.commit()

        return True, "Loan status successfully updated!"

    except Exception as error:

        if connection:
            connection.rollback()

        return False, str(error)

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ============================================================
# 8. SIDEBAR NAVIGATION
# ============================================================
st.sidebar.title("EGSA2025 Loan System")

page = st.sidebar.radio(
    "Navigation",
    [
        "Register New Loan",
        "Loan History",
        "Update Loan Status"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    f"Default From Account\n\n{DEFAULT_FROM_ACCOUNT}"
)

st.sidebar.caption("Database: lottery_db")
st.sidebar.caption("Table: EGSA2025_short_term_loan")


# ============================================================
# 9. REGISTER NEW LOAN
# ============================================================
if page == "Register New Loan":

    st.subheader("📝 New Loan Member Registration")

    current_date = datetime.now(LOCAL_TZ).date()

    with st.form("loan_registration_form"):

        col1, col2 = st.columns(2)

        with col1:

            from_account = st.text_input(
                "From Account",
                value=DEFAULT_FROM_ACCOUNT
            )

            to_account = st.text_input(
                "To Account",
                placeholder="Enter receiving account"
            )

            phone_no = st.text_input(
                "Phone Number",
                placeholder="Enter member phone number"
            )

        with col2:

            loan_type = st.selectbox(
                "Loan Level",
                list(LOAN_LEVELS.keys())
            )

            registration_date = st.date_input(
                "Business / Registration Date",
                value=current_date
            )

        selected = LOAN_LEVELS[loan_type]

        principal = selected["amount"]
        interest_rate = selected["rate"]
        duration = selected["days"]

        interest_amount = round(
            principal * interest_rate / 100, 2
        )

        collection_amount = round(
            principal + interest_amount, 2
        )

        due_date = registration_date + timedelta(
            days=duration
        )

        loan_id = generate_loan_id(
            from_account.strip(),
            registration_date,
            loan_type
        )

        st.divider()

        st.subheader("Automatic Loan Calculation")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Loan Principal",
            f"ETB {principal:,.2f}"
        )

        c2.metric(
            "Interest Rate",
            f"{interest_rate}%"
        )

        c3.metric(
            "Duration",
            f"{duration} Days"
        )

        c4, c5, c6 = st.columns(3)

        c4.metric(
            "Interest Amount",
            f"ETB {interest_amount:,.2f}"
        )

        c5.metric(
            "Total Collection",
            f"ETB {collection_amount:,.2f}"
        )

        c6.metric(
            "Due Date",
            due_date.strftime("%d-%m-%Y")
        )

        st.caption(f"Loan ID: {loan_id}")

        submitted = st.form_submit_button(
            "💾 Register New Loan",
            type="primary",
            use_container_width=True
        )

    if submitted:

        errors = []

        if not from_account.strip().isdigit():
            errors.append("Invalid From Account.")

        if not to_account.strip().isdigit():
            errors.append("Invalid To Account.")

        if not phone_no.strip().isdigit():
            errors.append("Invalid Phone Number.")

        if from_account.strip() == to_account.strip():
            errors.append(
                "From Account and To Account cannot be identical."
            )

        if registration_date > current_date:
            errors.append(
                "Registration date cannot be in the future."
            )

        if errors:

            for error in errors:
                st.error(error)

        else:

            loan_data = {

                "loan_id": loan_id,
                "loan_type": loan_type,
                "business_date": registration_date,
                "disbursed_amount": principal,
                "interest_rate": interest_rate,
                "interest_amount": interest_amount,
                "collection_amount": collection_amount,
                "from_account": int(from_account),
                "to_account": int(to_account),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "phone_no": int(phone_no),
                "status": "In Progress"

            }

            with st.spinner("Saving loan to TiDB..."):

                success, message = save_loan(loan_data)

            if success:

                st.success(message)

                st.subheader("Registered Loan Details")

                st.dataframe(
                    pd.DataFrame([loan_data]),
                    use_container_width=True,
                    hide_index=True
                )

                st.balloons()

            else:

                st.error(message)


# ============================================================
# 10. LOAN HISTORY
# ============================================================
elif page == "Loan History":

    st.subheader("📊 Registered Loan History")

    col1, col2 = st.columns([1, 4])

    with col1:

        if st.button("🔄 Refresh Records"):
            st.rerun()

    df, error = load_loans()

    if error:

        st.error(f"Database Error: {error}")

    elif df.empty:

        st.info("No registered loans found.")

    else:

        total_loans = len(df)

        total_disbursed = pd.to_numeric(
            df["disbursed_amount"],
            errors="coerce"
        ).sum()

        total_collection = pd.to_numeric(
            df["collection_amount"],
            errors="coerce"
        ).sum()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Loans",
            f"{total_loans:,}"
        )

        c2.metric(
            "Total Disbursed",
            f"ETB {total_disbursed:,.2f}"
        )

        c3.metric(
            "Expected Collection",
            f"ETB {total_collection:,.2f}"
        )

        st.divider()

        search = st.text_input(
            "Search Loan ID or Account Number"
        )

        if search:

            mask = (
                df["loan_id"].astype(str).str.contains(
                    search, case=False, na=False
                )
                |
                df["from_account"].astype(str).str.contains(
                    search, na=False
                )
                |
                df["to_account"].astype(str).str.contains(
                    search, na=False
                )
            )

            df = df[mask]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Loan History CSV",
            data=csv_data,
            file_name="EGSA2025_Loan_History.csv",
            mime="text/csv"
        )


# ============================================================
# 11. UPDATE LOAN STATUS
# ============================================================
elif page == "Update Loan Status":

    st.subheader("🔄 Update Existing Loan Status")

    df, error = load_loans()

    if error:

        st.error(f"Database Error: {error}")

    elif df.empty:

        st.info("No registered loans available.")

    else:

        search = st.text_input(
            "Search by Loan ID or From Account",
            key="status_search"
        )

        filtered = df.copy()

        if search:

            mask = (
                filtered["loan_id"].astype(str).str.contains(
                    search, case=False, na=False
                )
                |
                filtered["from_account"].astype(str).str.contains(
                    search, na=False
                )
            )

            filtered = filtered[mask]

        if filtered.empty:

            st.warning("No matching loans found.")

        else:

            selected_loan_id = st.selectbox(
                "Select Loan ID",
                filtered["loan_id"].astype(str).tolist()
            )

            loan = filtered[
                filtered["loan_id"].astype(str)
                == selected_loan_id
            ].iloc[0]

            st.divider()

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Loan Principal",
                f"ETB {float(loan['disbursed_amount']):,.2f}"
            )

            c2.metric(
                "Expected Collection",
                f"ETB {float(loan['collection_amount']):,.2f}"
            )

            c3.metric(
                "Current Status",
                str(loan["status"])
            )

            c4, c5 = st.columns(2)

            c4.write(
                f"**From Account:** {loan['from_account']}"
            )

            c5.write(
                f"**To Account:** {loan['to_account']}"
            )

            c4.write(
                f"**Loan Type:** {loan['loan_type']}"
            )

            c5.write(
                f"**Due Date:** {loan['due_date']}"
            )

            st.divider()

            current_status = str(loan["status"])

            options = STATUS_OPTIONS.copy()

            if current_status not in options:
                options.insert(0, current_status)

            new_status = st.selectbox(
                "Select New Status",
                options,
                index=options.index(current_status)
            )

            if st.button(
                "💾 Update Loan Status",
                type="primary",
                use_container_width=True
            ):

                if new_status == current_status:

                    st.warning(
                        "Please select a different status."
                    )

                else:

                    with st.spinner("Updating TiDB..."):

                        success, message = update_loan_status(
                            selected_loan_id,
                            new_status
                        )

                    if success:

                        st.success(message)
                        st.rerun()

                    else:

                        st.error(message)
