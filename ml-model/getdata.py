import requests
import pandas as pd
import os
import time
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

def fetch_all_activities(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    activities = []
    page = 1
    
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities?page={page}&per_page=100"
        r = requests.get(url, headers=headers).json()
        if not r or (isinstance(r, dict) and 'message' in r): 
            break
        activities.extend(r)
        print(f"Fetched summary page {page}...")
        page += 1
        
    return pd.DataFrame(activities)

def fetch_streams(rides_df, access_token, flle_path):
    """
    Loops through all biking activities and fetches second-by-second 
    heart rate and time data for ML training.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    all_stream_data = []

    print(f"Starting stream fetch for {len(rides_df)} rides...")

    for index, row in rides_df.iterrows():
        activity_id = row['id']
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {'keys': 'time,heartrate,watts', 'key_by_type': True}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            temp_df = pd.DataFrame({
                'activity_id': activity_id,
                'time_offset': data['time']['data'] if 'time' in data else None,
                'heartrate': data['heartrate']['data'] if 'heartrate' in data else None,
                'watts': data['watts']['data'] if 'watts' in data else None
            })
            
            temp_df = temp_df.dropna(subset=['heartrate'])
            all_stream_data.append(temp_df)
            
            print(f"Fetched {len(temp_df)} seconds of data for Ride ID: {activity_id}")
            
            # rate limit 100 requests / 15 mins
            time.sleep(0.6) 
        else:
            print(f"Failed to fetch streams for {activity_id}: {response.status_code}")

    if all_stream_data:
        final_df = pd.concat(all_stream_data, ignore_index=True)
        final_df.to_csv(flle_path, index=False)
        return final_df
    
    return pd.DataFrame()

if __name__ == "__main__":
    token = get_new_access_token()
    
    all_activities_df = fetch_all_activities(token)
    
    if all_activities_df.empty:
        print("No activities found!")
    else:
        all_activities_df.to_csv('ml-model/strava_data.csv', index=False)
        print("Exported 'ml-model/strava_data.csv'")

        rides_df = all_activities_df[all_activities_df['type'] == 'Ride']
        rides_df.to_csv('ml-model/all_strava_bike_data.csv', index=False)
        print(f"Exported {len(rides_df)} ride summaries to 'ml-model/all_strava_bike_data.csv'")



        runs_df = all_activities_df[all_activities_df['type'] == 'Run']
        running_time_series = fetch_streams(runs_df, token, "ml-model/running_time_series.csv")
        if not running_time_series.empty:
            print(f"Success! Exported {len(running_time_series)} data points to 'ml-model/running_time_series.csv'")
        else:
            print("No time-series data found for the identified runs.")


        biking_time_series = fetch_streams(rides_df, token, "ml-model/biking_time_series.csv")
        
        if not biking_time_series.empty:
            print(f"Success! Exported {len(biking_time_series)} data points to 'ml-model/biking_time_series.csv'")
        else:
            print("No time-series data found for the identified rides.")