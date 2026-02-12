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
        'schema': os.getenv('SNOWFLAKE_SCHEMA'),
        'client_session_keep_alive': True  # Optional
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
    """Get compound heatmap data: team fans who also like specific interests"""
    try:
        team = request.args.get('team')
        size_by = request.args.get('sizeBy')
        color_by = request.args.get('colorBy')
        top_n = request.args.get('topN', type=int)
        
        if not team:
            return jsonify({'error': 'team parameter is required'}), 400
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Query VERSION3_MASTER_COMPOUND for compound data
        # Get three interests: team itself (baseline), sizeBy, and colorBy
        interests_to_fetch = {team}  # Always include team as baseline
        if size_by != 'Average Income':
            interests_to_fetch.add(size_by)
        if color_by != 'Average Income':
            interests_to_fetch.add(color_by)
        
        placeholders = ', '.join(['%s'] * len(interests_to_fetch))
        query = f"""
        SELECT 
            CITY_NAME,
            STATE_NAME,
            CENTROID_LAT,
            CENTROID_LON,
            INTEREST,
            UNIQUE_FANS,
            TOTAL_FAN_COUNT,
            AVID_FAN_COUNT,
            AVG_INCOME
        FROM VERSION3_MASTER_COMPOUND
        WHERE TEAM = %s
          AND INTEREST IN ({placeholders})
        """
        
        params = [team] + list(interests_to_fetch)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Organize data by city
        city_data = {}
        for row in rows:
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
            
            interest = row[4]
            city_data[city_key]['interests'][interest] = {
                'interestFanCount': int(row[5]) if row[5] else 0,  # Compound fan count
                'totalFanCount': int(row[6]) if row[6] else 0,
                'avidFanCount': int(row[7]) if row[7] else 0,
                'avgIncome': float(row[8]) if row[8] else 0
            }
        
        result = list(city_data.values())
        
        # Apply Top N filtering
        if top_n and top_n > 0:
            # Sort by sizeBy interest (or team baseline if Average Income)
            sort_key = team if size_by == 'Average Income' else size_by
            
            result_with_size = []
            for city in result:
                if sort_key in city['interests']:
                    city['_sort_value'] = city['interests'][sort_key]['interestFanCount']
                    result_with_size.append(city)
            
            result_with_size.sort(key=lambda x: x['_sort_value'], reverse=True)
            result = result_with_size[:top_n]
            
            for city in result:
                del city['_sort_value']
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /api/heatmap: {e}")
        return jsonify({'error': str(e)}), 500
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /api/heatmap: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/heatmap-compound', methods=['GET'])
def get_heatmap_compound():
    """Get compound heatmap data: team fans who also like specific interests"""
    try:
        team = request.args.get('team')
        size_by = request.args.get('sizeBy')
        color_by = request.args.get('colorBy')
        top_n = request.args.get('topN', type=int)
        
        if not team:
            return jsonify({'error': 'team parameter is required'}), 400
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Build compound query
        # For each city, get:
        # 1. Team baseline (total team fans)
        # 2. Team fans who also like sizeBy interest
        # 3. Team fans who also like colorBy interest
        
        query = """
        WITH TeamFans AS (
            -- Get all team fans by city
            SELECT DISTINCT
                CITY_NAME,
                STATE_NAME,
                CENTROID_LAT,
                CENTROID_LON,
                AA_ID
            FROM COMPOUND_FANS_MV
            WHERE TOPIC = %s
        ),
        TeamCityCounts AS (
            -- Count team fans per city
            SELECT 
                CITY_NAME,
                STATE_NAME,
                CENTROID_LAT,
                CENTROID_LON,
                COUNT(DISTINCT AA_ID) as TEAM_TOTAL_FANS,
                COUNT(DISTINCT CASE WHEN EXISTS (
                    SELECT 1 FROM COMPOUND_FANS_MV cf 
                    WHERE cf.AA_ID = TeamFans.AA_ID 
                    AND cf.FREQUENCY >= 5 
                    AND cf.TOPIC = %s
                ) THEN AA_ID END) as TEAM_AVID_FANS
            FROM TeamFans
            GROUP BY CITY_NAME, STATE_NAME, CENTROID_LAT, CENTROID_LON
        )
        SELECT 
            tcc.CITY_NAME,
            tcc.STATE_NAME,
            tcc.CENTROID_LAT,
            tcc.CENTROID_LON,
            tcc.TEAM_TOTAL_FANS,
            tcc.TEAM_AVID_FANS,
            
            -- Size interest: team fans who also like this interest
            COUNT(DISTINCT CASE 
                WHEN size_interest.AA_ID IS NOT NULL THEN tf.AA_ID 
            END) as SIZE_INTEREST_FANS,
            
            -- Color interest: team fans who also like this interest  
            COUNT(DISTINCT CASE 
                WHEN color_interest.AA_ID IS NOT NULL THEN tf.AA_ID 
            END) as COLOR_INTEREST_FANS,
            
            -- Average income of team fans in this city
            AVG(CASE 
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%Under $10,000%' THEN 5000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$10,000-$19,999%' THEN 15000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$20,000-$29,999%' THEN 25000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$30,000-$39,999%' THEN 35000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$40,000-$49,999%' THEN 45000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$50,000-$59,999%' THEN 55000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$60,000-$74,999%' THEN 67500
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$75,000-$99,999%' THEN 87500
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$100,000-$124,999%' THEN 112500
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$125,000-$149,999%' THEN 137500
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$150,000-$174,999%' THEN 162500
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$175,000-$199,999%' THEN 187500
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$200,000-$249,999%' THEN 225000
                WHEN tf_income.DISCRETIONARY_INCOME LIKE '%$250,000%' THEN 300000
            END) as AVG_INCOME
            
        FROM TeamCityCounts tcc
        JOIN TeamFans tf 
            ON tcc.CITY_NAME = tf.CITY_NAME 
            AND tcc.CENTROID_LAT = tf.CENTROID_LAT
            AND tcc.CENTROID_LON = tf.CENTROID_LON
        LEFT JOIN FANS_COMPLETE size_interest
            ON tf.AA_ID = size_interest.AA_ID
            AND size_interest.TOPIC = %s
            AND size_interest.CENTROID_LAT = tf.CENTROID_LAT
            AND size_interest.CENTROID_LON = tf.CENTROID_LON
        LEFT JOIN FANS_COMPLETE color_interest
            ON tf.AA_ID = color_interest.AA_ID
            AND color_interest.TOPIC = %s
            AND color_interest.CENTROID_LAT = tf.CENTROID_LAT
            AND color_interest.CENTROID_LON = tf.CENTROID_LON
        LEFT JOIN COMPOUND_FANS_MV tf_income
            ON tf.AA_ID = tf_income.AA_ID
            AND tf_income.CENTROID_LAT = tf.CENTROID_LAT
            AND tf_income.CENTROID_LON = tf.CENTROID_LON
            
        GROUP BY 
            tcc.CITY_NAME, tcc.STATE_NAME, tcc.CENTROID_LAT, tcc.CENTROID_LON,
            tcc.TEAM_TOTAL_FANS, tcc.TEAM_AVID_FANS
        """
        
        params = [team, team, size_by, color_by]
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Organize results
        result = []
        for row in rows:
            city_data = {
                'city': row[0],
                'state': row[1],
                'lat': float(row[2]) if row[2] else 0,
                'lon': float(row[3]) if row[3] else 0,
                'teamTotalFans': int(row[4]) if row[4] else 0,
                'teamAvidFans': int(row[5]) if row[5] else 0,
                'sizeInterestFans': int(row[6]) if row[6] else 0,
                'colorInterestFans': int(row[7]) if row[7] else 0,
                'avgIncome': float(row[8]) if row[8] else 0
            }
            result.append(city_data)
        
        # Apply Top N filtering if requested
        if top_n and top_n > 0:
            result.sort(key=lambda x: x['sizeInterestFans'], reverse=True)
            result = result[:top_n]
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /api/heatmap-compound: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)