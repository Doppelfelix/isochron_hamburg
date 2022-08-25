import streamlit as st


st.title("Isochron Map for Walking distances in Hamburg")


def render_map(url):
    with open("pages/maps/" + url, "r") as f:
        html_data = f.read()

    st.components.v1.html(html_data, width=700, height=700)


url_dict = {
    "Bike Stations": "hamburg_bike_darker",
    "Subway/-urban Stations": "hamburg_hvv_darker",
    "Both": "hamburg_all_darker",
}

map_source = st.radio(
    "Select View:", options=["Bike Stations", "Subway/-urban Stations", "Both"]
)
n_nodes = st.radio(
    "Number of Nodes (Warning 15k won't work on Firefox):",
    options=[10000, 15000],
    index=0,
)


url = f"{url_dict[map_source]}_{n_nodes}.html"

render_map(url)
