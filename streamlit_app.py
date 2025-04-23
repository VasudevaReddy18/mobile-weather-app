import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Pro Weather App", layout="wide")

# Session state
if "city" not in st.session_state:
    st.session_state.city = "New York"
if "data" not in st.session_state:
    st.session_state.data = {}

# Sidebar settings
st.sidebar.title("Settings")
unit = st.sidebar.radio("Units", ["metric", "imperial"])
symbol = "°C" if unit == "metric" else "°F"
city = st.sidebar.text_input("Enter city", st.session_state.city)
submit = st.sidebar.button("Get Weather")

# Fetch weather
def get_weather(city, unit):
    API_KEY = "your_api_key_here"  # replace on Streamlit Cloud with secrets
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": unit}
    response = requests.get(url, params=params).json()
    return response

# Parse and display
def render_forecast(data):
    st.subheader(f"📍 Forecast for {data['city']['name']}")
    forecasts = data["list"]
    times, temps, hums = [], [], []
    for entry in forecasts:
        dt = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
        times.append(dt)
        temps.append(entry["main"]["temp"])
        hums.append(entry["main"]["humidity"])

    df = pd.DataFrame({"Time": times, f"Temp ({symbol})": temps, "Humidity (%)": hums})
    st.line_chart(df.set_index("Time")[[f"Temp ({symbol})", "Humidity (%)"]])
    st.dataframe(df)

# App layout
st.title("🌦️ Pro Weather App - Final Version")
if submit:
    st.session_state.city = city
    data = get_weather(city, unit)
    if data.get("cod") == "200":
        st.session_state.data = data
    else:
        st.error("City not found or API error.")

if st.session_state.data:
    render_forecast(st.session_state.data)

# Tabs for new features (placeholders for now)
tab1, tab2, tab3 = st.tabs(["🌍 Multi-City", "🎙️ Voice Input", "👕 AI Clothing Tips"])
with tab1:
    st.write("Compare multiple cities - Coming Soon")
with tab2:
    st.write("Voice input integration - Coming Soon")
with tab3:
    st.write("Based on humidity/temperature - Suggest light clothes or jacket")

st.markdown("---")
st.caption("🔁 Unified version of Real Weather App with full forecast and future features")
