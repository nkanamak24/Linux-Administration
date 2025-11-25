import streamlit as st
import mysql.connector
import pandas as pd
import altair as alt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Säädata", layout="wide")

# Automaattinen päivitys 15 min välein
st_autorefresh(interval=900000, key="data_refresh")

st.title("Säädata")

# --- SÄÄDATA ---
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="esimerkkikäyttäjä",
        password="1234",
        database="weather_db"
    )

    query = """
    SELECT id, paikkakunta, lämpötila, sää, paikallinen_aika
    FROM weather_data
    ORDER BY paikallinen_aika DESC LIMIT 50;
    """
    df = pd.read_sql(query, conn)

finally:
    conn.close()

df.rename(columns={
    'paikkakunta': 'Paikkakunta',
    'lämpötila': 'Lämpötila (°C)',
    'sää': 'Sää',
    'paikallinen_aika': 'Paikallinen aika'
}, inplace=True)

if df.empty:
    st.warning("Ei säädataa saatavilla. Odota seuraavaa päivitystä.")
else:
    city_name = df.iloc[0]['Paikkakunta']
    latest = df.iloc[0]

    st.header(f"Säädata parhaasta paikasta, eli:")
    st.header(f"{city_name}")
    st.subheader(f"(Kellossa näkyy Suomen aika)")
    st.subheader(f"Viimeisin mittaus: {latest['Lämpötila (°C)']}°C, {latest['Sää']} ({latest['Paikallinen aika']})")

    st.dataframe(df)

    chart = alt.Chart(df.sort_values('Paikallinen aika')).mark_line(point=True).encode(
        x='Paikallinen aika:T',
        y='Lämpötila (°C):Q'
    ).properties(title=f"Lämpötilatrendi ({city_name})")

    st.altair_chart(chart, use_container_width=True)
# --- ILMANLAATU ---
st.header("Ilmanlaatu (Seinäjoki)")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="esimerkkikäyttäjä",
        password="Tämä_on_hyvä_salasana2",
        database="weather_db"
    )

    aq_query = """
    SELECT timestamp, aqi, pm25, pm10
    FROM air_quality
    ORDER BY timestamp DESC LIMIT 24;
    """
    aq_df = pd.read_sql(aq_query, conn)

finally:
    conn.close()
if aq_df.empty:
    st.warning("Ei ilmanlaatudataa saatavilla. Odota seuraavaa päivitystä.")
else:
    latest_aq = aq_df.iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("EU AQI", f"{latest_aq['aqi']}")
    col2.metric("PM2.5", f"{latest_aq['pm25']} µg/m³")
    col3.metric("PM10", f"{latest_aq['pm10']} µg/m³")

    aq_chart = alt.Chart(aq_df.sort_values('timestamp')).mark_line(point=True).encode(
        x='timestamp:T',
        y='pm25:Q',
        tooltip=['timestamp', 'pm25', 'pm10', 'aqi']
    ).properties(title="Ilmanlaadun trendi (PM2.5)")
    st.altair_chart(aq_chart, use_container_width=True)

