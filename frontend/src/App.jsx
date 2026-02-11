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
  const [topN, setTopN] = useState(100); // NEW: Top N filter (null = show all)
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
      console.log('Sample team:', teamsRes.data[0]);
      
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
      console.log('Fetching heatmap for:', {
        team: selectedTeam,
        sizeBy,
        colorBy,
        topN: topN || 'all'
      });
      
      setLoading(true);
      
      const params = { 
        team: selectedTeam, 
        sizeBy, 
        colorBy 
      };
      
      // Add topN parameter if set
      if (topN) {
        params.topN = topN;
      }
      
      axios.get(`${API_BASE_URL}/heatmap`, { params })
        .then(res => {
          console.log('Heatmap data received:', res.data.length, 'cities');
          console.log('Sample city:', res.data[0]);
          setRawMapData(res.data);
          setLoading(false);
        }).catch(err => {
          console.error('Error loading heatmap:', err);
          setLoading(false);
        });
    }
  }, [selectedTeam, sizeBy, colorBy, topN]);

  // Transform backend data to Map component format
  const transformedCities = rawMapData?.map(city => {
    const sizeInterest = city.interests[sizeBy] || {};
    const colorInterest = city.interests[colorBy] || {};
    
    return {
      cityName: city.city,
      stateName: city.state,
      cityLat: city.lat,
      cityLon: city.lon,
      sizeValue: sizeInterest.interestFanCount || 0,
      colorValue: colorInterest.interestFanCount || 0,
      totalFanCount: sizeInterest.totalFanCount || colorInterest.totalFanCount || 0
    };
  }) || [];

  // Log transformed data for debugging
  useEffect(() => {
    if (transformedCities.length > 0) {
      console.log('Transformed cities:', transformedCities.length);
      console.log('Sample transformed:', transformedCities[0]);
      console.log('Size value range:', {
        min: Math.min(...transformedCities.map(c => c.sizeValue)),
        max: Math.max(...transformedCities.map(c => c.sizeValue))
      });
      console.log('Color value range:', {
        min: Math.min(...transformedCities.map(c => c.colorValue)),
        max: Math.max(...transformedCities.map(c => c.colorValue))
      });
    }
  }, [transformedCities]);

  // Get current team's stats for sidebar
  const currentTeamData = teams.find(t => t.name === selectedTeam);
  const teamSummary = currentTeamData ? {
    totalFans: currentTeamData.totalFans,
    avidFans: currentTeamData.avidFans,
    avgIncome: currentTeamData.avgIncome || 0
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
        topN={topN}
        onTopNChange={setTopN}
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