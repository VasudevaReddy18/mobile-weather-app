
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Ultimate Weather PWA", layout="centered")

# API Key
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "your_openweathermap_api_key"
UNITS = "metric"
CACHE_FILE = "cached_weather.json"

# Sidebar
st.sidebar.title("🌍 Settings + 🎙️ Voice Input")
st.sidebar.text("🎤 Voice search coming soon!")
st.sidebar.button("🎙️ Speak")

city = st.sidebar.text_input("Enter city name", "Hyderabad")
submit = st.sidebar.button("Get Weather")

# Fetch weather
@st.cache_data(show_spinner=True)
def fetch_weather(city):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": UNITS}
    return requests.get(url, params=params).json()

@st.cache_data
def fetch_alerts(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": UNITS, "exclude": "minutely,hourly,daily"}
    return requests.get(url, params=params).json()

# Emoji for weather condition
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

# Wind direction
def wind_direction(degree):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = int((degree + 22.5) // 45) % 8
    return dirs[ix]

data = None
if submit:
    data = fetch_weather(city)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
elif os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        data = json.load(f)
        st.warning("⚠️ Using cached data.")

# Display weather
if data:
    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message')}")
    else:
        forecasts = data["list"]
        city_info = data["city"]
        lat = city_info["coord"]["lat"]
        lon = city_info["coord"]["lon"]

        current = forecasts[0]
        main = current["weather"][0]["main"]
        emoji = get_weather_emoji(main)

        st.title(f"{emoji} {city} Weather")
        st.metric("🌡️ Temp", f"{current['main']['temp']}°C")
        st.metric("💧 Humidity", f"{current['main']['humidity']}%")
        st.metric("💨 Wind", f"{current['wind']['speed']} m/s {wind_direction(current['wind']['deg'])}")

        times = []
        temps = []
        hums = []
        winds = []
        dirs = []
        rain = []

        for f in forecasts:
            dt = datetime.strptime(f["dt_txt"], "%Y-%m-%d %H:%M:%S")
            times.append(dt)
            temps.append(f["main"]["temp"])
            hums.append(f["main"]["humidity"])
            winds.append(f["wind"]["speed"])
            dirs.append(wind_direction(f["wind"]["deg"]))
            rain.append(f.get("rain", {}).get("3h", 0))

        df = pd.DataFrame({
            "Datetime": times,
            "🌡️ Temperature (°C)": temps,
            "💧 Humidity (%)": hums,
            "💨 Wind Speed (m/s)": winds,
            "🌬️ Wind Dir": dirs,
            "🌧️ Rain (mm)": rain
        })

        tab1, tab2 = st.tabs(["📍 Current + Map", "📆 Forecast"])

        with tab1:
            m = folium.Map(location=[lat, lon], zoom_start=9)
            popup = f"{emoji} {city}<br>{temps[0]}°C"
            folium.Marker([lat, lon], tooltip=popup, popup=popup).add_to(m)

            # Animated cloud overlay
            cloud_tile = f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"
            folium.raster_layers.TileLayer(tiles=cloud_tile, name="Clouds", attr="OpenWeather").add_to(m)

            st_folium(m, height=350, width=700)

        with tab2:
            st.subheader("📈 Hourly Chart")
            st.line_chart(df.set_index("Datetime")[["🌡️ Temperature (°C)", "💧 Humidity (%)"]])
            st.subheader("📋 Forecast Table")
            st.dataframe(df)

        alerts = fetch_alerts(lat, lon)
        if "alerts" in alerts:
            st.subheader("⚠️ Weather Alerts")
            for alert in alerts["alerts"]:
                st.error(f"{alert['event']}: {alert['description'][:300]}...")
