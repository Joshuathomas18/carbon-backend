import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, Loader2, CheckCircle2, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';

// Import CSS
import 'leaflet/dist/leaflet.css';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

// Fix for default marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Calculate polygon area in hectares using geodesic Shoelace formula
const calculateAreaHectares = (latlngs) => {
  if (!latlngs || latlngs.length < 3) return 0;

  let area = 0;
  const R = 6371000; // Earth radius in meters

  for (let i = 0; i < latlngs.length; i++) {
    const p1 = latlngs[i];
    const p2 = latlngs[(i + 1) % latlngs.length];

    const lat1 = (p1.lat * Math.PI) / 180;
    const lat2 = (p2.lat * Math.PI) / 180;
    const dLng = ((p2.lng - p1.lng) * Math.PI) / 180;

    area += Math.sin(lat1) * Math.cos(lat2) * Math.sin(dLng);
    area -= Math.sin(lat2) * Math.cos(lat1) * Math.sin(dLng);
  }

  area = Math.abs(area * R * R) / 2;
  return area / 10000; // Convert m² to hectares
};

// Map controller: activates polygon drawing
const MapManager = ({ position, onPolygonChange }) => {
  const map = useMap();
  const drawLayerRef = useRef(null);

  useEffect(() => {
    if (!map) return;

    // Center map on position (either from session token or default)
    if (position) {
      map.setView(position, 16);
    }

    // Initialize Geoman with polygon drawing only
    try {
      map.pm.addControls({
        position: 'topleft',
        drawCircle: false,
        drawMarker: false,
        drawCircleMarker: false,
        drawPolyline: false,
        drawPolygon: true,  // Only polygon drawing
        drawText: false,
        cutPolygon: false,
        rotateMode: true,
        dragMode: true,
        editMode: true,
        removalMode: false,
        drawRectangle: false,
      });

      map.pm.setGlobalOptions({
        allowSelfIntersection: false,
      });

      // When user draws a polygon
      const handleDrawCreate = (e) => {
        const { layer } = e;
        if (layer && layer.getLatLngs) {
          const latlngs = layer.getLatLngs()[0] || [];
          const area = calculateAreaHectares(latlngs);
          const geojson = layer.toGeoJSON();

          // Store reference to enable editing
          drawLayerRef.current = layer;
          onPolygonChange(geojson.geometry, area, latlngs);

          console.log('✅ Polygon drawn:', {
            corners: latlngs.length,
            area: area.toFixed(2),
            coordinates: latlngs.map(p => `[${p.lat.toFixed(4)},${p.lng.toFixed(4)}]`).join(' ')
          });
        }
      };

      // When user edits/drags/rotates
      const handleDrawUpdate = (e) => {
        const layer = e.layer || drawLayerRef.current;
        if (layer && layer.getLatLngs) {
          const latlngs = layer.getLatLngs()[0] || [];
          const area = calculateAreaHectares(latlngs);
          const geojson = layer.toGeoJSON();
          onPolygonChange(geojson.geometry, area, latlngs);

          console.log('📍 Polygon updated:', {
            area: area.toFixed(2),
            corners: latlngs.length
          });
        }
      };

      map.on('pm:create', handleDrawCreate);
      map.on('pm:edit', handleDrawUpdate);
      map.on('pm:drag', handleDrawUpdate);
      map.on('pm:dragend', handleDrawUpdate);
      map.on('pm:rotateend', handleDrawUpdate);

      return () => {
        map.off('pm:create', handleDrawCreate);
        map.off('pm:edit', handleDrawUpdate);
        map.off('pm:drag', handleDrawUpdate);
        map.off('pm:dragend', handleDrawUpdate);
        map.off('pm:rotateend', handleDrawUpdate);
      };
    } catch (err) {
      console.error('Geoman setup error:', err);
    }
  }, [map, position, onPolygonChange]);

  return null;
};

const SimpleMapView = () => {
  const navigate = useNavigate();
  const [position, setPosition] = useState([28.6139, 77.2090]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [token, setToken] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [area, setArea] = useState(0);
  const [polygon, setPolygon] = useState(null);
  const [coordinates, setCoordinates] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const editTimeoutRef = useRef(null);

  // Load session token and position from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    const urlPhone = params.get('phone');

    if (urlToken) {
      setToken(urlToken);
      setIsLoading(true);
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

      fetch(`${apiBaseUrl}/sessions/${urlToken}`)
        .then(res => res.json())
        .then(data => {
          if (data.lat && data.lon) {
            setPosition([data.lat, data.lon]);
            console.log('📍 Loaded position from token:', data);
          }
          if (data.phone) {
            setPhoneNumber(data.phone);
          }
        })
        .catch(err => console.error('Session lookup failed:', err))
        .finally(() => setIsLoading(false));
    } else if (urlPhone) {
      setPhoneNumber(urlPhone);
    }
  }, []);

  const handlePolygonChange = (geojson, areaValue, latlngs) => {
    setPolygon(geojson);
    setArea(areaValue);
    setCoordinates(latlngs);
    setIsEditing(true);

    if (editTimeoutRef.current) clearTimeout(editTimeoutRef.current);
    editTimeoutRef.current = setTimeout(() => {
      setIsEditing(false);
    }, 1000);
  };

  const handleConfirm = async () => {
    if (!polygon) {
      alert("Draw your farm boundary on the map by tapping the polygon icon (top-left).");
      return;
    }

    const areaNum = Number(area);
    if (!Number.isFinite(areaNum) || areaNum <= 0.01) {
      alert("Your farm area is too small (less than 0.01 hectares). Draw a larger area.");
      return;
    }

    setIsSaving(true);
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

    try {
      const payload = {
        polygon: polygon,
        area_hectares: areaNum,
      };

      if (token) payload.token = token;
      else payload.phone_number = phoneNumber;

      const response = await fetch(`${apiBaseUrl}/plots/save-with-phone`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setShowSuccess(true);
      } else {
        let errMsg = `Failed to save boundary (HTTP ${response.status})`;
        try {
          const errData = await response.json();
          const d = errData.detail;
          if (typeof d === 'string') {
            errMsg = d;
          } else if (Array.isArray(d)) {
            errMsg = d.map(x => x.msg || JSON.stringify(x)).join('; ');
          } else if (d) {
            errMsg = JSON.stringify(d);
          }
        } catch (_) { /* keep default */ }
        console.error("Save error response:", errMsg);
        alert(`Error: ${errMsg}`);
      }
    } catch (err) {
      console.error("Save failed:", err);
      alert("Network error. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full bg-[#f8f9fa] items-center justify-center space-y-4">
        <Loader2 className="animate-spin text-green-700" size={40} />
        <p className="text-gray-500 font-medium">Locating your farm...</p>
      </div>
    );
  }

  return (
    <div className="relative h-[100dvh] w-full flex flex-col overflow-hidden bg-black text-white">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-[1000] p-4 pointer-events-none">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="p-3 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 pointer-events-auto active:scale-90 transition-transform"
          >
            <ChevronLeft size={24} />
          </button>

          <div className="bg-green-600/90 backdrop-blur-md px-4 py-2 rounded-2xl border border-green-400/30 flex items-center space-x-2 pointer-events-auto">
            <span className="text-xs font-black uppercase tracking-widest leading-none">Draw Your Farm</span>
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
          </div>
        </div>
      </div>

      {/* Area & Coordinates Display */}
      {area > 0 && (
        <div className="absolute top-20 left-4 right-4 z-[1000] pointer-events-none">
          <motion.div
            initial={{ y: -20, opacity: 0, scale: 0.9 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            className="bg-white/95 backdrop-blur-sm text-gray-900 px-6 py-4 rounded-3xl shadow-2xl border-2 flex flex-col items-center gap-2"
            style={{ borderColor: isEditing ? '#fbbf24' : '#22c55e' }}
          >
            <span className="text-[10px] font-black uppercase tracking-widest text-gray-600">
              {isEditing ? '✏️ Editing...' : '✅ Ready to Save'}
            </span>
            <div className="flex items-baseline space-x-1">
              <span className="text-3xl font-black">{area.toFixed(2)}</span>
              <span className="text-sm font-bold text-gray-400">Hectares</span>
            </div>
            {coordinates.length > 0 && (
              <div className="text-xs text-gray-500 text-center mt-1 max-w-xs">
                <div className="font-bold text-gray-700 mb-0.5">Coordinates ({coordinates.length} corners):</div>
                {coordinates.map((c, i) => (
                  <div key={i}>{i + 1}. {c.lat.toFixed(5)}, {c.lng.toFixed(5)}</div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      )}

      {/* Map */}
      <div className="flex-1 w-full relative min-h-[300px]">
        <MapContainer
          center={position}
          zoom={16}
          style={{ height: '100%', width: '100%', position: 'absolute' }}
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          />
          <MapManager position={position} onPolygonChange={handlePolygonChange} />
        </MapContainer>
      </div>

      {/* Bottom Action Tray */}
      <div className="bg-zinc-950 p-6 pb-12 rounded-t-[40px] border-t border-zinc-800 z-[1000] shadow-[0_-20px_50px_rgba(0,0,0,0.5)]">
        <div className="w-12 h-1 bg-zinc-800 rounded-full mx-auto mb-6" />
        <h2 className="text-xl font-black mb-2">Draw Your Farm Boundary</h2>
        <p className="text-zinc-500 text-sm font-medium mb-8">
          Tap the polygon icon (top-left) to start drawing. Drag corners to adjust. Area calculates automatically.
        </p>

        <button
          disabled={isSaving || !polygon || area < 0.01}
          onClick={handleConfirm}
          className={`w-full py-6 rounded-3xl font-black text-lg flex items-center justify-center space-x-3 transition-all active:scale-95 shadow-xl ${
            polygon && area >= 0.01
              ? 'bg-green-600 border-b-4 border-green-800 text-white hover:bg-green-500'
              : 'bg-zinc-800 text-zinc-600 cursor-not-allowed border-b-4 border-zinc-900'
          }`}
        >
          {isSaving ? <Loader2 className="animate-spin" /> : (
            <>
              <span>Confirm Boundary</span>
              <CheckCircle2 size={20} />
            </>
          )}
        </button>
      </div>

      {/* Success Modal */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-[2000] bg-black/80 backdrop-blur-xl flex items-center justify-center p-8"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              className="bg-zinc-900 w-full max-w-sm rounded-[40px] p-8 border border-zinc-800 shadow-2xl text-center"
            >
              <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-green-500/20">
                <CheckCircle2 className="text-green-500" size={40} />
              </div>
              <h3 className="text-2xl font-black text-white mb-4">Boundary Saved!</h3>
              <p className="text-zinc-400 font-medium mb-8 leading-relaxed">
                Processing your satellite data. Check WhatsApp for your carbon estimate.
              </p>

              <button
                onClick={() => window.location.href = 'https://wa.me/your_number'}
                className="w-full py-5 bg-green-600 hover:bg-green-500 text-white rounded-3xl font-black text-lg flex items-center justify-center space-x-3 transition-colors border-b-4 border-green-800 active:scale-95"
              >
                <MessageSquare size={20} />
                <span>Open WhatsApp</span>
              </button>

              <button
                onClick={() => setShowSuccess(false)}
                className="mt-6 text-zinc-500 font-bold hover:text-white transition-colors"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SimpleMapView;
