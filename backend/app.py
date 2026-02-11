from flask import Flask, jsonify, request
from flask_cors import CORS
import snowflake.connector
import os

import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
CORS(app)

def get_private_key_from_env():
    """
    Load private key from environment variable.
    The key should be stored as a base64-encoded string or PEM format.
    """
    private_key_data = os.getenv('SNOWFLAKE_PRIVATE_KEY')
    
    if not private_key_data:
        return None
    
    # If the key is base64 encoded, decode it first
    # If it's already PEM format, use it directly
    try:
        # Try to load as PEM directly
        if private_key_data.startswith('-----BEGIN'):
            private_key_bytes = private_key_data.encode('utf-8')
        else:
            # Assume base64 encoded
            import base64
            private_key_bytes = base64.b64decode(private_key_data)
        
        # Load the private key
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
            backend=default_backend()
        )
        
        # Extract the key in the format Snowflake expects
        pkb = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return pkb
    except Exception as e:
        print(f"Error loading private key: {e}")
        return None

# Snowflake connection config - ALL from environment variables
def get_snowflake_config():
    """Build Snowflake configuration, preferring key-pair auth over password"""
    config = {
        'user': os.getenv('SNOWFLAKE_USER'),
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA')
    }
    
    # Try key-pair authentication first (preferred for MFA accounts)
    private_key = get_private_key_from_env()
    if private_key:
        config['private_key'] = private_key
        print("Using key-pair authentication")
    else:
        # Fall back to password authentication
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
    
    # Validate required fields (except auth which is validated in get_snowflake_config)
    required_vars = ['user', 'account', 'warehouse', 'database', 'schema']
    missing = [var for var in required_vars if not config.get(var)]
    
    if missing:
        raise ValueError(f"Missing required Snowflake environment variables: {', '.join([f'SNOWFLAKE_{v.upper()}' for v in missing])}")
    
    return snowflake.connector.connect(**config)

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of unique teams with their total fan counts"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Query to get unique teams with aggregated metrics
        query = """
        SELECT 
            TEAM_NAME,
            SUM(TOTAL_FAN_COUNT) as TOTAL_FANS,
            SUM(AVID_FAN_COUNT) as AVID_FANS,
            SUM(INTEREST_FAN_COUNT) as INTEREST_FANS
        FROM TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL
        GROUP BY TEAM_NAME
        ORDER BY TEAM_NAME
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        teams = []
        for row in rows:
            teams.append({
                'name': row[0],
                'totalFans': int(row[1]) if row[1] else 0,
                'avidFans': int(row[2]) if row[2] else 0,
                'interestFans': int(row[3]) if row[3] else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(teams)
    
    except Exception as e:
        print(f"Error in /api/teams: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interests', methods=['GET'])
def get_interests():
    """Get list of unique interests"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT INTEREST
        FROM TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL
        WHERE INTEREST IS NOT NULL
        ORDER BY INTEREST
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
    """Get heatmap data filtered by team and interests"""
    try:
        team = request.args.get('team')
        size_by = request.args.get('sizeBy')
        color_by = request.args.get('colorBy')
        
        if not team:
            return jsonify({'error': 'team parameter is required'}), 400
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Build the query with filters
        query = """
        SELECT 
            CITY_NAME,
            STATE_NAME,
            CITY_LAT,
            CITY_LON,
            INTEREST,
            INTEREST_FAN_COUNT,
            TOTAL_FAN_COUNT,
            AVID_FAN_COUNT,
            AVG_INCOME
        FROM TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL
        WHERE TEAM_NAME = %s
        """
        
        params = [team]
        
        # Add interest filters if provided
        if size_by and color_by:
            query += " AND INTEREST IN (%s, %s)"
            params.extend([size_by, color_by])
        elif size_by:
            query += " AND INTEREST = %s"
            params.append(size_by)
        elif color_by:
            query += " AND INTEREST = %s"
            params.append(color_by)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Organize data by city
        city_data = {}
        for row in rows:
            city_key = f"{row[0]}, {row[1]}"  # "City, State"
            
            if city_key not in city_data:
                city_data[city_key] = {
                    'city': row[0],
                    'state': row[1],
                    'lat': float(row[2]) if row[2] else 0,
                    'lon': float(row[3]) if row[3] else 0,
                    'interests': {}
                }
            
            interest = row[4]
            city_data[city_key]['interests'][interest] = {
                'interestFanCount': int(row[5]) if row[5] else 0,
                'totalFanCount': int(row[6]) if row[6] else 0,
                'avidFanCount': int(row[7]) if row[7] else 0,
                'avgIncome': float(row[8]) if row[8] else 0
            }
        
        # Convert to list
        result = list(city_data.values())
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in /api/heatmap: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use PORT environment variable for Azure, default to 5000 locally
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)