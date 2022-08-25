colormap = cm.LinearColormap(colors=iso_colors)
colormap = colormap.to_step(index=range(0, 51, 5))

import folium

m = folium.Map(
    location=[53.555, 9.9914],
    zoom_start=12,
    prefer_canvas=True,
)


for val in coords.values():
    folium.Circle(
        location=[val["y"], val["x"]],
        radius=50,
        stroke=False,
        fill=True,
        color=val["color"],
        fill_opacity=0.3,
        interactive=True,
    ).add_to(m)
colormap.add_to(m)
m
