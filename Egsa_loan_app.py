import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import mysql.connector
import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="EGSA | Loan Registration",
    page_icon="💰",
    layout="wide"
)

st.title("💰 EGSA Loan Registration System")
st.caption("Loan member registration | TiDB Cloud Database")

# ============================================================
# LOAN CONFIGURATION
# ============================================================
LOAN_LEVELS = {
    "Level 1": {"amount": 5000, "rate": 5, "days": 15},
    "Level 2": {"amount": 10000, "rate": 5, "days": 20},
    "Level 3": {"amount": 15000, "rate": 10, "days": 30},
    "Level 4": {"amount": 25000, "rate": 15, "days": 60},
    "Level 5": {"amount": 50000, "rate": 25, "days": 90},
    "Level 6": {"amount": 100000, "rate": 15, "days": 180},
}

DEFAULT_FROM_ACCOUNT = "1000724673337"
LOCAL_TZ = ZoneInfo("Africa/Addis_Ababa")

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
def get_db_connection():
    config = st.secrets["tidb"]

    connection_args = {
        "host": config["host"],
        "port": int(config.get("port", 4000)),
        "user": config["user"],
        "password": config["password"],
        "database": config["database"],
        "connection_timeout": 20,
        "autocommit": False,
        "ssl_disabled": False,
        "ssl_verify_cert": config.get("ssl_verify_cert", False),
        "ssl_verify_identity": config.get("ssl_verify_identity", False),
    }

    # Optional CA certificate file, if configured
    if config.get("ssl_ca"):
        connection_args["ssl_ca"] = config["ssl_ca"]

    return mysql.connector.connect(**connection_args)


# ============================================================
# TABLE NAME VALIDATION
# ============================================================
def get_table_name():
    table = st.secrets["tidb"].get("table", "loans")

    if not re.fullmatch(r"[A-Za-z0-9_]+", table):
        raise ValueError("Invalid TiDB table name in secrets.toml")

    return f"`{table}`"


# ============================================================
# LOAN ID GENERATION
# Format:
# FROMACCOUNT_BUSINESSDATE_STATUS_LOANTYPE
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
# DATABASE INSERT
# ============================================================
def save_loan(loan_data):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        table = get_table_name()

        sql = f"""
            INSERT INTO {table} (
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
            loan_data["status"],
        )

        cursor.execute(sql, values)
        connection.commit()

        return True, "Loan successfully registered!"

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()

        return False, (
            "Duplicate loan ID. A loan with this account, "
            "date and level may already exist."
        )

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
# LOAD REGISTERED LOANS
# ============================================================
def load_loans():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        table = get_table_name()

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
            FROM {table}
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
# SIDEBAR
# ============================================================
st.sidebar.title("EGSA Loan System")
page = st.sidebar.radio(
    "Navigation",
    ["Register New Loan", "Loan History"]
)

st.sidebar.divider()
st.sidebar.info(
    f"Default From Account\n\n{DEFAULT_FROM_ACCOUNT}"
)


# ============================================================
# PAGE 1: REGISTER NEW LOAN
# ============================================================
if page == "Register New Loan":

    st.subheader("New Loan Member Registration")

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
                placeholder="Enter receiving account number"
            )

            phone_no = st.text_input(
                "Phone Number",
                placeholder="Enter member phone number"
            )

        with col2:
            loan_type = st.selectbox(
                "Loan Level",
                options=list(LOAN_LEVELS.keys())
            )

            registration_date = st.date_input(
                "Business / Registration Date",
                value=current_date
            )

        # Calculate loan details
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

        due_date = registration_date + timedelta(days=duration)

        loan_id = generate_loan_id(
            from_account.strip(),
            registration_date,
            loan_type
        )

        st.divider()
        st.subheader("Automatic Loan Calculation")

        c1, c2, c3 = st.columns(3)

        c1.metric("Loan Amount", f"ETB {principal:,.2f}")
        c2.metric("Interest", f"{interest_rate}%")
        c3.metric("Duration", f"{duration} days")

        c4, c5, c6 = st.columns(3)

        c4.metric("Interest Amount", f"ETB {interest_amount:,.2f}")
        c5.metric("Total Collection", f"ETB {collection_amount:,.2f}")
        c6.metric("Due Date", due_date.strftime("%d-%m-%Y"))

        st.caption(f"Generated Loan ID: {loan_id}")

        submitted = st.form_submit_button(
            "💾 Register Loan",
            type="primary",
            use_container_width=True
        )

    if submitted:

        # Validate account numbers and phone
        errors = []

        if not from_account.strip().isdigit():
            errors.append("From account must contain digits only.")

        if not to_account.strip().isdigit():
            errors.append("To account must contain digits only.")

        if not phone_no.strip().isdigit():
            errors.append("Phone number must contain digits only.")

        if from_account.strip() == to_account.strip():
            errors.append("From account and To account cannot be identical.")

        if registration_date > current_date:
            errors.append("Registration date cannot be in the future.")

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
                "status": "In Progress",
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
                st.error(f"Registration failed: {message}")


# ============================================================
# PAGE 2: LOAN HISTORY
# ============================================================
elif page == "Loan History":

    st.subheader("Registered Loan Members")

    if st.button("🔄 Refresh Loan Records"):
        st.rerun()

    with st.spinner("Loading records from TiDB..."):

        df, error = load_loans()

    if error:
        st.error(f"Unable to load loan records: {error}")

    elif df.empty:
        st.info("No loan records found.")

    else:

        total_loans = len(df)

        total_disbursed = pd.to_numeric(
            df["disbursed_amount"], errors="coerce"
        ).sum()

        total_collection = pd.to_numeric(
            df["collection_amount"], errors="coerce"
        ).sum()

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Loans", f"{total_loans:,}")
        c2.metric("Total Disbursed", f"ETB {total_disbursed:,.2f}")
        c3.metric("Expected Collection", f"ETB {total_collection:,.2f}")

        st.divider()

        search = st.text_input(
            "Search by Account Number or Loan ID"
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

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Download Loan Records (CSV)",
            data=csv_data,
            file_name="EGSA_Loan_Records.csv",
            mime="text/csv"
        )
