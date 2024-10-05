import requests

# API URL and parameters
url = "https://real-time-events-search.p.rapidapi.com/search-events"
querystring = {"query":"Hackathon","date":"any","is_virtual":"false","start":"0"}

# Headers with API key
headers = {
    "x-rapidapi-key": "31f9f38f67msh61dc71a007fa815p1d2c63jsnf6de091561b4",
    "x-rapidapi-host": "real-time-events-search.p.rapidapi.com"
}

# Sending the GET request
response = requests.get(url, headers=headers, params=querystring)

# If the request is successful
if response.status_code == 200:
    events = response.json().get('data', [])

    # Loop through each event and extract the required fields
    for event in events:
        event_name = event.get('name', 'N/A')
        link = event.get('link', 'N/A')
        venue = event.get('venue', {}).get('google_location', 'N/A')  # Fetch venue if available
        publisher = event.get('publisher', 'N/A')
        info_links = event.get('info_links', [{'link': 'N/A'}])[0].get('link', 'N/A')
        start_time = event.get('start_time', 'N/A')
        end_time = event.get('end_time', 'N/A')
        description = event.get('description', 'N/A')

        # Display the extracted details
        print(f"Event Name: {event_name}")
        print(f"Link: {link}")
        print(f"Venue: {venue}")
        print(f"Publisher: {publisher}")
        print(f"Info Links: {info_links}")
        print(f"Start Time: {start_time}")
        print(f"End Time: {end_time}")
        print(f"Description: {description}")
        print("\n" + "-"*50 + "\n")
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
