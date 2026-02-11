import { useState, useEffect } from 'react';
import axios from 'axios';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import Toolbar from './components/Toolbar';
import './App.css';

const API_BASE_URL = 'https://fanflux-api-b8cxfnggbzchc7de.centralus-01.azurewebsites.net/api';

function App() {
  const [teams, setTeams] = useState([]);
  const [interests, setInterests] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState('');
  const [sizeBy, setSizeBy] = useState('');
  const [colorBy, setColorBy] = useState('');
  const [rawMapData, setRawMapData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch teams and interests on mount
  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE_URL}/teams`),
      axios.get(`${API_BASE_URL}/interests`)
    ]).then(([teamsRes, interestsRes]) => {
      console.log('Teams loaded:', teamsRes.data.length);
      console.log('Interests loaded:', interestsRes.data.length);
      
      setTeams(teamsRes.data);
      setInterests(interestsRes.data);
      
      if (teamsRes.data.length > 0) {
        setSelectedTeam(teamsRes.data[0].name);
      }
      if (interestsRes.data.length > 1) {
        setSizeBy(interestsRes.data[0]);
        setColorBy(interestsRes.data[1]);
      }
    }).catch(err => {
      console.error('Error loading initial data:', err);
    });
  }, []);

  // Fetch heatmap data when selections change
  useEffect(() => {
    if (selectedTeam && sizeBy && colorBy) {
      console.log('Fetching heatmap for:', selectedTeam, sizeBy, colorBy);
      setLoading(true);
      
      axios.get(`${API_BASE_URL}/heatmap`, {
        params: { team: selectedTeam, sizeBy, colorBy }
      }).then(res => {
        console.log('Heatmap data received:', res.data.length, 'cities');
        setRawMapData(res.data);
        setLoading(false);
      }).catch(err => {
        console.error('Error loading heatmap:', err);
        setLoading(false);
      });
    }
  }, [selectedTeam, sizeBy, colorBy]);

  // Transform backend data to Map component format
  const transformedCities = rawMapData?.map(city => {
    const sizeInterest = city.interests[sizeBy] || {};
    const colorInterest = city.interests[colorBy] || {};
    
    return {
      // Map expects these exact property names
      cityName: city.city,
      stateName: city.state,
      cityLat: city.lat,
      cityLon: city.lon,
      // Extract interest fan counts for size and color
      sizeValue: sizeInterest.interestFanCount || 0,
      colorValue: colorInterest.interestFanCount || 0,
      // Total fans for this city (use either interest's totalFanCount)
      totalFanCount: sizeInterest.totalFanCount || colorInterest.totalFanCount || 0
    };
  }) || [];

  // Get current team's stats for sidebar
  const currentTeamData = teams.find(t => t.name === selectedTeam);
  const teamSummary = currentTeamData ? {
    totalFans: currentTeamData.totalFans,
    avidFans: currentTeamData.avidFans,
    // Calculate average income across all cities for this team
    avgIncome: rawMapData ? 
      Math.round(
        rawMapData.reduce((sum, city) => {
          const interests = Object.values(city.interests);
          const avgIncome = interests.length > 0 ? interests[0].avgIncome : 0;
          return sum + avgIncome;
        }, 0) / rawMapData.length
      ) : 0
  } : null;

  // Get list of team names for sidebar dropdown
  const teamNames = teams.map(t => t.name);

  return (
    <div className="app">
      <Sidebar 
        teams={teamNames}
        selectedTeam={selectedTeam}
        onTeamChange={setSelectedTeam}
        teamSummary={teamSummary}
      />
      <div className="main">
        <Toolbar 
          interests={interests}
          sizeBy={sizeBy}
          colorBy={colorBy}
          onSizeChange={setSizeBy}
          onColorChange={setColorBy}
        />
        {loading ? (
          <div className="loading">Loading map data...</div>
        ) : (
          <Map cities={transformedCities} />
        )}
      </div>
    </div>
  );
}

export default App;