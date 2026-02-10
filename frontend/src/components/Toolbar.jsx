export default function Toolbar({ interests, sizeBy, colorBy, onSizeChange, onColorChange }) {
    return (
      <div className="toolbar">
        <div className="control">
          <label>Size Bubbles By</label>
          <select value={sizeBy} onChange={(e) => onSizeChange(e.target.value)}>
            {interests.map(int => (
              <option key={int} value={int}>{int}</option>
            ))}
          </select>
        </div>
  
        <div className="control">
          <label>Color Bubbles By</label>
          <select value={colorBy} onChange={(e) => onColorChange(e.target.value)}>
            {interests.map(int => (
              <option key={int} value={int}>{int}</option>
            ))}
          </select>
        </div>
      </div>
    );
  }