import secrets
import requests
import json
import csv
import os
import datetime
import sys

new_totals = []

def get_token():
    url = "https://auth.sensourceinc.com/oauth/token"

    # Get the API key from secrets file
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"grant_type": "client_credentials", "client_id": str(secrets.client_id), "client_secret": str(secrets.client_secret)}
    response = requests.post(url, headers=header, data=payload)
    json_response = json.loads(response.text)
    # Create var to hold the response data
    active_patrons_token = json_response["access_token"]
    return active_patrons_token

# GETs data from the Vea API
def get_data():
    url = "https://vea.sensourceinc.com:443/api/data/traffic?relativeDate=thishour&dateGroupings=day&entityType=zone&metrics=ins%2Couts&excludeClosedHours=true"
    token = get_token()

    header = {"Authorization": "Bearer " + token, "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.get(url, headers=header)
    raw_data = json.loads(response.text)
    parse_data(raw_data)

# Parses retrieved data and writes the CSV
def parse_data(raw_data):

    # Setting variables, mostly lists for holding data
    gate_names = []
    total_building_entries = []
    total_building_exits = []
    childrens_room_entries = []
    childrens_room_exits = []
    security_gate_entries = []
    security_gate_exits = []
    loop_data = raw_data['results']

    # For loop, parses through data, storing related data in lists to be calculated
    for data in loop_data:
        gate_names.append(data['name'])

        # Main entrance traffic
        if data['name'] == 'Main Entrance Child' or data['name'] == 'Main Entrance Adult':
            total_building_entries.append(data['sumins'])
            total_building_exits.append(data['sumouts'])
        
        # Lower entrance traffic
        if data['name'] == 'Lower Entrance Child' or data['name'] == 'Lower Entrance Adult':
            total_building_entries.append(data['sumins'])
            total_building_exits.append(data['sumouts'])

        # Children's room traffic
        if data['name'] == "Children's Entrance Child" or data['name'] == "Children's Entrance Adult":
            childrens_room_entries.append(data['sumins'])
            childrens_room_exits.append(data['sumouts'])
        
        # Lobby traffic
        if data['name'] == "Security Gate Child" or data['name'] == "Security Gate Adult":
            security_gate_entries.append(data['sumins'])
            security_gate_exits.append(data['sumouts'])
    
    # These calculate the difference of entries & exits in the last hour at each gate
    building_entry_total = sum(total_building_entries)  
    building_exit_total = sum(total_building_exits)
    current_building_pop = building_entry_total - building_exit_total

    childrens_entry_total = sum(childrens_room_entries)
    childrens_exit_total = sum(childrens_room_exits)
    childrens_room_total = childrens_entry_total - childrens_exit_total

    security_entry_total = sum(security_gate_entries)
    security_exit_total = sum(security_gate_exits)
    security_gate_total = security_entry_total - security_exit_total

    # Setting more variables
    headers = ["Datetime", "Total Occupancy", "Children's Room Occupancy", "Lobby Occupancy"]
    now = datetime.datetime.now()

    # Open file as read to retrieve previous values
    with open("sensource.csv", "r", newline='') as file:
        row_count = sum(1 for row in file)
        time = str(datetime.datetime.now().time())
        weekno = datetime.datetime.today().weekday()
        reader = csv.reader(file, delimiter=",")
        file.seek(0)
        has_header = next(reader, None)

        # Don't read the header
        if has_header:
                next(reader)

        # If it's a weekday, at 9 AM, variables = 0
        if weekno <= 4 and time[0:2] == "09":
            prev_build_pop = 0
            prev_chld_pop = 0
            prev_lob_pop = 0

        # If it's the weekend, at 10 AM, variables = 0
        if weekno >= 5 and time[0:2] == "10":
            prev_build_pop = 0
            prev_chld_pop = 0
            prev_lob_pop = 0

        # Otherwise, variables = values of the last row
        else:
            for row in reader:
                prev_build_pop = int(row[1])
                prev_chld_pop = int(row[2])
                prev_lob_pop = int(row[3])

    # Opens file as append
    with open("sensource.csv", "a") as sensource:
        
        # If there are no rows in the CSV, write headers
        if row_count == 0:
            csv_writer = csv.DictWriter(sensource, fieldnames=headers, extrasaction='ignore', delimiter=',')
            csv_writer.writeheader()

        # If there is more than 1 row, calculate cell value based on previous value
        if row_count > 1:
            new_build_pop = current_building_pop + prev_build_pop
            new_chld_pop = childrens_room_total + prev_chld_pop
            new_lob_pop = security_gate_total + prev_lob_pop

            sensource.write(str(now) + ", ")
            sensource.write(str(new_build_pop) + ", ")
            sensource.write(str(new_chld_pop) + ", ")
            sensource.write(str(new_lob_pop) + "\n")

        # If there is a header, but no rows yet, write unaltered data
        else:
            sensource.write(str(now) + ", ")
            sensource.write(str(current_building_pop) + ", ")
            sensource.write(str(childrens_room_total) + ", ")
            sensource.write(str(security_gate_total) + "\n")


# Checks whether current time is within Library hours of operation, accounting for weekends
# If not, cancels script
def check_open():
    Now = datetime.datetime.now()
    business_hours = [(9,20),(9,20),(9,20),(9,20),(9,18),(10,18),(10,18),(-1,-1)]
    
    if Now.hour >= business_hours[Now.weekday()][0] and Now.hour <= business_hours[Now.weekday()][1]:
        get_data()
    else:
        sys.exit()

# Starts script        
check_open()