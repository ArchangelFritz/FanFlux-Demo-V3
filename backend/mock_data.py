import random

MOCK_TEAMS = [
    'Chicago Bulls',
    'Los Angeles Lakers',
    'Golden State Warriors',
    'Boston Celtics',
    'Miami Heat',
    'Dallas Mavericks'
]

# These are the column headers - includes both metrics AND interests
MOCK_INTERESTS = [
    'Total Fan Count',      # Can size/color by this
    'Avid Fan Count',       # Can size/color by this
    'Average Income',       # Can size/color by this
    'Ba&sh',               # Interest - can size/color by this
    'Yoga',                # Interest
    'Coffee',              # Interest
    'Tesla',               # Interest
    'Peloton',             # Interest
    'Whole Foods',         # Interest
    'Nike',                # Interest
    'Lululemon'            # Interest
]

CITIES = [
    {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060, 'state': 'NY'},
    {'name': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437, 'state': 'CA'},
    {'name': 'Chicago', 'lat': 41.8781, 'lon': -87.6298, 'state': 'IL'},
    {'name': 'Houston', 'lat': 29.7604, 'lon': -95.3698, 'state': 'TX'},
    {'name': 'Phoenix', 'lat': 33.4484, 'lon': -112.0740, 'state': 'AZ'},
    {'name': 'Philadelphia', 'lat': 39.9526, 'lon': -75.1652, 'state': 'PA'},
    {'name': 'San Antonio', 'lat': 29.4241, 'lon': -98.4936, 'state': 'TX'},
    {'name': 'San Diego', 'lat': 32.7157, 'lon': -117.1611, 'state': 'CA'},
    {'name': 'Dallas', 'lat': 32.7767, 'lon': -96.7970, 'state': 'TX'},
    {'name': 'San Jose', 'lat': 37.3382, 'lon': -121.8863, 'state': 'CA'},
    {'name': 'Austin', 'lat': 30.2672, 'lon': -97.7431, 'state': 'TX'},
    {'name': 'Seattle', 'lat': 47.6062, 'lon': -122.3321, 'state': 'WA'},
    {'name': 'Denver', 'lat': 39.7392, 'lon': -104.9903, 'state': 'CO'},
    {'name': 'Boston', 'lat': 42.3601, 'lon': -71.0589, 'state': 'MA'},
    {'name': 'Portland', 'lat': 45.5152, 'lon': -122.6784, 'state': 'OR'},
    {'name': 'Miami', 'lat': 25.7617, 'lon': -80.1918, 'state': 'FL'},
    {'name': 'Atlanta', 'lat': 33.7490, 'lon': -84.3880, 'state': 'GA'},
]

# Fixed team totals - these NEVER change regardless of interest selection
TEAM_TOTALS = {
    'Chicago Bulls': {'totalFans': 4500000, 'avidFans': 850000, 'avgIncome': 75000},
    'Los Angeles Lakers': {'totalFans': 6200000, 'avidFans': 1200000, 'avgIncome': 82000},
    'Golden State Warriors': {'totalFans': 5800000, 'avidFans': 1100000, 'avgIncome': 95000},
    'Boston Celtics': {'totalFans': 4200000, 'avidFans': 780000, 'avgIncome': 78000},
    'Miami Heat': {'totalFans': 3900000, 'avidFans': 720000, 'avgIncome': 71000},
    'Dallas Mavericks': {'totalFans': 3600000, 'avidFans': 650000, 'avgIncome': 68000},
}

# Static city-level data per team - mimics SQL table rows
# Each (team, city) combo has fixed values that don't change
CITY_DATA_CACHE = {}

def get_city_data_for_team(team, city):
    """Get consistent city data for a team - same values every time"""
    cache_key = f"{team}_{city['name']}"
    
    if cache_key not in CITY_DATA_CACHE:
        # Generate once and cache
        random.seed(hash(cache_key))
        CITY_DATA_CACHE[cache_key] = {
            'totalFanCount': random.randint(1000, 20000),
            'avidFanCount': random.randint(200, 5000),
            'avgIncome': random.randint(40000, 140000),
            # Each interest also has a value for this city
            'Ba&sh': random.randint(100, 3000),
            'Yoga': random.randint(100, 3000),
            'Coffee': random.randint(100, 3000),
            'Tesla': random.randint(100, 3000),
            'Peloton': random.randint(100, 3000),
            'Whole Foods': random.randint(100, 3000),
            'Nike': random.randint(100, 3000),
            'Lululemon': random.randint(100, 3000),
        }
        random.seed()  # Reset
    
    return CITY_DATA_CACHE[cache_key]

def generate_mock_heatmap_data(team, size_by, color_by):
    """
    Mimics the SQL query that returns city data for a team.
    Size and color values are extracted from the static city data.
    """
    cities_data = []
    
    for city in CITIES:
        # Get the static data for this team+city combo
        city_metrics = get_city_data_for_team(team, city)
        
        # Extract the specific values based on what user selected
        if size_by == 'Total Fan Count':
            size_val = city_metrics['totalFanCount']
        elif size_by == 'Avid Fan Count':
            size_val = city_metrics['avidFanCount']
        elif size_by == 'Average Income':
            size_val = city_metrics['avgIncome']
        else:
            # It's an interest name like "Ba&sh"
            size_val = city_metrics.get(size_by, 0)
        
        if color_by == 'Total Fan Count':
            color_val = city_metrics['totalFanCount']
        elif color_by == 'Avid Fan Count':
            color_val = city_metrics['avidFanCount']
        elif color_by == 'Average Income':
            color_val = city_metrics['avgIncome']
        else:
            # It's an interest name
            color_val = city_metrics.get(color_by, 0)
        
        cities_data.append({
            'cityName': city['name'],
            'stateName': city['state'],
            'cityLat': city['lat'],
            'cityLon': city['lon'],
            'sizeValue': size_val,
            'colorValue': color_val,
            'totalFanCount': city_metrics['totalFanCount'],
            'avidFanCount': city_metrics['avidFanCount'],
            'avgIncome': city_metrics['avgIncome']
        })
    
    return cities_data

def get_mock_team_summary(team, cities_data=None):
    """
    Returns fixed team-wide totals.
    These are the same regardless of which interests are selected.
    Mimics: SELECT SUM(TOTAL_FAN_COUNT), SUM(AVID_FAN_COUNT), AVG(AVG_INCOME) 
            FROM table WHERE TEAM = X AND INTEREST = TEAM_NAME
    """
    return {
        'teamName': team,
        **TEAM_TOTALS.get(team, {'totalFans': 4000000, 'avidFans': 750000, 'avgIncome': 70000})
    }