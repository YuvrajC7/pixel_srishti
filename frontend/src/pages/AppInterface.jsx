import React, { useState, useRef, useEffect } from 'react';
import { Send, UploadCloud, Map as MapIcon, MessageSquare, Loader, Image as ImageIcon, Layers, Activity, ChevronRight, ChevronLeft, Plus, Minus, Crosshair, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const GeomanInit = ({ setInput }) => {
  const map = useMap();
  useEffect(() => {
    map.pm.addControls({
      position: 'topleft',
      drawCircleMarker: false,
      drawText: false,
      cutPolygon: false,
    });
    map.pm.setLang('en');
    
    // Disable continuous drawing globally so the user has to re-click the tool
    map.pm.setGlobalOptions({ continueDrawing: false });
    
    // Listen for drawn items (like markers)
    map.on('pm:create', (e) => {
      if (e.shape === 'Marker') {
        const coord = e.layer.getLatLng();
        const lat = coord.lat.toFixed(5);
        const lng = coord.lng.toFixed(5);
        
        // Append to chat input
        setInput(prev => prev + (prev.trim() ? ' ' : '') + `${lat}, ${lng}`);
        
        // Force disable drawing mode immediately after one click
        map.pm.disableDraw();
        
        // Zoom in to the marker with a slight delay to ensure Geoman finishes processing the click
        setTimeout(() => {
          map.flyTo([coord.lat, coord.lng], Math.max(map.getZoom(), 14), { duration: 1.5 });
        }, 50);
      }
    });
    
    return () => {
      map.off('pm:create');
    };
  }, [map, setInput]);
  return null;
};

// Component to dynamically fly to coordinates if user provides them
const MapController = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, map.getZoom() > 10 ? map.getZoom() : 13, { duration: 1.5 });
    }
  }, [center, map]);
  return null;
};

const CoordinateTracker = () => {
  const [hoverCoord, setHoverCoord] = useState(null);
  useMapEvents({
    mousemove(e) { setHoverCoord([e.latlng.lat, e.latlng.lng]); },
    mouseout() { setHoverCoord(null); }
  });
  return (
    <div className={`bg-[#02040A]/80 backdrop-blur-md border border-white/10 text-white text-xs px-3 py-2 rounded-lg font-mono tracking-widest shadow-lg transition-opacity duration-200 absolute right-[60px] top-1/2 -translate-y-1/2 whitespace-nowrap ${hoverCoord ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
      {hoverCoord ? `${hoverCoord[0].toFixed(5)}, ${hoverCoord[1].toFixed(5)}` : '0.00000, 0.00000'}
    </div>
  );
};

// Component to expose zoom controls
const ZoomControls = ({ setMapInstance }) => {
  const map = useMap();
  useEffect(() => {
    setMapInstance(map);
  }, [map, setMapInstance]);
  return null;
};


export default function AppInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Welcome to PIXEL Srishti Orbital Interface.\nSelect your analysis mode and upload geospatial telemetry.' }
  ]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const startVoiceSearch = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Voice search is not supported in this browser. Try Chrome.");
      return;
    }
    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-IN'; 
    
    recognition.onstart = () => setIsRecording(true);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const finalInput = input + (input ? ' ' : '') + transcript;
      setInput(finalInput);
      
      // Auto-send when voice is finished
      handleSend(finalInput);
    };
    recognition.onerror = (e) => console.error("Speech recognition error", e);
    recognition.onend = () => setIsRecording(false);
    
    recognition.start();
  };
  
  const [mode, setMode] = useState('SINGLE_IMAGE');
  const [fileT1, setFileT1] = useState(null);
  const [fileT2, setFileT2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [targetCoord, setTargetCoord] = useState(null);
  
  // New State for Map Tools
  const [mapInstance, setMapInstance] = useState(null);
  const [isPinMode, setIsPinMode] = useState(false);
  const [hoverCoord, setHoverCoord] = useState(null);
  
  const messagesEndRef = useRef(null);
  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); };
  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  const INDIAN_LOCATIONS = {
    "andhra pradesh": [15.9129, 79.7400, 7, "State"], "arunachal pradesh": [28.2180, 94.7278, 7, "State"], "assam": [26.2006, 92.9376, 7, "State"], "bihar": [25.0961, 85.3131, 7, "State"],
    "chhattisgarh": [21.2787, 81.8661, 7, "State"], "goa": [15.2993, 74.1240, 8, "State"], "gujarat": [22.2587, 71.1924, 7, "State"], "haryana": [29.0588, 76.0856, 7, "State"],
    "himachal pradesh": [31.1048, 77.1665, 7, "State"], "jharkhand": [23.6102, 85.2799, 7, "State"], "karnataka": [15.3173, 75.7139, 7, "State"], "kerala": [10.8505, 76.2711, 7, "State"],
    "madhya pradesh": [22.9734, 78.6569, 7, "State"], "maharashtra": [19.7515, 75.7139, 7, "State"], "manipur": [24.6637, 93.9063, 7, "State"], "meghalaya": [25.4670, 91.3662, 7, "State"],
    "mizoram": [23.1645, 92.9376, 7, "State"], "nagaland": [26.1584, 94.5624, 7, "State"], "odisha": [20.9517, 85.0985, 7, "State"], "punjab": [31.1471, 75.3412, 7, "State"],
    "rajasthan": [27.0238, 74.2179, 7, "State"], "sikkim": [27.5330, 88.5122, 7, "State"], "tamil nadu": [11.1271, 78.6569, 7, "State"], "telangana": [18.1124, 79.0193, 7, "State"],
    "tripura": [23.9408, 91.9882, 7, "State"], "uttar pradesh": [26.8467, 80.9462, 7, "State"], "uttarakhand": [30.0668, 79.0193, 7, "State"], "west bengal": [22.9868, 87.8550, 7, "State"],
    "jammu and kashmir": [33.7782, 76.5762, 7, "Territory"], "ladakh": [34.1526, 77.5771, 7, "Territory"],
    "delhi": [28.7041, 77.1025, 11, "Megacity"], "mumbai": [19.0760, 72.8777, 12, "Megacity"], "bangalore": [12.9716, 77.5946, 12, "Megacity"], 
    "chennai": [13.0827, 80.2707, 12, "Megacity"], "kolkata": [22.5726, 88.3639, 12, "Megacity"], "hyderabad": [17.3850, 78.4867, 12, "Megacity"],
    "pune": [18.5204, 73.8567, 12, "City"], "ahmedabad": [23.0225, 72.5714, 12, "City"], "surat": [21.1702, 72.8311, 12, "City"], 
    "jaipur": [26.9124, 75.7873, 12, "City"], "kanpur": [26.4499, 80.3319, 12, "City"], "lucknow": [26.8467, 80.9462, 12, "City"], 
    "nagpur": [21.1458, 79.0882, 12, "City"], "indore": [22.7196, 75.8577, 12, "City"], "patna": [25.5941, 85.1376, 12, "City"], 
    "bhopal": [23.2599, 77.4126, 12, "City"], "thane": [19.2183, 72.9781, 12, "City"], "agra": [27.1767, 78.0081, 12, "City"], 
    "vadodara": [22.3072, 73.1812, 12, "City"], "ghaziabad": [28.6692, 77.4538, 12, "City"], "ludhiana": [30.9010, 75.8573, 12, "City"]
  };

  const levenshtein = (a, b) => {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    const matrix = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) == a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1));
        }
      }
    }
    return matrix[b.length][a.length];
  };

  const handleSend = async (overrideInput = null) => {
    const textToProcess = (typeof overrideInput === 'string' ? overrideInput : input);
    if (!textToProcess.trim() && !fileT1 && !fileT2) return;

    const userMessage = { role: 'user', text: textToProcess, hasFile: !!fileT1 || !!fileT2 };
    
    let automatedResponse = null;
    const lowerText = textToProcess.toLowerCase();
    
    // Quick hack to detect if user typed coordinates
    const coordMatch = textToProcess.match(/(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)/);
    if (coordMatch) {
      if (mapInstance) mapInstance.flyTo([parseFloat(coordMatch[1]), parseFloat(coordMatch[2])], 14, { duration: 1.5 });
      automatedResponse = { role: 'assistant', text: `[System]: Navigational coordinates confirmed. Targeting sector [${coordMatch[1]}, ${coordMatch[2]}].` };
    } else {
      // 1. Efficient Local Interceptor with Fuzzy Matching
      let foundLocal = false;
      const cleanText = lowerText.replace(/(show me|go to|zoom to|find|locate|take me to|navigate to|in|at)\b/g, '').trim();
      const words = cleanText.split(/\s+/);
      
      for (const [location, dataArr] of Object.entries(INDIAN_LOCATIONS)) {
        const locWords = location.split(/\s+/);
        let isMatch = false;
        let isFuzzy = false;
        
        // Exact Substring Match
        if (cleanText === location || cleanText.startsWith(location + " ") || cleanText.endsWith(" " + location) || cleanText.includes(" " + location + " ")) {
          isMatch = true;
        } else {
          // Fuzzy Match (Levenshtein Distance)
          for (let i = 0; i <= words.length - locWords.length; i++) {
            const ngram = words.slice(i, i + locWords.length).join(" ");
            const maxTypos = location.length > 8 ? 2 : 1; 
            if (levenshtein(ngram, location) <= maxTypos) {
              isMatch = true;
              isFuzzy = true;
              break;
            }
          }
        }

        // Specificity Check: If the user typed a long specific query (e.g. "Manipal University Jaipur"),
        // DO NOT hijack it with the local city interceptor just because it contains the word "Jaipur".
        // Let it fall through to Nominatim so the dynamic API can locate the exact building/POI!
        if (isMatch && cleanText.length > location.length + 8) {
            isMatch = false; 
        }

        if (isMatch) {
          const lat = dataArr[0];
          const lon = dataArr[1];
          const zoomLvl = dataArr[2];
          const locType = dataArr[3];
          
          if (mapInstance) mapInstance.flyTo([lat, lon], zoomLvl, { duration: 2.0 });
          const formattedLoc = location.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          const matchLabel = isFuzzy ? " (Fuzzy Match)" : "";
          automatedResponse = { role: 'assistant', text: `[System]: ${locType} entity identified${matchLabel}. Navigating map to ${formattedLoc} at coordinates [${lat.toFixed(4)}, ${lon.toFixed(4)}].` };
          foundLocal = true;
          break; // Stop after first match
        }
      }

      // 2. Dynamic Fallback Interceptor for any Indian City
      if (!foundLocal && textToProcess.length < 50) {
        try {
          const nomRes = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(textToProcess)}&format=json&limit=1&countrycodes=in`);
          const nomData = await nomRes.json();
          if (nomData && nomData.length > 0) {
            const place = nomData[0];
            const lat = parseFloat(place.lat);
            const lon = parseFloat(place.lon);
            
            let zoomLvl = 12;
            
            if (place.class === 'amenity' || place.class === 'building') zoomLvl = 15;
            
            if (mapInstance) mapInstance.flyTo([lat, lon], zoomLvl, { duration: 2.0 });
            
            const placeName = place.name || place.display_name.split(',')[0];
            automatedResponse = { role: 'assistant', text: `[System]: City/Local entity identified. Navigating map to ${placeName} at coordinates [${lat.toFixed(4)}, ${lon.toFixed(4)}].` };
          }
        } catch (e) {
          console.error("Dynamic Geocoding failed", e);
        }
      }
    }

    setMessages(prev => {
      const newMsgs = [...prev, userMessage];
      if (automatedResponse) newMsgs.push(automatedResponse);
      return newMsgs;
    });

    // Short-circuit: If the user just gave a location/navigation command and hasn't uploaded images,
    // skip hitting the ML backend to prevent the "No images provided" error.
    if (automatedResponse && !fileT1 && !fileT2) {
      setInput('');
      return;
    }

    const currentMode = mode;
    const currentT1 = fileT1;
    const currentT2 = fileT2;
    
    setInput('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('query', textToProcess || 'Execute analysis');
      
      if (currentT1) formData.append('images', currentT1);
      if (currentT2) formData.append('images', currentT2);

      const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const res = await fetch(baseUrl + '/api/chat', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let errMsg = errData.detail || 'Network response was not ok';
        if (typeof errMsg === 'object') {
          errMsg = JSON.stringify(errMsg);
        }
        throw new Error(errMsg);
      }
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'assistant', text: data.agent_response || data.reply || data.answer, metadata: data.metadata }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'assistant', text: 'API Error: ' + error.message }]);
    } finally {
      setLoading(false);
    }
  };
  
  const handleMapClick = (coord) => {
    setTargetCoord(coord);
    setIsPinMode(false);
    setInput(prev => prev + (prev.trim() ? ' ' : '') + `${coord[0].toFixed(6)}, ${coord[1].toFixed(6)}`);
    if (!chatOpen) setChatOpen(true);
  };

  const getPreviewName = (file) => file ? (file.name.length > 15 ? file.name.substring(0, 15) + '...' : file.name) : 'No file';

  return (
    <div className="h-screen w-full bg-[#030712] text-slate-100 flex flex-col font-sans overflow-hidden selection:bg-blue-500/30">
      
      <header className="h-14 border-b border-white/10 bg-[#02040A] flex items-center justify-between px-6 shrink-0 z-50 shadow-md">
        <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity py-1">
          <div className="w-8 h-8 rounded-lg overflow-hidden bg-black border border-white/20 shadow-lg shrink-0">
            <img src="/logo.jpg?v=3" alt="PIXEL Srishti" className="w-full h-full object-cover" />
          </div>
          <span className="text-lg tracking-widest mt-1" style={{ fontFamily: '"Silkscreen", cursive' }}>
            <span className="text-white">PIXEL</span> <span className="text-blue-400">SRISHTI</span>
          </span>
        </Link>
        <div className="flex items-center gap-4 text-xs font-medium text-slate-400 bg-white/5 px-4 py-1.5 rounded-full border border-white/10">
          <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div> Router Online</span>
        </div>
      </header>

      <div className="flex-1 relative flex overflow-hidden">
        
                                            <style>{`
          /* Dark mode for Leaflet and Geoman Toolbars */
          .leaflet-bar { border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5) !important; }
          .leaflet-bar a { background-color: rgba(2,4,10,0.85) !important; color: #60a5fa !important; border-bottom: 1px solid rgba(255,255,255,0.05) !important; backdrop-filter: blur(12px); width: 36px !important; height: 36px !important; line-height: 36px !important; }
          .leaflet-bar a:hover { background-color: rgba(255,255,255,0.1) !important; color: #93c5fd !important; }
          
          /* CRITICAL FIX: Convert #5B5B5B grey icons to pure black first, then apply the precise color matrix for #60a5fa (blue-400) */
          .leaflet-pm-icon, .control-icon, .leaflet-control-layers-toggle { 
            filter: brightness(0) saturate(100%) invert(59%) sepia(85%) saturate(3015%) hue-rotate(193deg) brightness(101%) contrast(97%) !important; 
          }
          
          .leaflet-control-layers { background-color: rgba(2,4,10,0.85) !important; color: #cbd5e1 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; backdrop-filter: blur(12px); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5) !important; }
          .leaflet-control-layers-expanded { padding: 10px !important; background-color: rgba(2,4,10,0.95) !important; }
        `}</style>
        {/* HERO SATELLITE MAP */}
        <div className="absolute inset-0 z-0">
           <MapContainer center={[20.5937, 78.9629]} zoom={5} maxZoom={17} className="h-full w-full" zoomControl={false}>
                            <LayersControl position="bottomleft">
                <LayersControl.BaseLayer checked name="Satellite (Esri Imagery)">
                  <TileLayer
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    attribution="&copy; Esri"
                  />
                </LayersControl.BaseLayer>
                <LayersControl.BaseLayer name="Terrain (Bhuvan Style)">
                  <TileLayer
                    url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                    attribution="Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)"
                  />
                </LayersControl.BaseLayer>
                <LayersControl.BaseLayer name="Streets (OpenStreetMap)">
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution="&copy; OpenStreetMap contributors"
                  />
                </LayersControl.BaseLayer>
              </LayersControl>
              <GeomanInit setInput={setInput} />
              <MapController center={targetCoord} />
              
              <CoordinateTracker />
              <ZoomControls setMapInstance={setMapInstance} />
              
              
           </MapContainer>
        </div>
        
        {/* MAP TOOLS FLOATING WIDGET (Bottom Right when chat is open, or dynamic) */}
        <div className={`absolute bottom-6 z-10 flex flex-col gap-3 transition-all duration-500 ease-in-out ${chatOpen ? 'right-[474px]' : 'right-6'}`}>
           

           

           
           
           <div className="flex flex-col bg-[#02040A]/80 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden shadow-lg">
             <button 
               onClick={() => mapInstance?.zoomIn()}
               className="w-12 h-12 flex items-center justify-center text-blue-400 hover:bg-blue-400/20 hover:text-blue-300 transition-colors border-b border-white/10"
               title="Zoom In"
             >
               <Plus size={20} />
             </button>
             <button 
               onClick={() => mapInstance?.zoomOut()}
               className="w-12 h-12 flex items-center justify-center text-blue-400 hover:bg-blue-400/20 hover:text-blue-300 transition-colors"
             >
               <Minus size={20} />
             </button>
           </div>
        </div>

        {/* FLOATING CONFIGURATION WIDGET (Top Right Hover Icon) */}
        <div className={`absolute top-6 z-10 transition-all duration-500 ease-in-out group ${chatOpen ? 'right-[500px]' : 'right-16'}`}>
           
           {/* The Icon Trigger */}
           <div className="w-12 h-12 bg-[#02040A]/80 backdrop-blur-xl border border-white/10 rounded-xl flex items-center justify-center text-blue-400 shadow-2xl cursor-pointer hover:bg-blue-400/20 transition-all">
             <MapIcon size={22} />
           </div>

           {/* The Revealable Panel */}
           <div className="absolute top-0 right-0 w-[380px] bg-[#02040A]/95 backdrop-blur-2xl border border-white/10 rounded-3xl p-5 shadow-[0_20px_50px_rgba(0,0,0,0.7)] opacity-0 scale-95 origin-top-right pointer-events-none group-hover:opacity-100 group-hover:scale-100 group-hover:pointer-events-auto transition-all duration-300">
             <div className="flex items-center gap-3 mb-5">
                <MapIcon className="text-blue-400" size={18} />
                <h2 className="font-semibold text-sm tracking-wide text-white">Geospatial Configuration</h2>
             </div>
             
             <h3 className="text-[10px] font-semibold text-slate-400 mb-3 uppercase tracking-widest">Analysis Mode</h3>
             <div className="flex gap-2 mb-5">
                <button 
                  onClick={() => { setMode('SINGLE_IMAGE'); setFileT2(null); }}
                  className={`flex-1 flex flex-col items-center gap-1.5 p-2 rounded-xl border transition-all ${mode === 'SINGLE_IMAGE' ? 'bg-blue-500/20 border-blue-500 text-white' : 'bg-transparent border-white/10 text-slate-400 hover:bg-white/5'}`}
                >
                  <ImageIcon size={16} />
                  <span className="text-[10px] font-medium uppercase tracking-wide">Single</span>
                </button>
                <button 
                  onClick={() => setMode('CROSS_MODAL')}
                  className={`flex-1 flex flex-col items-center gap-1.5 p-2 rounded-xl border transition-all ${mode === 'CROSS_MODAL' ? 'bg-blue-500/20 border-blue-500 text-white' : 'bg-transparent border-white/10 text-slate-400 hover:bg-white/5'}`}
                >
                  <Layers size={16} />
                  <span className="text-[10px] font-medium uppercase tracking-wide">Fusion</span>
                </button>
                <button 
                  onClick={() => setMode('BI_TEMPORAL')}
                  className={`flex-1 flex flex-col items-center gap-1.5 p-2 rounded-xl border transition-all ${mode === 'BI_TEMPORAL' ? 'bg-blue-500/20 border-blue-500 text-white' : 'bg-transparent border-white/10 text-slate-400 hover:bg-white/5'}`}
                >
                  <Activity size={16} />
                  <span className="text-[10px] font-medium uppercase tracking-wide">Temporal</span>
                </button>
             </div>

             <div className="flex gap-3">
                <div className="flex-1">
                   <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5 block">{mode === 'CROSS_MODAL' ? 'Optical (RGB)' : 'Time T1 (Past)'}</label>
                   <label className="flex flex-col items-center justify-center py-4 border border-dashed border-white/20 rounded-xl hover:bg-white/5 hover:border-blue-500/50 cursor-pointer transition-colors bg-black/20">
                     <UploadCloud size={18} className="text-blue-400 mb-1" />
                     <span className="text-[10px] font-medium text-slate-300">{fileT1 ? getPreviewName(fileT1) : 'GeoTIFF'}</span>
                     <input type="file" className="hidden" accept=".tif,.tiff,.png,.jpg" onChange={(e) => setFileT1(e.target.files[0])} />
                   </label>
                </div>
                {(mode === 'BI_TEMPORAL' || mode === 'CROSS_MODAL') && (
                  <div className="flex-1">
                     <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5 block">{mode === 'CROSS_MODAL' ? 'SAR (Radar)' : 'Time T2 (Curr)'}</label>
                     <label className="flex flex-col items-center justify-center py-4 border border-dashed border-white/20 rounded-xl hover:bg-white/5 hover:border-blue-500/50 cursor-pointer transition-colors bg-black/20">
                       <UploadCloud size={18} className="text-blue-400 mb-1" />
                       <span className="text-[10px] font-medium text-slate-300">{fileT2 ? getPreviewName(fileT2) : 'GeoTIFF'}</span>
                       <input type="file" className="hidden" accept=".tif,.tiff,.png,.jpg" onChange={(e) => setFileT2(e.target.files[0])} />
                     </label>
                  </div>
                )}
             </div>
           </div>
        </div>

        {/* CHAT TOGGLE BUTTON */}
        <button 
          onClick={() => setChatOpen(!chatOpen)}
          className={`absolute top-6 z-30 bg-[#02040A] hover:bg-white/10 text-blue-400 border border-blue-400/30 p-2.5 rounded-l-xl hover:text-blue-400 shadow-2xl backdrop-blur-md transition-all duration-500 ease-in-out flex items-center justify-center ${chatOpen ? 'right-[450px]' : 'right-0'}`}
        >
          {chatOpen ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>

        {/* CHAT PANEL DRAWER */}
        <div 
          className={`absolute top-0 right-0 h-full bg-[#030712]/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl transition-transform duration-500 ease-in-out flex flex-col z-20 w-[450px] ${chatOpen ? 'translate-x-0' : 'translate-x-full'}`}
        >
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-5 ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white shadow-[0_0_20px_rgba(37,99,235,0.2)]' 
                    : 'bg-white/5 border border-white/10 text-slate-200 shadow-lg'
                }`}>
                  {msg.hasFile && (
                    <div className="flex items-center gap-2 mb-2 text-xs font-medium text-blue-200 bg-black/20 px-2 py-1 rounded-md inline-flex">
                      <ImageIcon size={14} /> Telemetry Attached
                    </div>
                  )}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                  
                  {msg.metadata && Object.keys(msg.metadata).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2">Analysis Data</p>
                      <pre className="text-xs text-blue-300 font-mono bg-black/40 p-3 rounded-lg overflow-x-auto">
                        {JSON.stringify(msg.metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white/5 border border-white/10 text-slate-200 rounded-2xl p-5 flex items-center gap-3">
                  <Loader className="animate-spin text-blue-400" size={16} />
                  <span className="text-sm">Agentic Router assigning task...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-5 bg-black/40 border-t border-white/10">
            <div className="flex gap-3 items-end">
              <div className="flex-1 bg-[#02040A] border border-white/10 rounded-2xl p-1.5 pl-4 flex items-center gap-2 focus-within:border-blue-500/50 transition-colors shadow-inner">
                <textarea
                  className="flex-1 bg-transparent border-none outline-none text-sm text-slate-100 placeholder:text-slate-500 resize-none max-h-32 py-2.5"
                  rows="1"
                  placeholder="Type coordinates or ask query..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                />
              </div>
              
              <button 
                onClick={startVoiceSearch}
                className={`w-12 h-12 shrink-0 ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-white/10 hover:bg-white/20'} text-white rounded-xl flex items-center justify-center shadow-lg transition-all`}
                title="Voice Search (Bhuvan NLP)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
              </button>
              <button 
                onClick={() => handleSend()}
                disabled={loading || (!input.trim() && !fileT1 && !fileT2)}
                className="w-12 h-12 shrink-0 bg-blue-600 hover:bg-blue-500 disabled:bg-white/10 disabled:text-slate-500 text-white rounded-xl flex items-center justify-center shadow-lg transition-all"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}




















