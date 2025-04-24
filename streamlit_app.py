
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Real Weather App", layout="wide")
API_KEY = "c2dcf9d6f8c83d0bf6cd5c937aaad189"

@st.cache_data
def detect_location():
    try:
        loc = requests.get("https://ipinfo.io/json").json()
        return loc.get("city", "New York")
    except:
        return "New York"

@st.cache_data
def fetch_weather(city, units):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": units}
    return requests.get(url, params=params).json()

def wind_direction(deg):
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[int((deg + 22.5)//45) % 8]

st.sidebar.title("Settings")
units_display = st.sidebar.radio("Units", ["Celsius", "Fahrenheit", "Kelvin"])
unit_map = {"Celsius": "metric", "Fahrenheit": "imperial", "Kelvin": "standard"}
unit_symbol = {"Celsius": "°C", "Fahrenheit": "°F", "Kelvin": "K"}
speed_unit = {"Celsius": "m/s", "Fahrenheit": "mph", "Kelvin": "m/s"}

units = unit_map[units_display]
symbol = unit_symbol[units_display]
speed = speed_unit[units_display]

city_input = st.sidebar.text_input("City (leave blank to auto-detect)", "")
st.sidebar.markdown("🎤 Try using your microphone to search by voice (supported browsers only).")
submit = st.sidebar.button("Get Weather")

if submit:
    city = city_input if city_input else detect_location()
    data = fetch_weather(city, units)
    st.session_state.city = city
    st.session_state.data = data

if "data" not in st.session_state:
    st.session_state.city = detect_location()
    st.session_state.data = fetch_weather(st.session_state.city, units)

data = st.session_state.data
city = st.session_state.city

if data.get("cod") != "200":
    st.error(f"API Error: {data.get('message')}")
else:
    st.title(f"🌈 Real Weather App — {city}")
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Current", "📈 Forecast", "🗺️ Map", "👕 AI Tips"])

    forecasts = data["list"]
    lat = data["city"]["coord"]["lat"]
    lon = data["city"]["coord"]["lon"]

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
        f"🌡️ Temp ({symbol})": temps,
        "💧 Humidity (%)": hums,
        f"💨 Wind ({speed})": winds,
        "🌬️ Direction": wind_dirs,
        "🌧️ Rain (mm)": rains
    })

    with tab1:
        st.metric("🌡️ Temp", f"{temps[0]} {symbol}")
        st.metric("💧 Humidity", f"{hums[0]}%")
        st.metric("💨 Wind", f"{winds[0]} {speed} {wind_dirs[0]}")

    with tab2:
        st.subheader("📊 Forecast Chart")
        st.line_chart(df.set_index("Datetime")[[f"🌡️ Temp ({symbol})", "💧 Humidity (%)"]])
        st.subheader("📋 Full Forecast Table")
        st.dataframe(df)

    with tab3:
        m = folium.Map(location=[lat, lon], zoom_start=7)
        folium.Marker([lat, lon], tooltip=f"{city}").add_to(m)
        tile_url = f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"
        folium.raster_layers.TileLayer(tiles=tile_url, attr="Clouds").add_to(m)
        st_folium(m, height=400, width=700)

    with tab4:
        tip = "👕 Wear light clothes!" if temps[0] > 30 else "🧥 It's cool, wear a jacket!"
        st.success(tip)

st.markdown("---")
st.caption("🌤️ Full Weather App | Forecast + Radar + AI Tips + Auto Location + Voice Search (Browser Only)")
