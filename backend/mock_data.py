MOCK_INTERESTS = [
    'Total Fan Count',  # ADD THESE THREE
    'Avid Fan Count',
    'Average Income',
    'Ba&sh', 'Yoga', 'Coffee', 'Tesla', 'Peloton', 'Whole Foods', 'Nike', 'Lululemon'
]

def generate_mock_heatmap_data(team, size_by, color_by):
    cities_data = []
    for city in CITIES:
        total_fans = random.randint(1000, 20000)
        avid_fans = random.randint(200, 5000)
        avg_income = random.randint(40000, 140000)
        
        # Determine size value based on what user selected
        if size_by == 'Total Fan Count':
            size_val = total_fans
        elif size_by == 'Avid Fan Count':
            size_val = avid_fans
        elif size_by == 'Average Income':
            size_val = avg_income
        else:
            size_val = random.randint(100, 5000)  # Interest value
        
        # Determine color value based on what user selected
        if color_by == 'Total Fan Count':
            color_val = total_fans
        elif color_by == 'Avid Fan Count':
            color_val = avid_fans
        elif color_by == 'Average Income':
            color_val = avg_income
        else:
            color_val = random.randint(50, 3000)  # Interest value
        
        cities_data.append({
            'cityName': city['name'],
            'stateName': city['state'],
            'cityLat': city['lat'],
            'cityLon': city['lon'],
            'sizeValue': size_val,
            'colorValue': color_val,
            'totalFanCount': total_fans,
            'avidFanCount': avid_fans,
            'avgIncome': avg_income
        })
    
    return cities_data

def get_mock_team_summary(team, cities_data):
    # Sum across ALL cities for team-wide totals
    return {
        'teamName': team,
        'totalFans': sum(c['totalFanCount'] for c in cities_data),
        'avidFans': sum(c['avidFanCount'] for c in cities_data),
        'avgIncome': sum(c['avgIncome'] for c in cities_data) // len(cities_data)
    }