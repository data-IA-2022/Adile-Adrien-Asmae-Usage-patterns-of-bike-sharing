import requests
import pandas as pd
import re
import folium
import branca.colormap as cm


def extract_lat_lng(point_str):
    match = re.match(r"POINT\(([-.\d]+) ([-.\d]+)\)", point_str)
    if match:
        lng, lat = float(match.group(1)), float(match.group(2))
        return lat, lng
    else:
        return None, None


data = pd.read_csv('Station_Bike_2015-2017_scored.csv')

data = data.dropna(subset="cluster_labels")


data['lat'], data['lng'] = zip(*data['GeoPoint'].apply(extract_lat_lng))

color_scale = cm.LinearColormap(['darkblue', 'dodgerblue', 'limegreen', 'gold', 'darkorange', 'red', 'magenta'], vmin=0, vmax=210000)
color_scale.caption = 'Nombre de trajets'


def draw_lines_between_stations(m, data, station_col, main_station_col):
    for index, row in data.iterrows():
        main_station = row[main_station_col]
        other_station = row[station_col]

        main_station_data = data.loc[data['terminalName'] == main_station, ['lat', 'lng', 'total count']]
        other_station_data = data.loc[data['terminalName'] == other_station, ['lat', 'lng']]

        if not main_station_data.empty and not other_station_data.empty:
            main_station_coords = main_station_data[['lat', 'lng']].values[0]
            other_station_coords = other_station_data[['lat', 'lng']].values[0]
            total_count = main_station_data['total count'].values[0]

            line_color = color_scale(total_count)

            folium.PolyLine([main_station_coords, other_station_coords],
                            color=line_color, weight=5, opacity = 0.6).add_to(m)


def add_markers(m, data):
    for index, row in data.iterrows():
        lat, lng = row['lat'], row['lng']
        cluster_id = int(row['cluster_labels'][-1])
        cluster_name = f"cluster {cluster_id}"

        popup = folium.Popup(cluster_name, max_width=300)

        colors = ['#F37735', '#D11141', '#91268F', '#194BA3', '#8CC63F', '#FFC425', '#00AEDB']

        folium.CircleMarker([lat, lng], radius = 25, popup = popup, fillColor = colors[cluster_id], stroke = False, fillOpacity = 0.6).add_to(m)


m = folium.Map(location=[38.8951100, -77.0363700], zoom_start=15, tiles='cartodb positron')

add_markers(m, data)

for station_col in ['most frequent station', 'second most frequent station', 'third most frequent station']:
    draw_lines_between_stations(m, data, station_col, 'terminalName')

color_scale.add_to(m)

locations = [
    "Georgetown, Washington, DC",
    "United States Capitol, Washington, DC",
    "Supreme Court of the United States, Washington, DC",
    "The White House, Washington, DC",
    "Washington Monument, Washington, DC",
    "Constitution Gardens, Washington, DC",
    "Lincoln Memorial, Washington, DC"
]


def get_coordinates(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        return [lat, lon]
    return None


for location in locations:
    coords = get_coordinates(location)
    if coords:
        folium.Marker(coords, popup=location).add_to(m)

m.save('lines_and_spots_2015_2017.html')
