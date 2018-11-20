import secrets
import requests
import json

def get_token():
    url = "https://auth.sensourceinc.com/oauth/token"

    # Get the API key from secrets file
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"grant_type": "client_credentials", "client_id": str(secrets.client_id), "client_secret": str(secrets.client_secret)}
    response = requests.post(url, headers=header, data=payload)
    json_response = json.loads(response.text)
    # Create var to hold the response data
    active_patrons_token = json_response["access_token"]
    print(active_patrons_token)
    return active_patrons_token


def get_data():
    url = "https://vea.sensourceinc.com:443/api/data/traffic?relativeDate=yesterday&dateGroupings=day&entityType=zone&metrics=ins%2Couts&excludeClosedHours=true"
    token = get_token()

    header = {"Authorization": "Bearer " + token, "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.get(url, headers=header)
    print(response.text)

get_data()