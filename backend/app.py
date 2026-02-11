from flask import Flask, jsonify, request
from flask_cors import CORS
import snowflake.connector
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

app = Flask(__name__)
CORS(app)

def get_private_key_from_env():
    """Load private key from environment variable."""
    private_key_data = os.getenv('SNOWFLAKE_PRIVATE_KEY')
    
    if not private_key_data:
        return None
    
    try:
        if private_key_data.startswith('-----BEGIN'):
            private_key_bytes = private_key_data.encode('utf-8')
        else:
            private_key_bytes = base64.b64decode(private_key_data)
        
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
            backend=default_backend()
        )
        
        pkb = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return pkb
    except Exception as e:
        print(f"Error loading private key: {e}")
        return None

def get_snowflake_config():
    """Build Snowflake configuration"""
    config = {
        'user': os.getenv('SNOWFLAKE_USER'),
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA')
    }
    
    private_key = get_private_key_from_env()
    if private_key:
        config['private_key'] = private_key
        print("Using key-pair authentication")
    else:
        password = os.getenv('SNOWFLAKE_PASSWORD')
        if password:
            config['password'] = password
            print("Using password authentication")
        else:
            raise ValueError("Neither SNOWFLAKE_PRIVATE_KEY nor SNOWFLAKE_PASSWORD is set")
    
    return config

def get_snowflake_connection():
    """Create and return a Snowflake connection"""
    config = get_snowflake_config()
    
    required_vars = ['user', 'account', 'warehouse', 'database', 'schema']
    missing = [var for var in required_vars if not config.get(var)]
    
    if missing:
        raise ValueError(f"Missing required Snowflake environment variables: {', '.join([f'SNOWFLAKE_{v.upper()}' for v in missing])}")
    
    return snowflake.connector.connect(**config)

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of unique teams (topics) with their total fan counts"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Sum fans across all cities for each topic
        # Filter to only actual sports teams (not interests like Yoga, Basketball, etc.)
        query = """
        SELECT 
            TOPIC,
            SUM(TOTAL_FAN_COUNT) as TOTAL_FANS,
            SUM(AVID_FAN_COUNT) as AVID_FANS,
            AVG(AVG_INCOME) as AVG_INCOME,
            COUNT(*) as NUM_CITIES
        FROM VERSION3_MASTER
        WHERE TOPIC IN (
            -- NHL Teams
            'Anaheim Ducks', 'Arizona Coyotes', 'Boston Bruins', 'Buffalo Sabres',
            'Calgary Flames', 'Carolina Hurricanes', 'Chicago Blackhawks', 'Colorado Avalanche',
            'Columbus Blue Jackets', 'Dallas Stars', 'Detroit Red Wings', 'Edmonton Oilers',
            'Florida Panthers', 'Los Angeles Kings', 'Minnesota Wild', 'Montreal Canadiens',
            'Nashville Predators', 'New York Islanders', 'New York Rangers',
            'Ottawa Senators', 'Philadelphia Flyers', 'Pittsburgh Penguins', 'San Jose Sharks',
            'St. Louis Blues', 'Tampa Bay Lightning', 'Toronto Maple Leafs',
            'Vancouver Canucks', 'Washington Capitals', 'Winnipeg Jets',
            
            -- NBA Teams
            'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Chicago Bulls', 'Bulls',
            'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets', 'Detroit Pistons',
            'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers', 'Los Angeles Clippers',
            'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat', 'Milwaukee Bucks',
            'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
            'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
            'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors', 'Utah Jazz',
            'Washington Wizards',
            
            -- MLB Teams
            'Arizona Diamondbacks', 'Atlanta Braves', 'Baltimore Orioles', 'Boston Redsox',
            'Chicago Cubs', 'Cincinnati Reds', 'Cleveland Indians', 'Colorado Rockies',
            'Detroit Tigers', 'Houston Astros', 'Kansas City Royals', 'Los Angeles Angels',
            'Los Angeles Dodgers', 'Miami Marlins', 'Milwaukee Brewers', 'Minnesota Twins',
            'New York Mets', 'New York Yankees', 'Oakland Athletics', 'Philadelphia Phillies',
            'Pittsburgh Pirates', 'San Diego Padres', 'San Francisco Giants', 'Seattle Mariners',
            'St. Louis Cardinals', 'Tampa Bay Rays', 'Texas Rangers', 'Toronto Blue Jays',
            'Washington Nationals',
            
            -- NFL Teams
            'Arizona Cardinals', 'Atlanta Falcons', 'Baltimore Ravens', 'Buffalo Bills',
            'Carolina Panthers', 'Chicago Bears', 'Cincinnati Bengals', 'Cleveland Browns',
            'Dallas Cowboys', 'Denver Broncos', 'Detroit Lions', 'Green Bay Packers',
            'Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars', 'Kansas City Chiefs',
            'Las Vegas Raiders', 'Los Angeles Chargers', 'Los Angeles Rams', 'Miami Dolphins',
            'Minnesota Vikings', 'New England Patriots', 'New Orleans Saints', 'New York Giants',
            'New York Jets', 'Philadelphia Eagles', 'Pittsburgh Steelers', 'San Francisco 49ers',
            'Seattle Seahawks', 'Tampa Bay Buccaneers', 'Tennessee Titans', 'Washington Football Team',
            
            -- MLS Teams
            'Atlanta United FC', 'LA Galaxy', 'Minnesota United FC', 'New York City FC',
            'New York Red Bulls', 'Portland Timbers', 'Seattle Sounders FC', 'Toronto FC',
            'Vancouver Whitecaps FC'
        )
        GROUP BY TOPIC
        ORDER BY TOPIC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        teams = []
        for row in rows:
            teams.append({
                'name': row[0],
                'totalFans': int(row[1]) if row[1] else 0,
                'avidFans': int(row[2]) if row[2] else 0,
                'avgIncome': int(row[3]) if row[3] else 0,
                'numCities': int(row[4]) if row[4] else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(teams)
    
    except Exception as e:
        print(f"Error in /api/teams: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interests', methods=['GET'])
def get_interests():
    """Get list of unique interests (topics)"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT TOPIC
        FROM VERSION3_MASTER
        WHERE TOPIC IS NOT NULL
        ORDER BY TOPIC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        interests = [row[0] for row in rows]
        
        cursor.close()
        conn.close()
        
        return jsonify(interests)
    
    except Exception as e:
        print(f"Error in /api/interests: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Get heatmap data filtered by team and interests with Top N filtering"""
    try:
        team = request.args.get('team')
        size_by = request.args.get('sizeBy')
        color_by = request.args.get('colorBy')
        top_n = request.args.get('topN', type=int)
        
        if not team:
            return jsonify({'error': 'team parameter is required'}), 400
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Build list of topics to query
        # When "Average Income" is selected, we just need the team row (it has avgIncome)
        topics = {team}
        if size_by != 'Average Income':
            topics.add(size_by)
        if color_by != 'Average Income':
            topics.add(color_by)
        
        placeholders = ', '.join(['%s'] * len(topics))
        query = f"""
        SELECT 
            CITY_NAME,
            STATE_NAME,
            CENTROID_LAT,
            CENTROID_LON,
            TOPIC,
            INTEREST_FAN_COUNT,
            TOTAL_FAN_COUNT,
            AVID_FAN_COUNT,
            AVG_INCOME
        FROM VERSION3_MASTER
        WHERE TOPIC IN ({placeholders})
        """
        params = list(topics)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Organize data by city (using lat/lon as unique identifier)
        city_data = {}
        for row in rows:
            # Use centroid lat/lon as the unique key
            lat = float(row[2]) if row[2] else 0
            lon = float(row[3]) if row[3] else 0
            city_key = f"{lat},{lon}"
            
            if city_key not in city_data:
                city_data[city_key] = {
                    'city': row[0],
                    'state': row[1],
                    'lat': lat,
                    'lon': lon,
                    'interests': {}
                }
            
            topic = row[4]
            city_data[city_key]['interests'][topic] = {
                'interestFanCount': int(row[5]) if row[5] else 0,
                'totalFanCount': int(row[6]) if row[6] else 0,
                'avidFanCount': int(row[7]) if row[7] else 0,
                'avgIncome': float(row[8]) if row[8] else 0
            }
        
        # Convert to list
        result = list(city_data.values())
        
        # Apply Top N filtering if requested
        if top_n and top_n > 0 and size_by:
            # Sort by the sizeBy interest fan count
            result_with_size = []
            for city in result:
                if size_by in city['interests']:
                    city['_sort_value'] = city['interests'][size_by]['interestFanCount']
                    result_with_size.append(city)
            
            # Sort descending and take top N
            result_with_size.sort(key=lambda x: x['_sort_value'], reverse=True)
            result = result_with_size[:top_n]
            
            # Remove temporary sort field
            for city in result:
                del city['_sort_value']
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /api/heatmap: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)