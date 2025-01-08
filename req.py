import requests

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
print(response.text)
