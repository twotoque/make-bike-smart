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

def fetch_all_rides():
    access_token = get_new_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    activities = []
    page = 1
    
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities?page={page}&per_page=100"
        r = requests.get(url, headers=headers).json()
        if not r or 'message' in r: # Handle empty pages or errors
            break
        activities.extend(r)
        page += 1
        print(f"Fetched page {page-1}...")
        
    df = pd.DataFrame(activities)
    if not df.empty:
        df = df[df['type'] == 'Ride']
    return df

if __name__ == "__main__":
    rides_df = fetch_all_rides()
    
    if rides_df.empty:
        print("No rides found!")
    else:
        rides_df.to_csv('all_strava_bike_data.csv', index=False)
        
        print(f"Success! Exported {len(rides_df)} rides to 'all_strava_bike_data.csv'")
        print("Available columns for your ML model:", rides_df.columns.tolist())