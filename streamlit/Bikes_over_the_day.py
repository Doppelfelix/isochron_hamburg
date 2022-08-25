import calendar
import math

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


st.title("City bike availability in Hamburg over the week")


df = pd.read_csv("input_data/station_df.csv")
max = math.ceil(df.average_res.max())


def draw_map(hour, day):
    unique_coords = df.query(f"resultHour == {hour} and resultWeekday == {day}")

    colormap = cm.LinearColormap(
        colors=[
            "#0d0887",
            "#cc4778",
            "#f0f921",
        ],
        index=[0, max / 2, max],
        vmin=0,
        vmax=max,
    )

    m = folium.Map(
        location=[53.555, 9.9914],
        zoom_start=12,
        tiles="OpenStreetMap",
        no_touch=True,
        prefer_canvas=True,
        max_bounds=[53.555, 9.9914],
    )

    for index, val in unique_coords.iterrows():
        folium.Circle(
            location=[val["coordinatesY"], val["coordinatesX"]],
            radius=150,
            stroke=False,
            fill=True,
            color=colormap(val["average_res"]),
            fill_opacity=0.7,
            interactive=False,
        ).add_to(m)

    colormap.caption = "Number of Bikes at station"
    colormap.add_to(m)

    st_data = st_folium(m, width=725)


day_dict = {}
for i in range(7):
    day_dict[calendar.day_name[i]] = i + 1

hour = 9
day = "Tuesday"


hour = st.slider("Hour of the day", 0, 23, value=9)


day = st.select_slider("Day of the week", options=day_dict.keys(), value="Tuesday")

draw_map(hour, day_dict[day])
