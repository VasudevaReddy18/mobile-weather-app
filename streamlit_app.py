
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import folium
from streamlit_folium import st_folium

# PAGE SETUP
st.set_page_config(page_title="Mobile Weather App", layout="centered")

# SIDEBAR SETTINGS
st.sidebar.title("Settings")
API_KEY = API_KEY = st.secrets["API_KEY"] 
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "your_openweathermap_api_key_here"
city = st.sidebar.text_input("City Name", "New York")
units = st.sidebar.radio("Units", ["Celsius", "Fahrenheit", "Kelvin"])
dark_mode = st.sidebar.toggle("Dark Mode")
submit = st.sidebar.button("Get Weather")

# APPLY DARK MODE STYLES
if dark_mode:
    st.markdown("""
        <style>
        body, .stApp {
            background-color: #0e1117;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

# UNIT MAPS
unit_map = {"Celsius": "metric", "Fahrenheit": "imperial", "Kelvin": "standard"}
unit_symbol = {"Celsius": "°C", "Fahrenheit": "°F", "Kelvin": "K"}
api_units = unit_map[units]
symbol = unit_symbol[units]

# WIND DIRECTION FUNCTION
def wind_direction(degree):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = int((degree + 22.5) // 45) % 8
    return dirs[ix]

# WEATHER FETCH
@st.cache_data(show_spinner=True)
def fetch_weather(city, units):
    url = f"http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": units}
    return requests.get(url, params=params).json()

# MAIN APP LOGIC
st.title("🌤️ Mobile Weather App")

if submit:
    if API_KEY == "your_openweathermap_api_key_here":
        st.error("Please set your OpenWeatherMap API key in Streamlit secrets.")
    else:
        data = fetch_weather(city, api_units)
        if data.get("cod") != "200":
            st.error(f"Error: {data.get('message')}")
        else:
            forecasts = data["list"]
            lat = data["city"]["coord"]["lat"]
            lon = data["city"]["coord"]["lon"]

            # Build DataFrame
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

            tab1, tab2 = st.tabs(["📍 Current", "📅 Forecast"])

            with tab1:
                st.subheader(f"Weather in {city}")
                st.metric("Temperature", f"{temps[0]} {symbol}")
                st.metric("Humidity", f"{hums[0]}%")
                st.metric("Wind", f"{winds[0]} {'m/s' if api_units != 'imperial' else 'mph'} {wind_dirs[0]}")

                st.subheader("📌 Location Map")
                m = folium.Map(location=[lat, lon], zoom_start=10)
                folium.Marker([lat, lon], tooltip=city).add_to(m)
                st_folium(m, height=350, width=700)

            with tab2:
                st.subheader("📈 Forecast Charts")
                st.line_chart(df.set_index("Datetime")[[f"Temperature ({symbol})", "Humidity (%)", f"Wind Speed ({'m/s' if api_units != 'imperial' else 'mph'})", "Rainfall (mm)"]])
                with st.expander("📋 Detailed Forecast Table"):
                    st.dataframe(df)
