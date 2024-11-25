from Gui import Gui
import json
import os
import requests as req

#streamlit run Main.py --> ausführen der Datei

url = "https://bikeshare.metro.net/stations/json/"
headers = {'User-Agent': 'Mozilla/5.0'}


# Main function of the program. Loads the live data and starts the GUI.
def main():
    load_live_data_and_write()
    gui = Gui()

# Function to load live data from the API and save it to a JSON file.
# This function performs the following steps:
# 1. Check if the 'stations' folder exists, and create it if it doesn't.
# 2. Retrieve the JSON data from the specified URL using the defined header.
# 3. Write the retrieved data to a file named 'stations.json' in the 'stations' folder.
# If there is an error while retrieving the data, an error message is printed.
def load_live_data_and_write():
    try:
        station_folder = "stations"
        if not os.path.exists(station_folder):
            os.makedirs(station_folder)

        response = req.get(url, headers=headers)
        response.raise_for_status()
        datajson = response.json()
        with open(os.path.join(station_folder, 'stations.json'), 'w') as json_file:
            json.dump(datajson, json_file, indent=4)

    except req.exceptions.RequestException as e:
        print(f"error while loading JSON: {e}")

if __name__ == "__main__":
    main()



