import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

def get_new_access_token():
    url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=payload).json()
    return response['access_token']

def fetch_all_activities():
    access_token = get_new_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    activities = []
    page = 1
    
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities?page={page}&per_page=100"
        r = requests.get(url, headers=headers).json()
        if not r or (isinstance(r, dict) and 'message' in r): 
            break
        activities.extend(r)
        page += 1
        print(f"Fetched page {page-1}...")
        
    return pd.DataFrame(activities)

if __name__ == "__main__":
    all_activities_df = fetch_all_activities()
    
    if all_activities_df.empty:
        print("No activities found!")
    else:
        all_activities_df.to_csv('ml-model/strava_data.csv', index=False)
        print(f"Exported all activities to ml-model/strava_data.csv")

        rides_df = all_activities_df[all_activities_df['type'] == 'Ride']
        rides_df.to_csv('ml-model/all_strava_bike_data.csv', index=False)
        
        print(f"Exported {len(rides_df)} activities to ml-model/all_strava_bike_data.csv")
        print("Available columns:", all_activities_df.columns.tolist())