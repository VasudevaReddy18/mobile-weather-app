
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import os

st.set_page_config(page_title="Weather Voice App", layout="centered")

API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "your_openweathermap_api_key_here"
UNITS = "metric"
CACHE_FILE = "cached_weather.json"

# Sidebar input
st.sidebar.title("🎙️ Voice Search (Coming Soon)")
st.sidebar.text("Click the mic and speak a city name.")
st.sidebar.button("🎤 Speak")

# Typed fallback
city = st.sidebar.text_input("Or type city name:", "Hyderabad")
submit = st.sidebar.button("Get Weather")

@st.cache_data(show_spinner=True)
def fetch_weather(city):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": UNITS}
    return requests.get(url, params=params).json()

data = None
if submit:
    data = fetch_weather(city)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
elif os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        data = json.load(f)
        st.warning("⚠️ Using cached data.")

if data:
    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message')}")
    else:
        forecasts = data["list"]
        st.title(f"📍 {city} Weather")
        st.metric("🌡️ Temperature", f"{forecasts[0]['main']['temp']}°C")
        st.metric("💧 Humidity", f"{forecasts[0]['main']['humidity']}%")
        st.metric("💨 Wind", f"{forecasts[0]['wind']['speed']} m/s")

        df = pd.DataFrame({
            "Time": [f["dt_txt"] for f in forecasts[:6]],
            "Temp (°C)": [f["main"]["temp"] for f in forecasts[:6]],
            "Humidity (%)": [f["main"]["humidity"] for f in forecasts[:6]],
        })
        st.line_chart(df.set_index("Time")[["Temp (°C)", "Humidity (%)"]])
        st.dataframe(df)
