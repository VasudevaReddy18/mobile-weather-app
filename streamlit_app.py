
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Ultimate Weather App", layout="centered")

# Language support
LANG = {
    "en": {"temp": "Temperature", "humidity": "Humidity", "wind": "Wind", "alerts": "Weather Alerts"},
    "hi": {"temp": "तापमान", "humidity": "नमी", "wind": "पवन", "alerts": "मौसम चेतावनी"},
    "te": {"temp": "ఉష్ణోగ్రత", "humidity": "ఆర్ద్రత", "wind": "గాలి", "alerts": "వాతావరణ హెచ్చరికలు"}
}

# Select language
lang = st.sidebar.selectbox("Language", options=["en", "hi", "te"], format_func=lambda x: {"en": "English", "hi": "Hindi", "te": "Telugu"}[x])

# API key
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "your_openweathermap_api_key_here"
UNITS = "metric"
CACHE_FILE = "cached_weather.json"

# City input
city = st.sidebar.text_input("Enter city name", "Hyderabad")
submit = st.sidebar.button("Get Weather")

# Weather emoji mapper
def get_weather_emoji(condition):
    condition = condition.lower()
    if "cloud" in condition:
        return "☁️"
    elif "rain" in condition:
        return "🌧️"
    elif "clear" in condition:
        return "☀️"
    elif "storm" in condition or "thunder" in condition:
        return "🌩️"
    elif "snow" in condition:
        return "❄️"
    else:
        return "🌈"

# Background style based on weather
def get_background_style(weather_main):
    if "clear" in weather_main.lower():
        return "background-color: #87CEEB;"
    elif "rain" in weather_main.lower():
        return "background-color: #a9a9a9;"
    elif "snow" in weather_main.lower():
        return "background-color: #f0f8ff;"
    elif "thunderstorm" in weather_main.lower():
        return "background-color: #4b0082;"
    else:
        return "background-color: #ffffff;"

# Direction helper
def wind_direction(degree):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = int((degree + 22.5) // 45) % 8
    return dirs[ix]

@st.cache_data(show_spinner=True)
def fetch_weather(city):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": UNITS}
    return requests.get(url, params=params).json()

@st.cache_data(show_spinner=True)
def fetch_alerts(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": UNITS, "exclude": "minutely,hourly,daily"}
    return requests.get(url, params=params).json()

data = None
if submit:
    data = fetch_weather(city)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
elif os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        data = json.load(f)
        st.warning("⚠️ Showing cached data.")

# DISPLAY WEATHER
if data:
    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message')}")
    else:
        forecasts = data["list"]
        lat = data["city"]["coord"]["lat"]
        lon = data["city"]["coord"]["lon"]
        weather_main = forecasts[0]["weather"][0]["main"]
        weather_icon = get_weather_emoji(weather_main)
        bg_style = get_background_style(weather_main)
        st.markdown(f"<style>.stApp {{{bg_style}}}</style>", unsafe_allow_html=True)

        st.title(f"{weather_icon} {city} Weather")
        st.metric(LANG[lang]["temp"], f"{forecasts[0]['main']['temp']}°C")
        st.metric(LANG[lang]["humidity"], f"{forecasts[0]['main']['humidity']}%")
        st.metric(LANG[lang]["wind"], f"{forecasts[0]['wind']['speed']} m/s {wind_direction(forecasts[0]['wind']['deg'])}")

        # Forecast DataFrame
        times, temps, hums, winds, wind_dirs, rains = [], [], [], [], [], []
        for f in forecasts:
            dt = datetime.strptime(f["dt_txt"], "%Y-%m-%d %H:%M:%S")
            times.append(dt)
            temps.append(f["main"]["temp"])
            hums.append(f["main"]["humidity"])
            winds.append(f["wind"]["speed"])
            wind_dirs.append(wind_direction(f["wind"]["deg"]))
            rains.append(f.get("rain", {}).get("3h", 0))

        df = pd.DataFrame({
            "Datetime": times,
            f"🌡️ {LANG[lang]['temp']} (°C)": temps,
            f"💧 {LANG[lang]['humidity']} (%)": hums,
            "💨 Wind Speed (m/s)": winds,
            "🌬️ Wind Dir": wind_dirs,
            "🌧️ Rain (mm)": rains
        })

        tab1, tab2 = st.tabs(["📍 Current", "📆 Forecast"])

        with tab1:
            m = folium.Map(location=[lat, lon], zoom_start=10)
            popup = f"{weather_icon} {city}<br>{temps[0]}°C"
            folium.Marker([lat, lon], tooltip=popup).add_to(m)

            # Animated cloud overlay
            tile_url = f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"
            folium.raster_layers.TileLayer(tiles=tile_url, name="Clouds", attr="OpenWeather").add_to(m)
            st_folium(m, height=350, width=700)

        with tab2:
            st.subheader("📈 Hourly Forecast")
            temp_col = [col for col in df.columns if "Temperature" in col or "तापमान" in col or "ఉష్ణోగ్రత" in col][0]
            hum_col = [col for col in df.columns if "Humidity" in col or "नमी" in col or "ఆర్ద్రత" in col][0]
            st.line_chart(df.set_index("Datetime")[[temp_col, hum_col]])
            st.subheader("📋 Forecast Table")
            st.dataframe(df)

        # Alerts
        alert_data = fetch_alerts(lat, lon)
        if "alerts" in alert_data:
            st.subheader(f"⚠️ {LANG[lang]['alerts']}")
            for alert in alert_data["alerts"]:
                st.error(f"{alert['event']}: {alert['description'][:300]}...")

# Voice assistant placeholder
st.markdown("---")
st.info("🎤 Voice search support coming soon!")
