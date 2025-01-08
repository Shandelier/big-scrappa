import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os


# Function to gather data
def gather_data():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,pl;q=0.8,en-GB;q=0.7",
        "Authorization": "Bearer eyJhbGciOiJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNobWFjLXNoYTI1NiIsInR5cCI6IkpXVCJ9.eyJNYXN0ZXJDb21wYW55Ijoid2VsbGZpdG5lc3MiLCJBdXRoZW50aWNhdGlvblR5cGUiOiJQYXNzd29yZCIsIlVzZXJJZCI6Ijg0NDQyNCIsImV4cCI6MTczNjM4MDQ2OCwiaXNzIjoicGVyZmVjdGd5bS5jb20iLCJhdWQiOiJwZXJmZWN0Z3ltLmNvbSJ9.jQs4AQrJ_y1PoCXb7EfOQjwDyDGT2H0s__XHyqZV3Ns",
        "CP-LANG": "en",
        "CP-MODE": "desktop",
        "Connection": "keep-alive",
        # 'Content-Length': '0',
        "Cookie": "ClientPortal.Embed; websiteAnalyticsConsent=true; customTrackingKey=true; BROWSER_UUID=4020d405-99e1-4055-b61f-f6d4a045b439; CpAuthToken=eyJhbGciOiJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNobWFjLXNoYTI1NiIsInR5cCI6IkpXVCJ9.eyJNYXN0ZXJDb21wYW55Ijoid2VsbGZpdG5lc3MiLCJBdXRoZW50aWNhdGlvblR5cGUiOiJQYXNzd29yZCIsIlVzZXJJZCI6Ijg0NDQyNCIsImV4cCI6MTczNjM4MDQ2OCwiaXNzIjoicGVyZmVjdGd5bS5jb20iLCJhdWQiOiJwZXJmZWN0Z3ltLmNvbSJ9.jQs4AQrJ_y1PoCXb7EfOQjwDyDGT2H0s__XHyqZV3Ns; x-bni-fpc=e26c9e69b72afe60458df094c38d0379; x-bni-rncf=1736353982852",
        "Origin": "https://wellfitness.perfectgym.pl",
        "Referer": "https://wellfitness.perfectgym.pl/ClientPortal2/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "X-Hash": "#/Clubs/MembersInClubs",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    response = requests.post(
        "https://wellfitness.perfectgym.pl/ClientPortal2/Clubs/Clubs/GetMembersInClubs",
        headers=headers,
    )
    if response.status_code == 200:
        try:
            print(
                "Response JSON:", response.json()
            )  # Print the JSON response for inspection
            return response.json()
        except ValueError:
            print("Response is not in JSON format:", response.text)
            return None
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
        return None


# Function to process data
def process_data(data):
    df = pd.DataFrame(data["UsersInClubList"])
    # Include ClubName, ClubAddress, and UsersCountCurrentlyInClub in the DataFrame
    df = df[["ClubName", "ClubAddress", "UsersCountCurrentlyInClub"]]
    # Add a timestamp column
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return df


# Function to save data to CSV
def save_to_csv(data, filename="data.csv"):
    # Check if the file exists and is not empty
    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        data.to_csv(filename, index=False)
    else:
        # Read existing data
        existing_data = pd.read_csv(filename)
        # Concatenate new data
        combined_data = pd.concat([existing_data, data], ignore_index=True)
        # Save combined data
        combined_data.to_csv(filename, index=False)


# Function to backup data
def backup_data(filename="data.csv"):
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d')}.csv"
    os.rename(filename, backup_filename)


# Function to delete old backups
def delete_old_backups(days=30):
    cutoff_date = datetime.now() - timedelta(days=days)
    for file in os.listdir("."):  # Assuming backups are in the current directory
        if file.startswith("backup_") and file.endswith(".csv"):
            file_date = datetime.strptime(file[7:15], "%Y%m%d")
            if file_date < cutoff_date:
                os.remove(file)


# Main function to run the scraper
if __name__ == "__main__":
    while True:
        data = gather_data()
        averages = process_data(data)
        save_to_csv(averages)
        time.sleep(600)  # Wait for 10 minutes before the next request
