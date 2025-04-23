import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import logging
import time
# from datetime import datetime

# Настройка логирования
logging.basicConfig(filename="weather_errors.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Настройки
API_KEY = "d54210e764604bb037209cd2c5534456"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"
DEFAULT_CITIES = ["London", "Moscow", "Tokyo", "Saint Petersburg", "Paris", "Sydney"]

# Функция для получения прогноза
def fetch_forecast(city, api_key, language="ru"):
    params = {
        "q": city.strip(),
        "appid": api_key,
        "units": "metric",
        "lang": language
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"URL запроса для {city}: {response.url}")
        logging.debug(f"Код состояния для {city}: {response.status_code}")
        logging.debug(f"Ответ API для {city}: {data}")
        if data.get("cod") != "200":
            error_message = data.get("message", "Неизвестная ошибка")
            logging.error(f"Ошибка API для {city}: {error_message}, cod: {data.get('cod')}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса для {city}: {e}")
        return None

# Функция для обработки прогноза
def process_forecast(data, city):
    weather_data = []
    if not data or "list" not in data:
        return weather_data
    for forecast in data["list"]:
        time_forecast = forecast.get("dt_txt", "N/A")
        temperature = forecast.get("main", {}).get("temp", "N/A")
        humidity = forecast.get("main", {}).get("humidity", "N/A")
        description = forecast.get("weather", [{}])[0].get("description", "N/A")
        wind_speed = forecast.get("wind", {}).get("speed", "N/A")
        pressure = forecast.get("main", {}).get("pressure", "N/A")

        weather_data.append({
            "city": city,
            "time": time_forecast,
            "temperature": temperature,
            "humidity": humidity,
            "description": description,
            "wind_speed": wind_speed,
            "pressure": pressure,
        })
    return weather_data

# Streamlit интерфейс
st.title("Прогноз погоды на 5 дней")

# Выбор или ввод города
st.sidebar.header("Настройки")
city_input = st.sidebar.text_input("Введите город (например, Tokyo,JP):", "Moscow")
city_select = st.sidebar.multiselect("Или выберите города:", DEFAULT_CITIES, default=["Moscow"])
cities = city_select + ([city_input] if city_input and city_input not in city_select else [])

# Выбор языка
language = st.sidebar.selectbox("Язык прогноза:", ["ru", "en", "fr"], index=0)

# Кнопка для получения прогноза
if st.button("Получить прогноз"):
    if not cities:
        st.error("Пожалуйста, выберите или введите хотя бы один город.")
    else:
        with st.spinner("Получаем прогноз..."):
            weather_data = []
            for city in cities:
                # Получение и обработка прогноза
                data = fetch_forecast(city, API_KEY, language)
                if data:
                    weather_data.extend(process_forecast(data, city))
                else:
                    st.error(f"Не удалось получить прогноз для {city}.")
                time.sleep(1)  # Задержка для предотвращения лимитов

            # Создание DataFrame
            df = pd.DataFrame(weather_data)
            if not df.empty:
                # Преобразование типов
                df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
                df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")
                df["wind_speed"] = pd.to_numeric(df["wind_speed"], errors="coerce")
                df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce")
                df["time"] = pd.to_datetime(df["time"])

                # Отображение таблицы
                st.subheader("Прогноз погоды")
                st.dataframe(df[["city", "time", "temperature", "humidity", "description", "wind_speed", "pressure"]])

                # Сохранение в CSV
                csv_file = "weather_forecast.csv"
                df.to_csv(csv_file, encoding="utf-8", index=False)
                try:
                    pd.read_csv(csv_file)
                    st.success(f"Данные сохранены в {csv_file}")
                    logging.info(f"Данные сохранены в {csv_file}")
                    # Кнопка для скачивания
                    with open(csv_file, "rb") as f:
                        st.download_button("Скачать CSV", f, file_name=csv_file)
                except Exception as e:
                    st.error(f"Ошибка при сохранении CSV: {e}")
                    logging.error(f"Ошибка при сохранении CSV: {e}")

                # Построение графика
                st.subheader("График температуры")
                fig = px.line(df, x="time", y="temperature", color="city", title="Температура по времени",
                              labels={"time": "Время", "temperature": "Температура (°C)", "city": "Город"})
                st.plotly_chart(fig, use_container_width=True)

                # График средней температуры
                st.subheader("Средняя температура по городам")
                avg_temps = df.groupby("city")["temperature"].mean().reset_index()
                fig_avg = px.bar(avg_temps, x="city", y="temperature", title="Средняя температура",
                                 labels={"city": "Город", "temperature": "Температура (°C)"}, color="temperature")
                st.plotly_chart(fig_avg, use_container_width=True)

            else:
                st.error("Нет данных для отображения.")
                logging.warning("DataFrame пуст")

else:
    st.info("Введите город или выберите города и нажмите 'Получить прогноз'.")