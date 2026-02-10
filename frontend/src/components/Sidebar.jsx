export default function Sidebar({ teams, selectedTeam, onTeamChange, teamSummary }) {
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
      </div>
    );
  }