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

    // Calculate min/max for normalization
    const sizeValues = cities.map(c => c.sizeValue).filter(v => v > 0);
    const colorValues = cities.map(c => c.colorValue).filter(v => v > 0);
    
    const minSize = Math.min(...sizeValues);
    const maxSize = Math.max(...sizeValues);
    const minColor = Math.min(...colorValues);
    const maxColor = Math.max(...colorValues);

    console.log('Size range:', minSize, '-', maxSize);
    console.log('Color range:', minColor, '-', maxColor);

    // Normalize function
    const normalize = (value, min, max) => {
      if (max === min) return 0.5;
      return (value - min) / (max - min);
    };

    // Convert cities to GeoJSON
    const geojsonData = {
      type: 'FeatureCollection',
      features: cities.map(city => {
        const normalizedSize = normalize(city.sizeValue, minSize, maxSize);
        const normalizedColor = normalize(city.colorValue, minColor, maxColor);
        
        return {
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [city.cityLon, city.cityLat]
          },
          properties: {
            cityName: city.cityName,
            stateName: city.stateName,
            totalFanCount: city.totalFanCount,
            sizeValue: city.sizeValue,
            colorValue: city.colorValue,
            // Normalized values for rendering
            circleRadius: 5 + (normalizedSize * 20), // 5-25 pixels
            circleOpacity: 0.3 + (normalizedColor * 0.7) // 0.3-1.0
          }
        };
      })
    };

    // Wait for map to load
    map.current.on('load', () => {
      // Remove existing source and layers if they exist
      if (map.current.getSource('cities')) {
        map.current.removeLayer('cities-layer');
        map.current.removeSource('cities');
      }

      // Add source
      map.current.addSource('cities', {
        type: 'geojson',
        data: geojsonData
      });

      // Add layer
      map.current.addLayer({
        id: 'cities-layer',
        type: 'circle',
        source: 'cities',
        paint: {
          'circle-radius': ['get', 'circleRadius'],
          'circle-color': '#ff6464',
          'circle-opacity': ['get', 'circleOpacity'],
          'circle-stroke-width': 2,
          'circle-stroke-color': 'rgba(255, 255, 255, 0.8)'
        }
      });

      // Add click popup
      map.current.on('click', 'cities-layer', (e) => {
        const props = e.features[0].properties;
        new mapboxgl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(`
            <div style="color: black; padding: 5px;">
              <strong>${props.cityName}, ${props.stateName}</strong><br/>
              <strong>Total Fans:</strong> ${parseInt(props.totalFanCount).toLocaleString()}<br/>
              <strong>Size Value:</strong> ${parseInt(props.sizeValue).toLocaleString()}<br/>
              <strong>Color Value:</strong> ${parseInt(props.colorValue).toLocaleString()}
            </div>
          `)
          .addTo(map.current);
      });

      // Change cursor on hover
      map.current.on('mouseenter', 'cities-layer', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', 'cities-layer', () => {
        map.current.getCanvas().style.cursor = '';
      });
    });

    // If map already loaded, update data directly
    if (map.current.isStyleLoaded()) {
      if (map.current.getSource('cities')) {
        map.current.getSource('cities').setData(geojsonData);
      } else {
        // Map loaded but source doesn't exist yet
        map.current.addSource('cities', {
          type: 'geojson',
          data: geojsonData
        });

        map.current.addLayer({
          id: 'cities-layer',
          type: 'circle',
          source: 'cities',
          paint: {
            'circle-radius': ['get', 'circleRadius'],
            'circle-color': '#ff6464',
            'circle-opacity': ['get', 'circleOpacity'],
            'circle-stroke-width': 2,
            'circle-stroke-color': 'rgba(255, 255, 255, 0.8)'
          }
        });

        map.current.on('click', 'cities-layer', (e) => {
          const props = e.features[0].properties;
          new mapboxgl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(`
              <div style="color: black; padding: 5px;">
                <strong>${props.cityName}, ${props.stateName}</strong><br/>
                <strong>Total Fans:</strong> ${parseInt(props.totalFanCount).toLocaleString()}<br/>
                <strong>Size Value:</strong> ${parseInt(props.sizeValue).toLocaleString()}<br/>
                <strong>Color Value:</strong> ${parseInt(props.colorValue).toLocaleString()}
              </div>
            `)
            .addTo(map.current);
        });

        map.current.on('mouseenter', 'cities-layer', () => {
          map.current.getCanvas().style.cursor = 'pointer';
        });

        map.current.on('mouseleave', 'cities-layer', () => {
          map.current.getCanvas().style.cursor = '';
        });
      }
    }
  }, [cities]);

  return <div ref={mapContainer} className="map-container" />;
}