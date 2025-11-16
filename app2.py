import streamlit as st
import mysql.connector
import pandas as pd

conn = mysql.connector.connect(
    host="localhost",
    user="esimerkkikäyttäjä",
    password="1234",
    database="streamlit_db"

cursor = conn.cursor()
cursor.execute("SELECT * FROM Streamlit")
rows = cursor.fetchall()

df = pd.DataFrame(rows, columns=[col[0] for col in cursor.description])

st.title("Data-analyysi")
st.write("Tietokannan sisältö:")
st.dataframe(df)
