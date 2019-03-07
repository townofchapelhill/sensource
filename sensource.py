# Libraries
import secrets
import requests
import json
import os
import datetime
import sys

# Object created to store data retrieved from API in an organized fashion
# Helps to ensure that the correct numbers are written under the correct headers
class Data(object):
    def __init__(self, mainAdultIns=None, mainAdultOuts=None, secAdultIns=None, secAdultOuts=None, chRmAdultIns=None, chRmAdultOuts=None, lwrAdultIns=None, lwrAdultOuts=None, mainChildIns=None, mainChildOuts=None, secChildIns=None, secChildOuts=None, chRmChildIns=None, chRmChildOuts=None, lwrChildIns=None, lwrChildOuts=None):
        self.mainAdultIns = ''
        self.mainAdultOuts = ''
        self.secAdultIns = ''
        self.secAdultOuts = ''
        self.chRmAdultIns = ''
        self.chRmAdultOuts = ''
        self.lwrAdultIns = ''
        self.lwrAdultOuts = ''
        self.mainChildIns = ''
        self.mainChildOuts = ''
        self.secChildIns = ''
        self.secChildOuts = ''
        self.chRmChildIns = ''
        self.chRmChildOuts = ''
        self.lwrChildIns = ''
        self.lwrChildOuts = ''

# Call this function to get the access token
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

# Function retrieves data from the Vea sensource API
def get_data():
    url = "https://vea.sensourceinc.com:443/api/data/traffic?relativeDate=today&dateGroupings=day&entityType=zone&metrics=ins%2Couts&excludeClosedHours=true"
    token = get_token()
    # Authentication
    header = {"Authorization": "Bearer " + token, "Content-Type": "application/x-www-form-urlencoded"}
    # Store response & call next function
    response = requests.get(url, headers=header)
    raw_data = json.loads(response.text)
    parse_data(raw_data)

# Function performs the data transformation
def parse_data(raw_data):
    # Lists for organizing & parsing data
    total_building_entries = []
    total_building_exits = []
    childrens_room_entries = []
    childrens_room_exits = []
    security_gate_entries = []
    security_gate_exits = []
    loop_data = raw_data['results']
    # Initialize new "Data" object
    new_data = Data()

    # Loop through data, sort by sensor name and whether it's an in or out count
    for data in loop_data:
        if data['name'] == 'Main Entrance Child':
            total_building_entries.append(data['sumins'])
            total_building_exits.append(data['sumouts'])
            new_data.mainChildIns = data['sumins']
            new_data.mainChildOuts = data['sumouts']

        if data['name'] == 'Main Entrance Adult':
            total_building_entries.append(data['sumins'])
            total_building_exits.append(data['sumouts'])
            new_data.mainAdultIns = data['sumins']
            new_data.mainAdultOuts = data['sumouts']

        if data['name'] == 'Lower Entrance Child':
            total_building_entries.append(data['sumins'])
            total_building_exits.append(data['sumouts'])
            new_data.lwrChildIns = data['sumins']
            new_data.lwrChildOuts = data['sumouts']

        if data['name'] == 'Lower Entrance Adult':
            total_building_entries.append(data['sumins'])
            total_building_exits.append(data['sumouts'])
            new_data.lwrAdultIns = data['sumins']
            new_data.lwrAdultOuts = data['sumouts']

        if data['name'] == "Children's Entrance Child":
            childrens_room_entries.append(data['sumins'])
            childrens_room_exits.append(data['sumouts'])
            new_data.chRmChildIns = data['sumins']
            new_data.chRmChildOuts = data['sumouts']

        if data['name'] == "Children's Entrance Adult":
            childrens_room_entries.append(data['sumins'])
            childrens_room_exits.append(data['sumouts'])
            new_data.chRmAdultIns = data['sumins']
            new_data.chRmAdultOuts = data['sumouts']

        if data['name'] == "Security Gate Child":
            security_gate_entries.append(data['sumins'])
            security_gate_exits.append(data['sumouts'])
            new_data.secChildIns = data['sumins']
            new_data.secChildOuts = data['sumouts']

        if data['name'] == "Security Gate Adult":
            security_gate_entries.append(data['sumins'])
            security_gate_exits.append(data['sumouts'])
            new_data.secAdultIns = data['sumins']
            new_data.secAdultOuts = data['sumouts']

    # Store object as dict to allow for subscripting later
    writeable_data = new_data.__dict__

    # Sum the contents of each list, then subject outs from ins to determine current occupancy
    building_entry_total = sum(total_building_entries)  
    building_exit_total = sum(total_building_exits)
    current_building_pop = building_entry_total - building_exit_total

    childrens_entry_total = sum(childrens_room_entries)
    childrens_exit_total = sum(childrens_room_exits)
    childrens_room_total = childrens_entry_total - childrens_exit_total

    security_entry_total = sum(security_gate_entries)
    security_exit_total = sum(security_gate_exits)
    security_gate_total = security_entry_total - security_exit_total

    # Sometimes the final numbers are negative because of sensor limitations
    # Population cannot be below 0, this code block accounts for that
    if current_building_pop <= 0:
        current_building_pop = 0
    if childrens_room_total <= 0:
        childrens_room_total = 0
    if security_gate_total <= 0:
        security_gate_total = 0

    # Calls next function, passes necessary variables
    write_data(current_building_pop, childrens_room_total, security_gate_total, writeable_data)

# Function that writes the final CSV
def write_data(current_building_pop, childrens_room_total, security_gate_total, writeable_data):
    new_data = writeable_data
    with open("sensource.csv", "a") as sensource:
        # Holds datetime, split because of strange date interpretation behavior on the Open Data Server
        day_time = str(datetime.datetime.now()).split(".")
        # Writes the rows
        sensource.write(str(day_time[0]) + ", ")
        sensource.write(str(current_building_pop) + ", ")
        sensource.write(str(childrens_room_total) + ", ")
        sensource.write(str(security_gate_total) + ", ")
        sensource.write(str(new_data['chRmChildIns']) + ", ")
        sensource.write(str(new_data['chRmChildOuts']) + ", ")
        sensource.write(str(new_data['lwrChildIns']) + ", ")
        sensource.write(str(new_data['lwrChildOuts']) + ", ")
        sensource.write(str(new_data['secAdultIns']) + ", ")
        sensource.write(str(new_data['secAdultOuts']) + ", ")
        sensource.write(str(new_data['lwrAdultIns']) + ", ")
        sensource.write(str(new_data['lwrAdultOuts']) + ", ")
        sensource.write(str(new_data['chRmAdultIns']) + ", ")
        sensource.write(str(new_data['chRmAdultOuts']) + ", ")
        sensource.write(str(new_data['secChildIns']) + ", ")
        sensource.write(str(new_data['secChildOuts']) + ", ")
        sensource.write(str(new_data['mainAdultIns']) + ", ")
        sensource.write(str(new_data['mainAdultOuts']) + ", ")
        sensource.write(str(new_data['mainChildIns']) + ", ")
        sensource.write(str(new_data['mainChildOuts']) + "\n")
        # Close file, exit script
        sensource.close()
        sys.exit()

# Function to check if Library is currently open
def check_open():
    Now = datetime.datetime.now()
    business_hours = [(9,20),(9,20),(9,20),(9,20),(9,18),(10,18),(10,18),(-1,-1)]
    # If current hour is within operating hours, continue
    # else, exit script
    if Now.hour >= business_hours[Now.weekday()][0] and Now.hour <= business_hours[Now.weekday()][1]:
        get_data()
    else:
        sys.exit()

# Begins script
check_open()