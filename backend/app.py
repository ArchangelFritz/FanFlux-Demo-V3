from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
import os

app = Flask(__name__)
CORS(app)

# Azure SQL connection
def get_db_connection():
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={os.environ.get('AZURE_SQL_SERVER')};"
        f"Database={os.environ.get('AZURE_SQL_DATABASE')};"
        f"Uid={os.environ.get('AZURE_SQL_USERNAME')};"
        f"Pwd={os.environ.get('AZURE_SQL_PASSWORD')};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str)

@app.route('/api/teams')
def get_teams():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT TEAM_NAME 
        FROM V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL
        ORDER BY TEAM_NAME
    """)
    teams = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'teams': teams})

@app.route('/api/interests')
def get_interests():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT INTEREST 
        FROM V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL
        ORDER BY INTEREST
    """)
    interests = ['Total Fan Count', 'Avid Fan Count', 'Average Income'] + [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'interests': interests})

@app.route('/api/heatmap')
def get_heatmap():
    team = request.args.get('team')
    size_by = request.args.get('sizeBy')
    color_by = request.args.get('colorBy')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get team summary
    cursor.execute("""
        SELECT 
            SUM(TOTAL_FAN_COUNT) as totalFans,
            SUM(AVID_FAN_COUNT) as avidFans,
            AVG(CAST(AVG_INCOME AS FLOAT)) as avgIncome
        FROM (
            SELECT DISTINCT CITY_LAT, CITY_LON, TOTAL_FAN_COUNT, AVID_FAN_COUNT, AVG_INCOME
            FROM V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL
            WHERE TEAM_NAME = ?
        ) as cities
    """, team)
    
    summary = cursor.fetchone()
    team_summary = {
        'teamName': team,
        'totalFans': int(summary[0]) if summary[0] else 0,
        'avidFans': int(summary[1]) if summary[1] else 0,
        'avgIncome': int(summary[2]) if summary[2] else 0
    }
    
    # Get heatmap data
    cursor.execute("""
        SELECT 
            c1.CITY_NAME as cityName,
            c1.STATE_NAME as stateName,
            c1.CITY_LAT as cityLat,
            c1.CITY_LON as cityLon,
            c1.INTEREST_FAN_COUNT as sizeValue,
            c2.INTEREST_FAN_COUNT as colorValue,
            c1.TOTAL_FAN_COUNT as totalFanCount,
            c1.AVID_FAN_COUNT as avidFanCount,
            CAST(c1.AVG_INCOME AS INT) as avgIncome
        FROM V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL c1
        JOIN V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL c2
            ON c1.TEAM_NAME = c2.TEAM_NAME
            AND c1.CITY_LAT = c2.CITY_LAT
            AND c1.CITY_LON = c2.CITY_LON
        WHERE c1.TEAM_NAME = ?
          AND c1.INTEREST = ?
          AND c2.INTEREST = ?
    """, team, size_by, color_by)
    
    cities = []
    for row in cursor.fetchall():
        cities.append({
            'cityName': row[0],
            'stateName': row[1],
            'cityLat': float(row[2]),
            'cityLon': float(row[3]),
            'sizeValue': int(row[4]) if row[4] else 0,
            'colorValue': int(row[5]) if row[5] else 0,
            'totalFanCount': int(row[6]) if row[6] else 0,
            'avidFanCount': int(row[7]) if row[7] else 0,
            'avgIncome': int(row[8]) if row[8] else 0
        })
    
    conn.close()
    
    return jsonify({
        'teamSummary': team_summary,
        'cities': cities
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)