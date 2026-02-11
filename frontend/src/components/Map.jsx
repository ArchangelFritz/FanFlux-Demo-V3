import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

export default function Map({ cities }) {
  const mapContainer = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (!map.current) {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-98, 39],
        zoom: 3.5
      });
    }
  }, []);

  useEffect(() => {
    if (!map.current || !cities.length) return;

    console.log('Rendering', cities.length, 'cities on map');

    // Clear existing markers
    const markers = document.getElementsByClassName('mapboxgl-marker');
    while (markers[0]) {
      markers[0].remove();
    }

    // Calculate min/max for normalization
    const sizeValues = cities.map(c => c.sizeValue).filter(v => v > 0);
    const colorValues = cities.map(c => c.colorValue).filter(v => v > 0);
    
    const minSize = Math.min(...sizeValues);
    const maxSize = Math.max(...sizeValues);
    const minColor = Math.min(...colorValues);
    const maxColor = Math.max(...colorValues);

    console.log('Size range:', minSize, '-', maxSize);
    console.log('Color range:', minColor, '-', maxColor);

    // Normalize function: map value to 0-1 range
    const normalize = (value, min, max) => {
      if (max === min) return 0.5;
      return (value - min) / (max - min);
    };

    // Add new markers
    cities.forEach(city => {
      // Normalize size (0-1), then scale to pixel range (5-50px)
      const normalizedSize = normalize(city.sizeValue, minSize, maxSize);
      const size = 5 + (normalizedSize * 45); // 5px to 50px range

      // Normalize color (0-1) for opacity
      const normalizedColor = normalize(city.colorValue, minColor, maxColor);
      const opacity = 0.3 + (normalizedColor * 0.7); // 0.3 to 1.0 range

      const el = document.createElement('div');
      el.className = 'marker';
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      el.style.backgroundColor = `rgba(255, 100, 100, ${opacity})`;
      el.style.borderRadius = '50%';
      el.style.border = '2px solid rgba(255, 255, 255, 0.8)';
      el.style.cursor = 'pointer';

      new mapboxgl.Marker(el)
        .setLngLat([city.cityLon, city.cityLat])
        .setPopup(new mapboxgl.Popup({ offset: 25 }).setHTML(`
          <div style="color: black; padding: 5px;">
            <strong>${city.cityName}, ${city.stateName}</strong><br/>
            <strong>Total Fans:</strong> ${city.totalFanCount.toLocaleString()}<br/>
            <strong>Size Value:</strong> ${city.sizeValue.toLocaleString()}<br/>
            <strong>Color Value:</strong> ${city.colorValue.toLocaleString()}
          </div>
        `))
        .addTo(map.current);
    });
  }, [cities]);

  return <div ref={mapContainer} className="map-container" />;
}