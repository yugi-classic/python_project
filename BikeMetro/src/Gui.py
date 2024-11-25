import streamlit as st
import folium
from shapely.geometry import Point
from streamlit_folium import st_folium
from Calculator import Calculator


class Gui:
    def __init__(self):
        self.map()

    """
        Display the main interface with options to select tasks and input positions.
    
        This function manages the user input for selecting tasks and entering positions,
        and displays the corresponding map based on the selected task.
    """

    def map(self):
        st.title("OpenStreetMap: Applied Data Science with Python")
        default_position = Point(-118.243, 34.0522)
        default_position_src = Point(-118.26095, 34.0684)
        default_position_dest = Point(-118.2915, 34.08905)
        default_bike_stations = 5
        option = st.selectbox("Select Task", ("Bikes Available", "Docks Available", "Route"), index=0)

        # Initialize session state for inputs if not already done
        if 'bike_stations' not in st.session_state:
            st.session_state.bike_stations = str(default_bike_stations)
        if 'lat_position' not in st.session_state:
            st.session_state.lat_position = str(default_position.y)
        if 'lon_position' not in st.session_state:
            st.session_state.lon_position = str(default_position.x)
        if 'lat_position_src' not in st.session_state:
            st.session_state.lat_position_src = str(default_position_src.y)
        if 'lon_position_src' not in st.session_state:
            st.session_state.lon_position_src = str(default_position_src.x)
        if 'lat_position_dest' not in st.session_state:
            st.session_state.lat_position_dest = str(default_position_dest.y)
        if 'lon_position_dest' not in st.session_state:
            st.session_state.lon_position_dest = str(default_position_dest.x)
        if 'map_updated' not in st.session_state:
            st.session_state.map_updated = False

        # Display map with or without updates based on submit button
        if option == "Route":
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.lat_position_src = st.text_input("Enter Source Latitude",
                                                                  value=st.session_state.lat_position_src,
                                                                  key="lat_position_src_input")
                st.session_state.lon_position_src = st.text_input("Enter Source Longitude",
                                                                  value=st.session_state.lon_position_src,
                                                                  key="lon_position_src_input")
            with col2:
                st.session_state.lat_position_dest = st.text_input("Enter Destination Latitude",
                                                                   value=st.session_state.lat_position_dest,
                                                                   key="lat_position_dest_input")
                st.session_state.lon_position_dest = st.text_input("Enter Destination Longitude",
                                                                   value=st.session_state.lon_position_dest,
                                                                   key="lon_position_dest_input")
            submitted = st.button("Submit")
            if submitted:
                st.session_state.map_updated = True
            self.route_map(st.session_state.lat_position_src, st.session_state.lon_position_src, option)
        else:
            # Text inputs for bike station and position
            st.session_state.bike_stations = st.text_input(f"Enter Station Number! ({option})",
                                                           value=st.session_state.bike_stations)
            st.session_state.lat_position = st.text_input(f"Enter Latitude ({option})",
                                                          value=st.session_state.lat_position)
            st.session_state.lon_position = st.text_input(f"Enter Longitude ({option})",
                                                          value=st.session_state.lon_position)
            submitted = st.button("Submit")
            if submitted:
                st.session_state.map_updated = True
            self.generate_map(option, st.session_state.bike_stations, st.session_state.lat_position,
                              st.session_state.lon_position)

    """
        Generate and display the map based on the selected task and user input.
    
        Parameters:
        option (str): The selected task (Bikes Available, Docks Available).
        default_bike_stations (str): The default number of bike stations to display.
        lat_position (str): The latitude of the current position.
        lon_position (str): The longitude of the current position.
    """

    def generate_map(self, option, default_bike_stations, lat_position, lon_position):
        try:
            lat_position_float = float(lat_position)
            lon_position_float = float(lon_position)
            current_position = self.current_position(lat_position_float, lon_position_float)
            folium_map = folium.Map(location=(lat_position, lon_position), crs="EPSG3857", zoom_start=20)
        except ValueError:
            st.error("Please enter valid numbers for latitude and longitude.")
            return

        if st.session_state.map_updated:
            calculator = Calculator(option)

            try:
                default_bike_stations = int(default_bike_stations)
            except ValueError:
                st.error("Please enter a valid number")
                return

            folium_map = self.mark_current_position_start(folium_map, lat_position_float, lon_position_float)
            geopandas_dataframe = calculator.calculate_distance(current_position)
            sorted_geopandas_dataframe = calculator.get_nearest_bikestations(default_bike_stations, geopandas_dataframe)

            for idx, row in sorted_geopandas_dataframe.iterrows():
                lat_position = row['latitude']
                lon_position = row['longitude']
                name = row['name']
                address_street = row['addressStreet']
                if option == "Bikes Available":
                    bikes_available = row['bikesAvailable']
                    folium_map = self.mark_bike_stations_available_bikes(folium_map, lat_position, lon_position, name,
                                                                         address_street, bikes_available)
                else:
                    docks_available = row['docksAvailable']
                    folium_map = self.mark_bike_stations_available_docks(folium_map, lat_position, lon_position, name,
                                                                         address_street, docks_available)

        st_folium(folium_map, width=700, height=500)

    """
        Generate and display the route map based on the user input.
    
        Parameters:
        lat_position (str): The latitude of the current position.
        lon_position (str): The longitude of the current position.
        option (str): The selected task (Route).
    """

    def route_map(self, lat_position, lon_position, option):
        try:
            src_position = Point(float(st.session_state.lon_position_src), float(st.session_state.lat_position_src))
            dest_position = Point(float(st.session_state.lon_position_dest), float(st.session_state.lat_position_dest))
            folium_map = folium.Map(location=(lat_position, lon_position), crs="EPSG3857", zoom_start=20)
        except ValueError:
            st.error("Please enter valid numbers for latitude and longitude.")
            return

        if st.session_state.map_updated:

            folium_map = self.mark_current_position_start(folium_map, src_position.y, src_position.x)
            folium_map = self.mark_current_position_end(folium_map, dest_position.y, dest_position.x)

            calculator = Calculator(option)
            calculator.option = "Bikes Available"
            start_geopandas_dataframe = calculator.calculate_distance(src_position)
            start_station_dataframe = calculator.get_nearest_bikestations(1, start_geopandas_dataframe)
            start_station_point = Point(float(start_station_dataframe['longitude'].iloc[0]),
                                        float(start_station_dataframe['latitude'].iloc[0]))

            for idx, row in start_geopandas_dataframe.iterrows():
                name = row['name']
                address_street = row['addressStreet']
                bikes_available = row['bikesAvailable']

            folium_map = self.mark_bike_stations_available_bikes(folium_map, start_station_point.y,
                                                                 start_station_point.x, name, address_street,
                                                                 bikes_available)

            calculator.option = "Docks Available"
            end_geopandas_dataframe = calculator.calculate_distance(dest_position)
            end_station_dataframe = calculator.get_nearest_bikestations(1, end_geopandas_dataframe)
            end_station_point = Point(float(end_station_dataframe['longitude'].iloc[0]),
                                      float(end_station_dataframe['latitude'].iloc[0]))

            for idx, row in end_geopandas_dataframe.iterrows():
                name = row['name']
                address_street = row['addressStreet']
                docks_available = row['docksAvailable']

            folium_map = self.mark_bike_stations_available_docks(folium_map, end_station_point.y, end_station_point.x,
                                                                 name, address_street, docks_available)

            start_coordinates = calculator.get_coordinates_from_api("foot-walking", src_position, start_station_point)
            end_coordinates = calculator.get_coordinates_from_api("cycling-regular", start_station_point,
                                                                  end_station_point)
            to_destination_coordinates = calculator.get_coordinates_from_api("foot-walking", end_station_point,
                                                                             dest_position)

            if start_coordinates and end_coordinates and to_destination_coordinates:
                folium_map = self.draw_route_line_by_foot(folium_map, start_coordinates)
                folium_map = self.draw_route_line_by_bike(folium_map, end_coordinates)
                folium_map = self.draw_route_line_by_foot(folium_map, to_destination_coordinates)

        st_folium(folium_map, width=700, height=500)

    """
       Get the current position as a Point object.
    
       Parameters:
       lat_position (float): The latitude of the current position.
       lon_position (float): The longitude of the current position.
    
       Returns:
       Point: The current position as a Point object.
    """

    @staticmethod
    def current_position(lat_position, lon_position):
        current_position = Point(lon_position, lat_position)
        return current_position

    """
        Mark the start position on the map.
    
        Parameters:
        folium_map (Map): The folium map object.
        lat_position_float (float): The latitude of the start position.
        lon_position_float (float): The longitude of the start position.
    
        Returns:
        Map: The folium map with the start position marked.
    """

    @staticmethod
    def mark_current_position_start(folium_map, lat_position_float, lon_position_float):
        folium.Marker(
            location=[lat_position_float, lon_position_float],
            tooltip="Click me!",
            popup="Your Start Position",
            icon=folium.Icon(color="green", icon='user', prefix='fa')
        ).add_to(folium_map)
        return folium_map

    """
        Mark the end position on the map.
    
        Parameters:
        folium_map (Map): The folium map object.
        lat_position_float (float): The latitude of the end position.
        lon_position_float (float): The longitude of the end position.
    
        Returns:
        Map: The folium map with the end position marked.
    """

    @staticmethod
    def mark_current_position_end(folium_map, lat_position_float, lon_position_float):
        folium.Marker(
            location=[lat_position_float, lon_position_float],
            tooltip="Click me!",
            popup="Your Destination",
            icon=folium.Icon(color="red", icon='user', prefix='fa')
        ).add_to(folium_map)
        return folium_map

    """
        Mark bike stations with available bikes on the map.
    
        Parameters:
        folium_map (Map): The folium map object.
        lat_position_float (float): The latitude of the bike station.
        lon_position_float (float): The longitude of the bike station.
        name (str): The name of the bike station.
        address_street (str): The address of the bike station.
        bikes_available (int): The number of available bikes at the station.
    
        Returns:
        Map: The folium map with available bike stations marked.
    """

    @staticmethod
    def mark_bike_stations_available_bikes(folium_map, lat_position_float, lon_position_float, name, address_street,
                                           bikes_available):
        popup_content = f"<strong>{name}</strong><br>{address_street}<br>Bikes: {bikes_available}"
        popup = folium.Popup(popup_content, max_width=250)
        folium.Marker(
            location=[lat_position_float, lon_position_float],
            tooltip="Click me!",
            popup=popup,
            icon=folium.Icon(color="blue", icon='bicycle', prefix='fa')
        ).add_to(folium_map)
        return folium_map

    """
        Mark bike stations with available docks on the map.
    
        Parameters:
        folium_map (Map): The folium map object.
        lat_position_float (float): The latitude of the bike station.
        lon_position_float (float): The longitude of the bike station.
        name (str): The name of the bike station.
        address_street (str): The address of the bike station.
        docks_available (int): The number of available docks at the station.
    
        Returns:
        Map: The folium map with available docks stations marked.
    """

    @staticmethod
    def mark_bike_stations_available_docks(folium_map, lat_position_float, lon_position_float, name, address_street,
                                           docks_available):
        popup_content = f"<strong>{name}</strong><br>{address_street}<br>Docks: {docks_available}"
        popup = folium.Popup(popup_content, max_width=250)
        folium.Marker(
            location=[lat_position_float, lon_position_float],
            tooltip="Click me!",
            popup=popup,
            icon=folium.Icon(color="orange", icon='bicycle', prefix='fa')
        ).add_to(folium_map)
        return folium_map

    """
        Draw a walking route line on the map.
    
        Parameters:
        folium_map (Map): The folium map object.
        coordinate_frame (list): The list of coordinates for the walking route.
    
        Returns:
        Map: The folium map with the walking route drawn.
    """

    @staticmethod
    def draw_route_line_by_foot(folium_map, coordinate_frame):
        folium.PolyLine(locations=coordinate_frame, color='black', weight=4).add_to(folium_map)
        return folium_map

    """
        Draw a biking route line on the map.
    
        Parameters:
        folium_map (Map): The folium map object.
        coordinate_frame (list): The list of coordinates for the biking route.
    
        Returns:
        Map: The folium map with the biking route drawn.
    """

    @staticmethod
    def draw_route_line_by_bike(folium_map, coordinate_frame):
        folium.PolyLine(locations=coordinate_frame, color='red', weight=4).add_to(folium_map)
        return folium_map
