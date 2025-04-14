
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import os

st.set_page_config(page_title="Pro Weather App – Phase 3", layout="centered")

# Language support dictionary (simple)
LANG = {
    "en": {"temp": "Temperature", "humidity": "Humidity", "wind": "Wind", "alerts": "Weather Alerts"},
    "hi": {"temp": "तापमान", "humidity": "नमी", "wind": "पवन", "alerts": "मौसम चेतावनी"},
    "te": {"temp": "ఉష్ణోగ్రత", "humidity": "ఆర్ద్రత", "wind": "గాలి", "alerts": "వాతావరణ హెచ్చరికలు"}
}

# Get selected language
lang = st.sidebar.selectbox("Language", options=["en", "hi", "te"], format_func=lambda x: {"en":"English","hi":"Hindi","te":"Telugu"}[x])

# City Input
city = st.text_input("Enter city name (or use cached)", value="Hyderabad")
submit = st.button("Get Weather")

API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "your_openweathermap_api_key_here"
UNITS = "metric"
CACHE_FILE = "cached_weather.json"

@st.cache_data(show_spinner=True)
def fetch_weather(city):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": UNITS}
    return requests.get(url, params=params).json()

@st.cache_data
def fetch_alerts(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": UNITS, "exclude": "minutely,hourly,daily"}
    return requests.get(url, params=params).json()

# Attempt fetch or load cached
data = None
if submit:
    data = fetch_weather(city)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
elif os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        data = json.load(f)
        st.warning("No request sent. Showing cached data.")

# Display
if data:
    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message')}")
    else:
        st.header(f"{city} – {LANG[lang]['temp']} & {LANG[lang]['humidity']}")
        forecasts = data["list"]
        current = forecasts[0]
        st.metric(LANG[lang]['temp'], f"{current['main']['temp']}°C")
        st.metric(LANG[lang]['humidity'], f"{current['main']['humidity']}%")
        st.metric(LANG[lang]['wind'], f"{current['wind']['speed']} m/s")

        # Show simple hourly table
        times = [f["dt_txt"] for f in forecasts[:6]]
        temps = [f["main"]["temp"] for f in forecasts[:6]]
        hums = [f["main"]["humidity"] for f in forecasts[:6]]
        df = pd.DataFrame({"Time": times, LANG[lang]['temp']: temps, LANG[lang]['humidity']: hums})
        st.dataframe(df)

        # ALERTS
        lat = data["city"]["coord"]["lat"]
        lon = data["city"]["coord"]["lon"]
        alert_data = fetch_alerts(lat, lon)
        if "alerts" in alert_data:
            st.subheader(f"⚠️ {LANG[lang]['alerts']}")
            for alert in alert_data["alerts"]:
                st.error(f"{alert['event']}: {alert['description'][:200]}...")

# Voice Input UI placeholder
st.markdown("---")
st.info("🎤 Voice input and full PWA support coming soon in final phase!")
