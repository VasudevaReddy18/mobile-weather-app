
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import folium
from streamlit_folium import st_folium

# PAGE SETUP
st.set_page_config(page_title="Pro Weather App", layout="centered")

# SESSION STATE INIT
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
if "stored_city" not in st.session_state:
    st.session_state.stored_city = ""

# Location Detection
@st.cache_data
def detect_location():
    try:
        ip_info = requests.get("https://ipinfo.io/json").json()
        return ip_info.get("city", "New York")
    except:
        return "New York"

# API Setup
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "your_openweathermap_api_key_here"

# UI
st.sidebar.title("Settings")
units = st.sidebar.radio("Units", ["Celsius", "Fahrenheit", "Kelvin"])
city_input = st.sidebar.text_input("City Name (leave blank to auto-detect)", "")
submit = st.sidebar.button("Get Weather")

# Units setup
unit_map = {"Celsius": "metric", "Fahrenheit": "imperial", "Kelvin": "standard"}
unit_symbol = {"Celsius": "°C", "Fahrenheit": "°F", "Kelvin": "K"}
api_units = unit_map[units]
symbol = unit_symbol[units]

# Weather fetcher
@st.cache_data(show_spinner=True)
def fetch_weather(city, units):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": units}
    return requests.get(url, params=params).json()

# Wind direction helper
def wind_direction(degree):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = int((degree + 22.5) // 45) % 8
    return dirs[ix]

# Handle user input and store results
if submit:
    city = city_input.strip() if city_input else detect_location()
    st.session_state.weather_data = fetch_weather(city, api_units)
    st.session_state.stored_city = city

# Main display
st.title("🌍 Pro Weather App")

if st.session_state.weather_data:
    city = st.session_state.stored_city
    data = st.session_state.weather_data

    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message')}")
    else:
        forecasts = data["list"]
        lat = data["city"]["coord"]["lat"]
        lon = data["city"]["coord"]["lon"]

        # Parse forecast
        times, temps, hums, winds, wind_dirs, rains = [], [], [], [], [], []
        for f in forecasts:
            dt = datetime.strptime(f["dt_txt"], "%Y-%m-%d %H:%M:%S")
            times.append(dt)
            temps.append(f["main"]["temp"])
            hums.append(f["main"]["humidity"])
            wind_speed = f["wind"]["speed"]
            wind_deg = f["wind"]["deg"]
            winds.append(wind_speed)
            wind_dirs.append(wind_direction(wind_deg))
            rains.append(f.get("rain", {}).get("3h", 0))

        df = pd.DataFrame({
            "Datetime": times,
            f"Temperature ({symbol})": temps,
            "Humidity (%)": hums,
            f"Wind Speed ({'m/s' if api_units != 'imperial' else 'mph'})": winds,
            "Wind Direction": wind_dirs,
            "Rainfall (mm)": rains
        })

        tab1, tab2 = st.tabs(["📍 Current", "📆 Forecast"])

        with tab1:
            st.subheader(f"Weather in {city}")
            st.metric("Temperature", f"{temps[0]} {symbol}")
            st.metric("Humidity", f"{hums[0]}%")
            st.metric("Wind", f"{winds[0]} {'m/s' if api_units != 'imperial' else 'mph'} {wind_dirs[0]}")

            m = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon], tooltip=city).add_to(m)
            st_folium(m, height=350, width=700)

        with tab2:
            st.subheader("Hourly Forecast")
            st.line_chart(df.set_index("Datetime")[[f"Temperature ({symbol})", "Humidity (%)"]])
            st.subheader("📋 Forecast Table")
            st.dataframe(df)
