from flask import Flask, jsonify, request
from flask_cors import CORS
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import os

app = Flask(__name__)
CORS(app)

# Load private key
def load_private_key():
    """Load the private key from file"""
    key_path = os.path.expanduser('~/snowflake_key.p8')
    with open(key_path, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    
    pkb = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pkb

# Snowflake connection config
SNOWFLAKE_CONFIG = {
    'user': 'FANFLUX',
    'account': 'KXZRGCU-PN74371',
    'warehouse': 'COMPUTE_WH',
    'database': 'FANFLUX',
    'schema': 'V3',
    'private_key': load_private_key()
}

def get_snowflake_connection():
    """Create and return a Snowflake connection"""
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

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
    app.run(debug=True, host='0.0.0.0', port=5000)