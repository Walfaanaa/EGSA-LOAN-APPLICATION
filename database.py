import streamlit as st
import mysql.connector


def get_connection():

    conn = mysql.connector.connect(

        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"],

        ssl_ca="tidb-ca.pem"

    )

    return conn
