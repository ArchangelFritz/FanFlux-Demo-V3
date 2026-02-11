import { useState, useEffect } from 'react';
import axios from 'axios';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import Toolbar from './components/Toolbar';
import './App.css';

const API_BASE_URL = 'https://fanflux-api-b8cxfnggbzchc7de.centralus-01.azurewebsites.net';

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
      axios.get(`${API_URL}/teams`),
      axios.get(`${API_URL}/interests`)
    ]).then(([teamsRes, interestsRes]) => {
      setTeams(teamsRes.data.teams);
      setInterests(interestsRes.data.interests);
      setSelectedTeam(teamsRes.data.teams[0]);
      setSizeBy(interestsRes.data.interests[0]);
      setColorBy(interestsRes.data.interests[1]);
    });
  }, []);

  // Fetch heatmap data when selections change
  useEffect(() => {
    if (selectedTeam && sizeBy && colorBy) {
      setLoading(true);
      axios.get(`${API_URL}/heatmap`, {
        params: { team: selectedTeam, sizeBy, colorBy }
      }).then(res => {
        setMapData(res.data);
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
        teamSummary={mapData?.teamSummary}
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
          <div className="loading">Loading...</div>
        ) : (
          <Map cities={mapData?.cities || []} />
        )}
      </div>
    </div>
  );
}

export default App;