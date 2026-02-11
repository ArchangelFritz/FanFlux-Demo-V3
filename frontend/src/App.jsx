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
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch teams and interests on mount
  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE_URL}/teams`),
      axios.get(`${API_BASE_URL}/interests`)
    ]).then(([teamsRes, interestsRes]) => {
      setTeams(teamsRes.data);                    // Data is array directly
      setInterests(interestsRes.data);            // Data is array directly
      if (teamsRes.data.length > 0) {
        setSelectedTeam(teamsRes.data[0].name);   // Access .name property
      }
      if (interestsRes.data.length > 1) {
        setSizeBy(interestsRes.data[0]);          // Already a string
        setColorBy(interestsRes.data[1]);         // Already a string
      }
    }).catch(err => {
      console.error('Error loading initial data:', err);
    });
  }, []);

  // Fetch heatmap data when selections change
  useEffect(() => {
    if (selectedTeam && sizeBy && colorBy) {
      setLoading(true);
      axios.get(`${API_BASE_URL}/heatmap`, {
        params: { team: selectedTeam, sizeBy, colorBy }
      }).then(res => {
        setMapData(res.data);                     // Data is cities array directly
        setLoading(false);
      }).catch(err => {
        console.error('Error loading heatmap:', err);
        setLoading(false);
      });
    }
  }, [selectedTeam, sizeBy, colorBy]);

  return (
    <div className="app">
      <Sidebar 
        teams={teams}
        selectedTeam={selectedTeam}
        onTeamChange={setSelectedTeam}
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
          <Map cities={mapData || []} />
        )}
      </div>
    </div>
  );
}

export default App;