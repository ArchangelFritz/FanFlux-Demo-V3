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

    // Clear existing markers
    const markers = document.getElementsByClassName('mapboxgl-marker');
    while (markers[0]) {
      markers[0].remove();
    }

    // Add new markers
    cities.forEach(city => {
      const size = Math.sqrt(city.sizeValue) / 2;
      const opacity = city.colorValue / 3000;

      const el = document.createElement('div');
      el.className = 'marker';
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      el.style.backgroundColor = `rgba(255, 100, 100, ${opacity})`;
      el.style.borderRadius = '50%';
      el.style.border = '2px solid white';

      new mapboxgl.Marker(el)
        .setLngLat([city.cityLon, city.cityLat])
        .setPopup(new mapboxgl.Popup().setHTML(`
          <strong>${city.cityName}, ${city.stateName}</strong><br/>
          Fans: ${city.totalFanCount.toLocaleString()}<br/>
          Size Value: ${city.sizeValue}<br/>
          Color Value: ${city.colorValue}
        `))
        .addTo(map.current);
    });
  }, [cities]);

  return <div ref={mapContainer} className="map-container" />;
}