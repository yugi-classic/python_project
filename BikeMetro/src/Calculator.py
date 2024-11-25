import geopandas
import os
import json
import requests as req

crs_in = 'EPSG:4326'
crs_out = 'EPSG:3857'
url = "https://bikeshare.metro.net/stations/json/"
api_key = "5b3ce3597851110001cf6248f0417563a92a40fa9174387301a3d6a6"
datajson = None
geopandas_dataframe = None
class Calculator:

    def __init__(self, option):
        self.option = option

    """
        Load the GeoDataFrame from the stations JSON file.

        Returns:
        GeoDataFrame: The GeoDataFrame loaded from the JSON file from the stations directory.
    """
    @staticmethod
    def load_dataframe():
        try:
            json_file_data = open('stations/stations.json')
            dataframe = geopandas.read_file(json_file_data)
            dataframe.set_crs(crs_in)
            return dataframe
        except Exception as e:
            print("Error occurred while reading the GeoJSON file:")
            print(e)
            return None

    """
        Calculate the distance from the current position to bike stations.

        Parameters:
        current_position (Point): The current position as a Shapely Point.

        Returns:
        GeoDataFrame: The GeoDataFrame with distances to bike stations.
    """

    def calculate_distance(self, current_position):

        dataframe = self.load_dataframe()
        if self.option == "Bikes Available":
            dataframe = self.check_dataframe_available_bikes(dataframe)
        if self.option == "Docks Available":
            dataframe = self.check_dataframe_available_docks(dataframe)
        geopandas_point = geopandas.GeoSeries([current_position], crs=crs_in)
        geopandas_point = geopandas_point.to_crs(crs_out)
        geopandas_dataframe = dataframe.to_crs(crs_out)
        geopandas_dataframe['distance'] = geopandas_dataframe.geometry.distance(geopandas_point.iloc[0])
        return geopandas_dataframe

    """
        Get the nearest bike stations based on distance.

        Parameters:
        bike_station_int (int): The number of nearest bike stations to return.
        geopandas_dataframe (GeoDataFrame): The GeoDataFrame containing bike stations.

        Returns:
        GeoDataFrame: The GeoDataFrame with the nearest bike stations.
    """
    def get_nearest_bikestations(self, bike_station_int, geopandas_dataframe):
        return geopandas_dataframe.sort_values(by='distance').head(bike_station_int)

    """
        Filter the DataFrame to include only bike stations with available bikes.

        Parameters:
        dataframe (GeoDataFrame): The GeoDataFrame containing bike stations.

        Returns:
        GeoDataFrame: The filtered GeoDataFrame with available bikes.
    """

    @staticmethod
    def check_dataframe_available_bikes(dataframe):
        if 'bikesAvailable' not in dataframe.columns:
            return dataframe

        filtered_dataframe = dataframe[dataframe['bikesAvailable'] > 0]
        return filtered_dataframe

    """
        Filter the DataFrame to include only bike stations with available docks.

        Parameters:
        dataframe (GeoDataFrame): The GeoDataFrame containing bike stations.

        Returns:
        GeoDataFrame: The filtered GeoDataFrame with available docks.
    """
    @staticmethod
    def check_dataframe_available_docks(dataframe):
        if 'docksAvailable' not in dataframe.columns:
            return dataframe

        filtered_dataframe = dataframe[dataframe['docksAvailable'] > 0]
        return filtered_dataframe

    """
       Get the coordinates for a route from an API and save to a JSON file.

       Parameters:
       travel_option (str): The travel mode (e.g., "foot-walking", "cycling-regular").
       point_src (Point): The source position as a Shapely Point.
       point_dest (Point): The destination position as a Shapely Point.

       Returns:
       list: The list of coordinates for the route.
    """
    def get_coordinates_from_api(self, travel_option, point_src, point_dest):
        route_folder = "routes"
        route_identifier = f'{point_src.x}_{point_src.y}_{point_dest.x}_{point_dest.y}'
        data_file = os.path.join(route_folder, f'{travel_option}_{route_identifier}.json')
        if os.path.exists(data_file):
            with open(data_file, 'r') as file:
                geojson_data = json.load(file)
        else:
            try:
                call = req.get(
                    f'https://api.openrouteservice.org/v2/directions/{travel_option}?api_key={api_key}&start={point_src.x},{point_src.y}&end={point_dest.x},{point_dest.y}')
                call.raise_for_status()
                geojson_data = json.loads(call.text)
                with open(data_file, "w") as file:
                    json.dump(geojson_data, file)
            except req.exceptions.HTTPError as http_err:
                if call.status_code == 429:
                    print("API-Limit reached")
                else:
                    print(f"HTTP-Error: {http_err}")
                return None
            except req.exceptions.RequestException as req_err:
                print(f"Request-Error: {req_err}")
                return None

        coordinates = geojson_data['features'][0]['geometry']['coordinates']
        reversed_coordinates = [(coord[1], coord[0]) for coord in coordinates]
        return reversed_coordinates