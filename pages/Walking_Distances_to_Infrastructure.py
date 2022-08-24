import streamlit as st


st.title('Isochron Map for Walking distances in Hamburg')

def render_map(url):
    with open("pages/maps/" + url,'r') as f: 
        html_data = f.read()

    st.components.v1.html(html_data, width=700, height=700)


url_dict = {
"Bike Stations":"hamburg_bike_darker.html",
"Subway/-urban Stations":"hamburg_hvv_darker.html",
"Both":"hamburg_all_darker.html",

}

map_source = st.radio("Select View:", options=["Bike Stations", "Subway/-urban Stations", "Both"])
render_map(url_dict[map_source])