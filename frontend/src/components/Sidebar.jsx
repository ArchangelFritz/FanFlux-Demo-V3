export default function Sidebar({ teams, selectedTeam, onTeamChange, teamSummary, topN, onTopNChange }) {
    return (
      <div className="sidebar">
        <h2>Team Selector</h2>
        
        <label>Select Team</label>
        <select value={selectedTeam} onChange={(e) => onTeamChange(e.target.value)}>
          {teams.map(team => (
            <option key={team} value={team}>{team}</option>
          ))}
        </select>
  
        {teamSummary && (
          <div className="team-stats">
            <h3>Total Fan Count</h3>
            <p className="big-number">{teamSummary.totalFans.toLocaleString()}</p>
            
            <h3>Avid Fans</h3>
            <p>{teamSummary.avidFans.toLocaleString()}</p>
            
            <h3>Avg Income</h3>
            <p>${teamSummary.avgIncome.toLocaleString()}</p>
          </div>
        )}
  
        <div className="team-stats" style={{ marginTop: '30px' }}>
          <h3>Map Filters</h3>
          <label>Show Top N Cities</label>
          <select 
            value={topN || 'all'} 
            onChange={(e) => onTopNChange(e.target.value === 'all' ? null : parseInt(e.target.value))}
          >
            <option value="all">Show All Cities</option>
            <option value="10">Top 10</option>
            <option value="25">Top 25</option>
            <option value="50">Top 50</option>
            <option value="100">Top 100</option>
            <option value="250">Top 250</option>
          </select>
        </div>
      </div>
    );
  }