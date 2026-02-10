import random

MOCK_TEAMS = [
    'Chicago Bulls', 'Los Angeles Lakers', 'Golden State Warriors',
    'Boston Celtics', 'Miami Heat', 'Dallas Mavericks'
]

MOCK_INTERESTS = [
    'Ba&sh', 'Yoga', 'Coffee', 'Tesla', 'Peloton', 'Whole Foods', 'Nike', 'Lululemon'
]

CITIES = [
    {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060, 'state': 'NY'},
    {'name': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437, 'state': 'CA'},
    {'name': 'Chicago', 'lat': 41.8781, 'lon': -87.6298, 'state': 'IL'},
    {'name': 'Houston', 'lat': 29.7604, 'lon': -95.3698, 'state': 'TX'},
    {'name': 'Phoenix', 'lat': 33.4484, 'lon': -112.0740, 'state': 'AZ'},
    {'name': 'Philadelphia', 'lat': 39.9526, 'lon': -75.1652, 'state': 'PA'},
    {'name': 'Miami', 'lat': 25.7617, 'lon': -80.1918, 'state': 'FL'},
    {'name': 'Atlanta', 'lat': 33.7490, 'lon': -84.3880, 'state': 'GA'},
]

def generate_mock_heatmap_data(team, size_by, color_by):
    return [{
        'cityName': city['name'],
        'stateName': city['state'],
        'cityLat': city['lat'],
        'cityLon': city['lon'],
        'sizeValue': random.randint(100, 5000),
        'colorValue': random.randint(50, 3000),
        'totalFanCount': random.randint(1000, 20000),
        'avidFanCount': random.randint(200, 5000),
        'avgIncome': random.randint(40000, 140000)
    } for city in CITIES]

def get_mock_team_summary(team):
    return {
        'teamName': team,
        'totalFans': random.randint(1000000, 5000000),
        'avidFans': random.randint(200000, 1000000),
        'avgIncome': random.randint(60000, 110000)
    }