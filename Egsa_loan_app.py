import uuid
from datetime import date, timedelta
from zoneinfo import ZoneInfo

import mysql.connector
import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="EGSA2025 | Short-Term Loan Dashboard",
    page_icon="💰",
    layout="wide"
)

st.title("💰 EGSA2025 Short-Term Loan Management")


# ============================================================
# DATABASE CONFIGURATION
# ============================================================
DB_NAME = st.secrets["DB_NAME"]
DB_TABLE = st.secrets["DB_TABLE"]

DEFAULT_FROM_ACCOUNT = "1000724673337"

STATUSES = [
    "in progress",
    "completed",
    "overdue",
    "cancelled"
]

# Loan configuration
LOAN_LEVELS = {
    "level_1": {
        "amount": 5000,
        "rate": 5,
        "term": 15
    },
    "level_2": {
        "amount": 10000,
        "rate": 5,
        "term": 20
    },
    "level_3": {
        "amount": 15000,
        "rate": 10,
        "term": 30
    },
    "level_4": {
        "amount": 25000,
        "rate": 15,
        "term": 60
    },
    "level_5": {
        "amount": 50000,
        "rate": 25,
        "term": 90
    },
    "level_6": {
        "amount": 100000,
        "rate": 15,
        "term": 180
    }
}


def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["DB_HOST"],
        port=int(st.secrets["DB_PORT"]),
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=DB_NAME,
        connection_timeout=20,
        autocommit=False,
        ssl_disabled=False,
        ssl_verify_cert=False,
        ssl_verify_identity=False
    )


# ============================================================
# DATABASE SCHEMA INFORMATION
# ============================================================
@st.cache_data(ttl=300)
def get_table_schema():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
            """,
            (DB_NAME, DB_TABLE)
        )

        rows = cursor.fetchall()
        return {row["COLUMN_NAME"].lower(): row for row in rows}

    finally:
        cursor.close()
        conn.close()


def is_numeric_column(column_name):
    schema = get_table_schema()

    if column_name.lower() not in schema:
        raise ValueError(f"Column {column_name} was not found in the database.")

    data_type = schema[column_name.lower()]["DATA_TYPE"].lower()

    return data_type in [
        "int", "integer", "bigint", "smallint",
        "mediumint", "tinyint", "decimal", "numeric",
        "float", "double"
    ]


def convert_value(column_name, value):
    """
    Convert values according to the actual database column type.
    """

    schema = get_table_schema()
    column = schema[column_name.lower()]
    data_type = column["DATA_TYPE"].lower()

    if value is None:
        return None

    if data_type in [
        "int", "integer", "bigint", "smallint",
        "mediumint", "tinyint"
    ]:
        return int(value)

    if data_type in ["decimal", "numeric", "float", "double"]:
        return float(value)

    if data_type == "date":
        return value

    return str(value)


def format_date_for_column(column_name, value):
    schema = get_table_schema()
    data_type = schema[column_name.lower()]["DATA_TYPE"].lower()

    if data_type == "date":
        return value

    if data_type in ["datetime", "timestamp"]:
        return value

    # For VARCHAR/TEXT date columns
    return value.strftime("%-m/%-d/%Y") if hasattr(value, "strftime") else str(value)


# ============================================================
# LOAN ID GENERATION
# ============================================================
def generate_loan_id(cursor):
    """
    Generate loan_id based on its database type.

    - If loan_id is AUTO_INCREMENT, let the database generate it.
    - If loan_id is numeric, generate MAX(loan_id) + 1.
    - If loan_id is text, generate a unique EGSA reference.
    """

    schema = get_table_schema()
    column = schema["loan_id"]

    if "auto_increment" in str(column["EXTRA"]).lower():
        return None

    if is_numeric_column("loan_id"):
        cursor.execute(
            f"SELECT COALESCE(MAX(`loan_id`), 0) + 1 FROM `{DB_TABLE}`"
        )
        return cursor.fetchone()[0]

    return f"EGSA-{date.today():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"


# ============================================================
# REGISTER NEW LOAN
# ============================================================
def register_loan(data):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check duplicate manually entered ID
        cursor.execute(
            f"SELECT COUNT(*) FROM `{DB_TABLE}` WHERE `id` = %s",
            (data["id"],)
        )

        if cursor.fetchone()[0] > 0:
            raise ValueError(
                f"ID {data['id']} already exists. Please enter another ID."
            )

        loan_id = generate_loan_id(cursor)

        columns = [
            "business_date",
            "id",
            "loan_type",
            "disbursed_amount",
            "interest_rate",
            "interest_amount",
            "collection_amount",
            "from_account",
            "to_account",
            "due_date",
            "phone_no",
            "status"
        ]

        values = [
            format_date_for_column("business_date", data["business_date"]),
            convert_value("id", data["id"]),
            data["loan_type"],
            data["disbursed_amount"],
            data["interest_rate"],
            data["interest_amount"],
            data["collection_amount"],
            convert_value("from_account", data["from_account"]),
            convert_value("to_account", data["to_account"]),
            format_date_for_column("due_date", data["due_date"]),
            convert_value("phone_no", data["phone_no"]),
            data["status"]
        ]

        # Include loan_id if it is not AUTO_INCREMENT
        if loan_id is not None:
            columns.insert(0, "loan_id")
            values.insert(0, convert_value("loan_id", loan_id))

        column_sql = ", ".join(f"`{col}`" for col in columns)
        placeholders = ", ".join(["%s"] * len(values))

        sql = f"""
            INSERT INTO `{DB_TABLE}` ({column_sql})
            VALUES ({placeholders})
        """

        cursor.execute(sql, values)
        conn.commit()

        return loan_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# LOAD LOAN HISTORY
# ============================================================
def load_loan_history():
    conn = get_db_connection()

    try:
        query = f"""
            SELECT
                `loan_id`,
                `business_date`,
                `id`,
                `loan_type`,
                `disbursed_amount`,
                `interest_rate`,
                `interest_amount`,
                `collection_amount`,
                `from_account`,
                `to_account`,
                `due_date`,
                `phone_no`,
                `status`
            FROM `{DB_TABLE}`
            ORDER BY `business_date` DESC
        """

        return pd.read_sql(query, conn)

    finally:
        conn.close()


# ============================================================
# UPDATE LOAN STATUS
# ============================================================
def update_loan_status(record_id, new_status):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE `{DB_TABLE}`
            SET `status` = %s
            WHERE `id` = %s
            """,
            (new_status, record_id)
        )

        affected_rows = cursor.rowcount
        conn.commit()

        return affected_rows

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Page",
    [
        "Register New Loan",
        "Loan History",
        "Update Loan Status"
    ]
)


# ============================================================
# PAGE 1: REGISTER NEW LOAN
# ============================================================
if page == "Register New Loan":

    st.header("📝 Register New Short-Term Loan")

    with st.form("loan_registration_form"):

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Loan Information")

            # MANUAL ID ENTRY
            record_id = st.number_input(
                "ID (Enter manually)",
                min_value=1,
                step=1,
                value=None,
                placeholder="Example: 1013"
            )

            business_date = st.date_input(
                "Business Date",
                value=date.today()
            )

            loan_type = st.selectbox(
                "Loan Type",
                list(LOAN_LEVELS.keys())
            )

            loan_config = LOAN_LEVELS[loan_type]

            disbursed_amount = loan_config["amount"]
            interest_rate = loan_config["rate"]
            loan_term = loan_config["term"]

            interest_amount = (
                disbursed_amount * interest_rate / 100
            )

            collection_amount = (
                disbursed_amount + interest_amount
            )

            due_date = business_date + timedelta(days=loan_term)

            st.number_input(
                "Disbursed Amount (ETB)",
                value=float(disbursed_amount),
                disabled=True
            )

            st.number_input(
                "Interest Rate (%)",
                value=float(interest_rate),
                disabled=True
            )

            st.number_input(
                "Interest Amount (ETB)",
                value=float(interest_amount),
                disabled=True
            )

            st.number_input(
                "Collection Amount (ETB)",
                value=float(collection_amount),
                disabled=True
            )

            st.info(f"Loan term: {loan_term} days")

        with col2:

            st.subheader("Account Information")

            from_account = st.text_input(
                "From Account",
                value=DEFAULT_FROM_ACCOUNT
            )

            to_account = st.text_input(
                "To Account"
            )

            phone_no = st.text_input(
                "Phone Number"
            )

            st.date_input(
                "Due Date",
                value=due_date,
                disabled=True
            )

            status = st.selectbox(
                "Loan Status",
                STATUSES,
                index=0
            )

        submitted = st.form_submit_button(
            "Register Loan",
            use_container_width=True
        )

    if submitted:

        if record_id is None:
            st.error("Please enter the loan ID.")
        elif not to_account.strip():
            st.error("Please enter the recipient account number.")
        elif not phone_no.strip():
            st.error("Please enter the phone number.")
        elif not from_account.strip():
            st.error("Please enter the source account number.")
        else:

            try:
                loan_data = {
                    "id": int(record_id),
                    "business_date": business_date,
                    "loan_type": loan_type,
                    "disbursed_amount": disbursed_amount,
                    "interest_rate": interest_rate,
                    "interest_amount": interest_amount,
                    "collection_amount": collection_amount,
                    "from_account": from_account.strip(),
                    "to_account": to_account.strip(),
                    "due_date": due_date,
                    "phone_no": phone_no.strip(),
                    "status": status
                }

                generated_loan_id = register_loan(loan_data)

                if generated_loan_id is None:
                    st.success(
                        f"Loan registered successfully. ID: {record_id}"
                    )
                else:
                    st.success(
                        f"Loan registered successfully. "
                        f"Loan ID: {generated_loan_id} | ID: {record_id}"
                    )

                st.cache_data.clear()

            except Exception as e:
                st.error(f"Registration failed: {e}")


# ============================================================
# PAGE 2: LOAN HISTORY
# ============================================================
elif page == "Loan History":

    st.header("📋 Loan History")

    try:
        df = load_loan_history()

        if df.empty:
            st.info("No loan records found.")

        else:

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Loans", len(df))

            col2.metric(
                "Total Disbursed (ETB)",
                f"{pd.to_numeric(df['disbursed_amount'], errors='coerce').sum():,.2f}"
            )

            col3.metric(
                "Total Collection (ETB)",
                f"{pd.to_numeric(df['collection_amount'], errors='coerce').sum():,.2f}"
            )

            st.divider()

            search = st.text_input(
                "Search by ID, Loan ID, Account, or Phone Number"
            )

            if search:
                mask = df.astype(str).apply(
                    lambda col: col.str.contains(
                        search,
                        case=False,
                        na=False
                    )
                ).any(axis=1)

                df = df[mask]

            status_filter = st.multiselect(
                "Filter by Status",
                options=sorted(
                    df["status"].dropna().astype(str).unique().tolist()
                )
            )

            if status_filter:
                df = df[
                    df["status"].astype(str).isin(status_filter)
                ]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            csv_data = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download Loan History CSV",
                data=csv_data,
                file_name="EGSA2025_loan_history.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Unable to load loan history: {e}")


# ============================================================
# PAGE 3: UPDATE LOAN STATUS
# ============================================================
elif page == "Update Loan Status":

    st.header("🔄 Update Loan Status")

    st.write(
        "Enter the manually assigned ID to find the loan "
        "and update its status."
    )

    record_id = st.number_input(
        "Enter Loan ID (ID column)",
        min_value=1,
        step=1,
        value=None,
        placeholder="Example: 1013"
    )

    if st.button("Find Loan", use_container_width=True):

        if record_id is None:
            st.warning("Please enter an ID.")

        else:
            try:
                conn = get_db_connection()

                query = f"""
                    SELECT *
                    FROM `{DB_TABLE}`
                    WHERE `id` = %s
                """

                found = pd.read_sql(
                    query,
                    conn,
                    params=(int(record_id),)
                )

                conn.close()

                if found.empty:
                    st.error("No loan found with this ID.")

                else:
                    st.session_state["selected_loan"] = found.iloc[0].to_dict()

            except Exception as e:
                st.error(f"Search failed: {e}")

    if "selected_loan" in st.session_state:

        loan = st.session_state["selected_loan"]

        st.divider()
        st.subheader("Loan Details")

        details = pd.DataFrame(
            [
                {"Field": "Loan ID", "Value": loan.get("loan_id")},
                {"Field": "ID", "Value": loan.get("id")},
                {"Field": "Loan Type", "Value": loan.get("loan_type")},
                {"Field": "Business Date", "Value": loan.get("business_date")},
                {"Field": "Disbursed Amount", "Value": loan.get("disbursed_amount")},
                {"Field": "Interest Amount", "Value": loan.get("interest_amount")},
                {"Field": "Collection Amount", "Value": loan.get("collection_amount")},
                {"Field": "Current Status", "Value": loan.get("status")}
            ]
        )

        st.dataframe(
            details,
            use_container_width=True,
            hide_index=True
        )

        current_status = str(loan.get("status", "")).lower()

        if current_status not in STATUSES:
            current_status = STATUSES[0]

        new_status = st.selectbox(
            "Select New Status",
            STATUSES,
            index=STATUSES.index(current_status)
        )

        if st.button(
            "Update Loan Status",
            type="primary",
            use_container_width=True
        ):

            try:
                affected = update_loan_status(
                    loan["id"],
                    new_status
                )

                if affected > 0:
                    st.success(
                        f"Status updated successfully to {new_status}."
                    )
                    st.session_state.pop("selected_loan", None)
                    st.cache_data.clear()
                else:
                    st.warning(
                        "No database row was changed. "
                        "The loan may already have this status."
                    )

            except Exception as e:
                st.error(f"Status update failed: {e}")


# ============================================================
# FOOTER
# ============================================================
st.sidebar.divider()
st.sidebar.caption("EGSA2025 | Short-Term Loan Management")
st.sidebar.caption("Database: TiDB Cloud")
