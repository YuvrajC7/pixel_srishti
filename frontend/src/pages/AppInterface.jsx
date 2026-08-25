import React, { useState, useRef, useEffect } from 'react';
import { Send, UploadCloud, Map as MapIcon, MessageSquare, Loader, Image as ImageIcon, Layers, Activity, ChevronRight, ChevronLeft, Plus, Minus, Crosshair, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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

// Component to handle map events (hover, click) for Pin Mode
const MapEventsHandler = ({ isPinMode, setHoverCoord, handleMapClick }) => {
  const map = useMap();
  
  useMapEvents({
    mousemove(e) {
      if (isPinMode) {
        setHoverCoord([e.latlng.lat, e.latlng.lng]);
      }
    },
    click(e) {
      if (isPinMode) {
        handleMapClick([e.latlng.lat, e.latlng.lng]);
      }
    },
    mouseout() {
      if (isPinMode) setHoverCoord(null);
    }
  });
  
  // Also change cursor when in pin mode
  useEffect(() => {
    if (isPinMode) {
      map.getContainer().style.cursor = 'crosshair';
    } else {
      map.getContainer().style.cursor = '';
      setHoverCoord(null);
    }
  }, [isPinMode, map, setHoverCoord]);

  return null;
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

  const handleSend = async () => {
    if (!input.trim() && !fileT1 && !fileT2) return;

    const userMessage = { role: 'user', text: input, hasFile: !!fileT1 || !!fileT2 };
    setMessages(prev => [...prev, userMessage]);
    
    // Quick hack to detect if user typed coordinates
    const coordMatch = input.match(/(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)/);
    if (coordMatch) {
        setTargetCoord([parseFloat(coordMatch[1]), parseFloat(coordMatch[2])]);
    }

    const currentInput = input;
    const currentMode = mode;
    const currentT1 = fileT1;
    const currentT2 = fileT2;
    
    setInput('');
    setLoading(true);

    try {
      let endpoint = '';
      let replyText = '';
      let meta = null;
      const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

      if (currentMode === 'BI_TEMPORAL') {
          if (!currentT1 || !currentT2) {
              setMessages(prev => [...prev, { role: 'assistant', text: 'Error: Both Image T1 (Past) and Image T2 (Current) are required for Bi-Temporal Change Detection.' }]);
              setLoading(false);
              return;
          }
          endpoint = '/api/detect_change';
          const formData = new FormData();
          formData.append('image1', currentT1);
          formData.append('image2', currentT2);
          const res = await fetch(baseUrl + endpoint, { method: 'POST', body: formData });
          if (!res.ok) { const errData = await res.json().catch(() => ({})); throw new Error(errData.detail || 'Network response was not ok'); }
          const data = await res.json();
          replyText = `[Change Detection Specialist]:\n${data.result}`;
      } 
      else if (currentMode === 'SINGLE_IMAGE') {
          if (!currentT1) {
              setMessages(prev => [...prev, { role: 'assistant', text: 'Error: An image is required for Single Image mode.' }]);
              setLoading(false);
              return;
          }
          if (currentInput.toLowerCase().includes('segment')) {
              endpoint = '/api/segment';
              const formData = new FormData();
              formData.append('image', currentT1);
              const res = await fetch(baseUrl + endpoint, { method: 'POST', body: formData });
              if (!res.ok) { const errData = await res.json().catch(() => ({})); throw new Error(errData.detail || 'Network response was not ok'); }
              const data = await res.json();
              replyText = `[Segmentation Specialist]:\n${data.description}`;
              meta = { mask_path: data.mask_path };
          } else {
              endpoint = '/api/ask_question';
              const formData = new FormData();
              formData.append('image', currentT1);
              formData.append('question', currentInput || 'Describe this image in detail.');
              const res = await fetch(baseUrl + endpoint, { method: 'POST', body: formData });
              if (!res.ok) { const errData = await res.json().catch(() => ({})); throw new Error(errData.detail || 'Network response was not ok'); }
              const data = await res.json();
              replyText = `[VQA Specialist]:\n${data.answer}`;
          }
      }
      else {
          replyText = `[Agentic Orchestrator]: Received query: '${currentInput}'. Mode ${currentMode} is currently pending integration with the ML backend.`;
      }

      setMessages(prev => [...prev, { role: 'assistant', text: replyText, metadata: meta }]);
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
        
        {/* HERO SATELLITE MAP */}
        <div className="absolute inset-0 z-0">
           <MapContainer center={[20.5937, 78.9629]} zoom={5} className="h-full w-full" zoomControl={false}>
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attribution="&copy; Esri"
              />
              <MapController center={targetCoord} />
              <MapEventsHandler isPinMode={isPinMode} setHoverCoord={setHoverCoord} handleMapClick={handleMapClick} />
              <ZoomControls setMapInstance={setMapInstance} />
              
              {targetCoord && (
                <Marker position={targetCoord}>
                  <Popup className="text-black font-sans font-medium">Target Sector Acquired.</Popup>
                </Marker>
              )}
           </MapContainer>
        </div>
        
        {/* MAP TOOLS FLOATING WIDGET (Bottom Right when chat is open, or dynamic) */}
        <div className={`absolute bottom-6 z-10 flex flex-col gap-3 transition-all duration-500 ease-in-out ${chatOpen ? 'right-[474px]' : 'right-6'}`}>
           {/* Coordinates Hover Display */}
           <div className={`bg-[#02040A]/80 backdrop-blur-md border border-white/10 text-white text-xs px-3 py-2 rounded-lg font-mono tracking-widest shadow-lg transition-opacity duration-200 absolute right-[60px] top-1/2 -translate-y-1/2 whitespace-nowrap ${isPinMode && hoverCoord ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
              {hoverCoord ? `${hoverCoord[0].toFixed(5)}, ${hoverCoord[1].toFixed(5)}` : '0.00000, 0.00000'}
           </div>

           {targetCoord && (
             <button 
               onClick={() => setTargetCoord(null)}
               className="w-12 h-12 rounded-full flex items-center justify-center shadow-lg border backdrop-blur-md bg-red-600/80 border-red-500 text-white hover:bg-red-500 transition-all shadow-[0_0_20px_rgba(220,38,38,0.3)]"
               title="Clear Pin"
             >
               <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
             </button>
           )}

           <button 
             onClick={() => setIsPinMode(!isPinMode)}
             className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg border backdrop-blur-md transition-all ${isPinMode ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)]' : 'bg-[#02040A]/80 border-white/10 text-slate-300 hover:bg-white/10'}`}
             title="Pin Location"
           >
             <Crosshair size={20} />
           </button>
           
           <div className="flex flex-col bg-[#02040A]/80 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden shadow-lg">
             <button 
               onClick={() => mapInstance?.zoomIn()}
               className="w-12 h-12 flex items-center justify-center text-slate-300 hover:bg-white/10 hover:text-white transition-colors border-b border-white/10"
               title="Zoom In"
             >
               <Plus size={20} />
             </button>
             <button 
               onClick={() => mapInstance?.zoomOut()}
               className="w-12 h-12 flex items-center justify-center text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
               title="Zoom Out"
             >
               <Minus size={20} />
             </button>
           </div>
        </div>

        {/* FLOATING CONFIGURATION WIDGET (Top Right Hover Icon) */}
        <div className={`absolute top-6 z-10 transition-all duration-500 ease-in-out group ${chatOpen ? 'right-[500px]' : 'right-16'}`}>
           
           {/* The Icon Trigger */}
           <div className="w-12 h-12 bg-[#02040A]/80 backdrop-blur-xl border border-white/10 rounded-xl flex items-center justify-center text-blue-400 shadow-2xl cursor-pointer hover:bg-white/10 transition-all">
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
          className={`absolute top-6 z-30 bg-[#02040A] hover:bg-white/10 text-slate-300 border border-white/10 p-2.5 rounded-l-xl shadow-2xl backdrop-blur-md transition-all duration-500 ease-in-out flex items-center justify-center ${chatOpen ? 'right-[450px]' : 'right-0'}`}
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
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                />
              </div>
              <button 
                onClick={handleSend}
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
