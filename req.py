import requests
import os
from dotenv import load_dotenv


def login(username, password):
    login_url = "https://wellfitness.perfectgym.pl/ClientPortal2/Auth/Login"
    login_data = {"login": username, "password": password}

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://wellfitness.perfectgym.pl",
        "Referer": "https://wellfitness.perfectgym.pl/ClientPortal2/",
    }

    session = requests.Session()
    response = session.post(login_url, json=login_data, headers=headers)

    if response.ok:
        return session
    else:
        raise Exception("Login failed")


def get_members_in_clubs(session):
    url = (
        "https://wellfitness.perfectgym.pl/ClientPortal2/Clubs/Clubs/GetMembersInClubs"
    )
    response = session.post(url)
    return response.text


def main():
    # Load environment variables
    load_dotenv()

    username = os.getenv("WELLFITNESS_USERNAME")
    password = os.getenv("WELLFITNESS_PASSWORD")

    if not username or not password:
        raise Exception("Missing credentials in environment variables")

    try:
        session = login(username, password)
        data = get_members_in_clubs(session)
        print(data)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
