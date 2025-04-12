
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="Mobile Weather App", layout="centered")

# SIDEBAR INPUTS
st.sidebar.title("Settings")
API_KEY = API_KEY = st.secrets["API_KEY"] 
city = st.sidebar.text_input("City Name", "New York")
units = st.sidebar.selectbox("Units", ["metric", "imperial"])
submit = st.sidebar.button("Get Weather")

# FETCH WEATHER
def fetch_weather(city_name, units):
    url = f"http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city_name,
        "appid": API_KEY,
        "units": units
    }
    response = requests.get(url, params=params)
    return response.json()

# MAIN DISPLAY
st.title("📱 Weather Forecast")

if submit:
    if API_KEY == "your_openweathermap_api_key_here":
        st.error("Please enter your OpenWeatherMap API key in the script.")
    else:
        data = fetch_weather(city, units)
        if data.get("cod") != "200":
            st.error(f"Error fetching data: {data.get('message', 'Unknown error')}")
        else:
            st.success(f"Showing forecast for {city}")

            # Parse Data
            forecasts = data["list"]
            times, temps, humidities, wind_speeds, rains = [], [], [], [], []

            for f in forecasts:
                dt = datetime.strptime(f["dt_txt"], "%Y-%m-%d %H:%M:%S")
                times.append(dt)
                temps.append(f["main"]["temp"])
                humidities.append(f["main"]["humidity"])
                wind_speeds.append(f["wind"]["speed"])
                rains.append(f.get("rain", {}).get("3h", 0))

            df = pd.DataFrame({
                "Datetime": times,
                "Temperature": temps,
                "Humidity": humidities,
                "Wind Speed": wind_speeds,
                "Rain (mm)": rains
            })

            # Display Key Metrics
            st.metric("Current Temperature", f"{temps[0]}°")
            st.metric("Humidity", f"{humidities[0]}%")
            st.metric("Wind Speed", f"{wind_speeds[0]} { 'm/s' if units=='metric' else 'mph' }")

            # Line Charts
            st.subheader("📊 Trends")
            st.line_chart(df.set_index("Datetime")[["Temperature", "Humidity", "Wind Speed", "Rain (mm)"]])

            # Data Table
            st.subheader("📋 Forecast Data")
            st.dataframe(df)
