import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta
import os
import uuid


st.set_page_config(
    page_title="EGSA Loan System",
    layout="centered"
)


st.title("💰 EGSA Loan Application")

st.write("Complete all information below.")


# =====================================================
# PERSONAL INFORMATION
# =====================================================

st.subheader("👤 Personal Information")


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
        "Contract"
    ]
)


monthly_salary = st.number_input(
    "Monthly Salary",
    min_value=0.0,
    step=1000.0
)



# =====================================================
# LOAN INFORMATION
# =====================================================

st.subheader("💰 Loan Information")


loan_amount = st.number_input(
    "Loan Amount",
    min_value=0.0,
    step=500.0
)


loan_duration = st.number_input(
    "Loan Duration (Months)",
    min_value=1,
    step=1
)


interest_rate = 25


st.info(
    f"Interest Rate : {interest_rate}%"
)



# =====================================================
# LOAN CALCULATION
# =====================================================


interest_amount = (
    loan_amount * interest_rate / 100 / 12 * loan_duration
)


total_repayment = (
    loan_amount + interest_amount
)


monthly_payment = (
    total_repayment / loan_duration
    if loan_duration > 0
    else 0
)



st.write(
    f"""
    ### Loan Summary

    **Loan Amount:** {loan_amount:,.2f} ETB

    **Interest Amount:** {interest_amount:,.2f} ETB

    **Monthly Payment:** {monthly_payment:,.2f} ETB

    **Total Repayment:** {total_repayment:,.2f} ETB
    """
)



# Eligibility

maximum_payment = monthly_salary * 0.4


if monthly_payment <= maximum_payment:

    st.success(
        f"✅ Eligible for Loan\n\nMaximum Monthly Payment: {maximum_payment:,.2f} ETB"
    )

else:

    st.error(
        f"❌ Not Eligible\n\nMaximum Monthly Payment: {maximum_payment:,.2f} ETB"
    )



# =====================================================
# REPAYMENT DATE
# =====================================================

st.subheader("📅 Repayment Information")


repayment_start = st.date_input(
    "Repayment Start Date"
)


loan_end_date = (
    repayment_start 
    + relativedelta(months=loan_duration)
)


st.info(
    f"Loan End Date: {loan_end_date}"
)



# =====================================================
# GUARANTOR INFORMATION
# =====================================================

st.subheader("👥 Guarantor")


guarantor_name = st.text_input(
    "Guarantor Name"
)


guarantor_id = st.text_input(
    "Guarantor National ID"
)


guarantor_phone = st.text_input(
    "Guarantor Phone"
)

# =====================================================
# UPLOAD DOCUMENTS
# =====================================================

st.subheader("📂 Upload Documents")


support_letter = st.file_uploader(
    "Support Letter",
    type=["pdf", "jpg", "jpeg", "png"],
    key="loan_support_letter"
)


passport_photo = st.file_uploader(
    "Passport Photo",
    type=["jpg", "jpeg", "png"],
    key="loan_passport_photo"
)


# Display selected files

if support_letter is not None:
    st.success(
        f"✅ Support Letter Selected: {support_letter.name}"
    )

else:
    st.warning(
        "⚠️ Support Letter not selected"
    )


if passport_photo is not None:
    st.success(
        f"✅ Passport Photo Selected: {passport_photo.name}"
    )

else:
    st.warning(
        "⚠️ Passport Photo not selected"
    )


st.divider()

# =====================================================
# SUBMIT APPLICATION
# =====================================================

if st.button("📤 Submit Loan Application"):


    if not full_name:
        st.error("Please enter Full Name")
        st.stop()


    if not national_id:
        st.error("Please enter National ID")
        st.stop()


    if not phone:
        st.error("Please enter Phone Number")
        st.stop()


    if loan_amount <= 0:
        st.error("Please enter Loan Amount")
        st.stop()


    if not guarantor_name:
        st.error("Please enter Guarantor Name")
        st.stop()


    if support_letter is None:

        st.error(
            "Please upload the Support Letter."
        )

        st.stop()



    # FIXED: photo --> passport_photo

    if passport_photo is None:

        st.error(
            "Please upload the Passport Photo."
        )

        st.stop()



    # =====================================================
    # SAVE DOCUMENTS
    # =====================================================

    upload_folder = "uploads"


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    support_filename = (
        f"{uuid.uuid4()}_{support_letter.name}"
    )


    passport_filename = (
        f"{uuid.uuid4()}_{passport_photo.name}"
    )



    with open(
        os.path.join(
            upload_folder,
            support_filename
        ),
        "wb"
    ) as f:

        f.write(
            support_letter.getbuffer()
        )



    with open(
        os.path.join(
            upload_folder,
            passport_filename
        ),
        "wb"
    ) as f:

        f.write(
            passport_photo.getbuffer()
        )



    st.success(
        "🎉 Loan Application Submitted Successfully!"
    )


    st.write(
        "Documents saved successfully."
    )
