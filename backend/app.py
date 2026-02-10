from flask import Flask, jsonify, request
from flask_cors import CORS
from mock_data import MOCK_TEAMS, MOCK_INTERESTS, generate_mock_heatmap_data, get_mock_team_summary

app = Flask(__name__)
CORS(app)

@app.route('/api/teams')
def get_teams():
    return jsonify({'teams': MOCK_TEAMS})

@app.route('/api/interests')
def get_interests():
    return jsonify({'interests': MOCK_INTERESTS})

@app.route('/api/heatmap')
def get_heatmap():
    team = request.args.get('team')
    size_by = request.args.get('sizeBy')
    color_by = request.args.get('colorBy')
    
    cities = generate_mock_heatmap_data(team, size_by, color_by)
    team_summary = get_mock_team_summary(team, cities)  # Pass cities data
    
    return jsonify({
        'teamSummary': team_summary,
        'cities': cities
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)