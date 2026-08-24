import React, { useRef, useState, useEffect, useMemo } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Link } from 'react-router-dom';
import Globe from 'react-globe.gl';
import * as THREE from 'three';

// Generate pure CSS starfields (No external image dependencies)
const generateStars = (count, maxSize = 2000) => {
  let shadow = '';
  for (let i = 0; i < count; i++) {
    const x = Math.floor(Math.random() * maxSize);
    const y = Math.floor(Math.random() * maxSize);
    const alpha = (0.5 + Math.random() * 0.5).toFixed(2);
    shadow += `${x}px ${y}px rgba(255, 255, 255, ${alpha})${i === count - 1 ? '' : ', '}`;
  }
  return shadow;
};
const starsSmall = generateStars(800);
const starsMedium = generateStars(300);
const starsLarge = generateStars(100);

export default function LandingPage() {
  const globeEl = useRef();
  const [hoveredCountry, setHoveredCountry] = useState(null);
  
  const activeSats = useRef([]);
  const pointerPos = useRef({ x: 0, y: 0 });

  const { scrollYProgress } = useScroll();
  
  // Cinematic globe scaling
  const globeScale = useTransform(scrollYProgress, [0, 0.3], [1.4, 0.6]);
  const globeY = useTransform(scrollYProgress, [0, 0.3], ['0%', '-15%']);
  
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 0.15], ['0px', '-50px']);

  const section1Opacity = useTransform(scrollYProgress, [0.15, 0.35, 0.55], [0, 1, 0]);
  const section2Opacity = useTransform(scrollYProgress, [0.4, 0.6, 0.8], [0, 1, 0]);
  const section3Opacity = useTransform(scrollYProgress, [0.65, 0.85, 1], [0, 1, 1]);

  // Create Highly Realistic Modern Aerospace Satellite (Geometry & Materials Shared)
  const { baseSatMesh, allMaterials } = useMemo(() => {
    const group = new THREE.Group();

    const busMat = new THREE.MeshPhongMaterial({ 
      color: '#f8fafc', specular: '#ffffff', shininess: 20, transparent: true, opacity: 1 
    });
    const darkMetalMat = new THREE.MeshPhongMaterial({ 
      color: '#555555', specular: '#999999', shininess: 50, transparent: true, opacity: 1 
    });
    const panelMat = new THREE.MeshPhongMaterial({ 
      color: '#1d4ed8', specular: '#60a5fa', shininess: 150, side: THREE.DoubleSide, transparent: true, opacity: 1 
    });
    const gridMat = new THREE.MeshBasicMaterial({ 
      color: '#e2e8f0', wireframe: true, transparent: true, opacity: 0.6 
    });
    const dishMat = new THREE.MeshPhongMaterial({ 
      color: '#ffffff', specular: '#cccccc', shininess: 10, transparent: true, opacity: 1 
    });

    const bodyGeom = new THREE.BoxGeometry(2.5, 2.5, 6);
    const body = new THREE.Mesh(bodyGeom, busMat);
    group.add(body);

    const panelW = 14;
    const panelH = 0.1;
    const panelD = 4;
    
    const createWing = (xOffset) => {
      const wingGroup = new THREE.Group();
      const base = new THREE.Mesh(new THREE.BoxGeometry(panelW, panelH, panelD), panelMat);
      const grid = new THREE.Mesh(new THREE.BoxGeometry(panelW, panelH, panelD, 12, 1, 4), gridMat);
      wingGroup.add(base);
      wingGroup.add(grid);
      
      const truss = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 4, 8), darkMetalMat);
      truss.rotation.z = Math.PI / 2;
      truss.position.set(xOffset > 0 ? -panelW/2 - 2 : panelW/2 + 2, 0, 0);
      wingGroup.add(truss);
      wingGroup.position.set(xOffset, 0, 0);
      return wingGroup;
    };

    group.add(createWing(-10)); 
    group.add(createWing(10));  

    const dishGeom = new THREE.SphereGeometry(2.5, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2.5);
    const dish = new THREE.Mesh(dishGeom, dishMat);
    dish.rotation.x = -Math.PI / 2;
    dish.position.set(0, 0, 3.5); 
    group.add(dish);
    
    const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 3, 8), darkMetalMat);
    spire.rotation.x = Math.PI / 2;
    spire.position.set(0, 0, 4.5);
    group.add(spire);

    const sensor = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.2, 1.2), darkMetalMat);
    sensor.position.set(0, -1.2, 2);
    group.add(sensor);

    const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.5, 16), dishMat);
    lens.position.set(0, -1.8, 2);
    group.add(lens);

    const engine = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 0.5, 1.8, 16), darkMetalMat);
    engine.rotation.x = Math.PI / 2;
    engine.position.set(0, 0, -3.5);
    group.add(engine);

    group.scale.set(1.6, 1.6, 1.6);
    
    return { 
      baseSatMesh: group, 
      allMaterials: [busMat, darkMetalMat, panelMat, gridMat, dishMat] 
    };
  }, []);

  const spawnSatellite = (intersectPoint) => {
    if (!globeEl.current) return;
    
    const mesh = baseSatMesh.clone();
    
    // Calculate normal vector from origin to point
    const normal = intersectPoint.clone().normalize();
    
    // Place mesh exactly at the clicked spot on the orbit sphere
    mesh.position.copy(intersectPoint);
    mesh.lookAt(0, 0, 0); // Always face Earth
    
    // Pick a random orbital plane axis that is perpendicular to the normal!
    // This guarantees the satellite starts exactly here, and orbits through this point.
    const randomVec = new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize();
    const orbitAxis = new THREE.Vector3().crossVectors(normal, randomVec).normalize();
    
    mesh.userData = {
       axis: orbitAxis,
       speed: 0.003 // Locked to a slow, realistic speed
    };
    
    // Inject directly into the ThreeJS Scene
    globeEl.current.scene().add(mesh);
    activeSats.current.push(mesh);
  };

  const hasSpawnedInitial = useRef(false);

  // Ensure there's exactly ONE starting satellite
  useEffect(() => {
    if (globeEl.current && !hasSpawnedInitial.current) {
       hasSpawnedInitial.current = true;
       setTimeout(() => {
          const defaultPoint = new THREE.Vector3(140, 40, 40);
          spawnSatellite(defaultPoint);
       }, 500);
    }
  }, []);

  // Fast Animation Loop (Pure Math Orbiting)
  useEffect(() => {
    let frameId;
    const animate = () => {
      // Filter out any dead references just in case
      activeSats.current = activeSats.current.filter(m => m.parent !== null);
      
      activeSats.current.forEach(mesh => {
        // Apply quaternion rotation around the Earth's center (0,0,0)
        mesh.position.applyAxisAngle(mesh.userData.axis, mesh.userData.speed);
        // Ensure satellite always points dish towards Earth
        mesh.lookAt(0,0,0);
        
        // Spin the satellite slowly on its own axis for added realism
        mesh.rotateZ(0.005);
      });
      frameId = requestAnimationFrame(animate);
    };
    animate();
    return () => cancelAnimationFrame(frameId);
  }, []);

  // Fade satellites away based on scroll
  useEffect(() => {
    const maxOpacities = [1, 1, 1, 0.6, 1]; 
    return heroOpacity.on("change", (v) => {
      allMaterials.forEach((mat, i) => {
        mat.opacity = v * maxOpacities[i]; 
      });
    });
  }, [heroOpacity, allMaterials]);

  useEffect(() => {
    if (globeEl.current) {
      globeEl.current.controls().autoRotate = true;
      globeEl.current.controls().autoRotateSpeed = 0.5; // Slow Earth rotation
      globeEl.current.controls().enableZoom = false;
    }
  }, []);

  const handleNavClick = (e, id) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const handlePointerDown = (e) => {
    pointerPos.current = { x: e.clientX, y: e.clientY };
  };

  const handlePointerUp = (e) => {
    const dx = e.clientX - pointerPos.current.x;
    const dy = e.clientY - pointerPos.current.y;
    
    // If the user has scrolled down at all, disable the spawning feature
    if (scrollYProgress.get() > 0.05) return;
    
    // If it's a true click (not a drag)
    if (Math.sqrt(dx * dx + dy * dy) < 5) {
      if (globeEl.current) {
         const camera = globeEl.current.camera();
         const mouse = new THREE.Vector2(
           (e.clientX / window.innerWidth) * 2 - 1,
           -(e.clientY / window.innerHeight) * 2 + 1
         );
         
         const raycaster = new THREE.Raycaster();
         raycaster.setFromCamera(mouse, camera);
         
         // Orbit altitude is 140 (Earth is 100)
         const orbitSphere = new THREE.Sphere(new THREE.Vector3(0,0,0), 140);
         const targetPoint = new THREE.Vector3();
         
         // If click hits the orbital sphere shell, spawn exactly there!
         if (raycaster.ray.intersectSphere(orbitSphere, targetPoint)) {
            spawnSatellite(targetPoint);
         }
      }
    }
  };

  return (
    <div className="relative w-full bg-black overflow-x-hidden font-sans">
      
      {/* Z-0: FIXED BACKGROUND WITH TWINKLING STARS */}
      <div className="fixed inset-0 w-full h-full pointer-events-none z-0 bg-[#02040A] overflow-hidden">
        <style>{`
          @keyframes animStar {
            from { transform: translateX(0px); }
            to { transform: translateX(-2000px); }
          }
          @keyframes twinkle {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 0.2; }
          }
          .stars1 { width: 1px; height: 1px; background: transparent; box-shadow: ${starsSmall}; animation: twinkle 4s infinite, animStar 150s linear infinite; }
          .stars2 { width: 2px; height: 2px; background: transparent; box-shadow: ${starsMedium}; animation: twinkle 6s infinite, animStar 100s linear infinite; }
          .stars3 { width: 3px; height: 3px; background: transparent; box-shadow: ${starsLarge}; animation: twinkle 8s infinite, animStar 50s linear infinite; }
          
          /* Duplicate boxes for seamless horizontal loop */
          .stars1:after { content: " "; position: absolute; left: 2000px; top: 0; width: 1px; height: 1px; background: transparent; box-shadow: ${starsSmall}; }
          .stars2:after { content: " "; position: absolute; left: 2000px; top: 0; width: 2px; height: 2px; background: transparent; box-shadow: ${starsMedium}; }
          .stars3:after { content: " "; position: absolute; left: 2000px; top: 0; width: 3px; height: 3px; background: transparent; box-shadow: ${starsLarge}; }
        `}</style>
        
        {/* Core Night Sky Base Texture */}
        <div className="absolute inset-0 bg-cover bg-center opacity-70" style={{ backgroundImage: 'url("//unpkg.com/three-globe/example/img/night-sky.png")' }}></div>
        
        {/* Pure CSS Procedural Twinkling Stars */}
        <div className="stars1" />
        <div className="stars2" />
        <div className="stars3" />
      </div>

      {/* Z-10: THE 3D GLOBE (No custom layer data, we inject directly) */}
      <motion.div 
        className="fixed inset-0 w-full h-full flex items-center justify-center z-10 pointer-events-auto cursor-crosshair"
        style={{ scale: globeScale, y: globeY }}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
      >
        <Globe
          ref={globeEl}
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          polygonsData={[]}
          polygonAltitude={0.01}
          polygonCapColor={() => 'rgba(56, 189, 248, 0.1)'}
          polygonSideColor={() => 'rgba(56, 189, 248, 0.05)'}
          polygonStrokeColor={() => '#38bdf8'}
          onPolygonHover={setHoveredCountry}
          backgroundColor="rgba(0,0,0,0)"
        />
      </motion.div>

      {/* Z-20: SCROLLABLE CONTENT */}
      <div className="relative w-full h-[400vh] z-20 pointer-events-none">
        
        {/* HERO CONTENT */}
        <section className="absolute top-0 left-0 w-full h-[100vh] flex flex-col items-center justify-start pt-[28vh]">
          <motion.div 
            style={{ opacity: heroOpacity, y: heroY }}
            className="flex flex-col items-center px-4 pointer-events-none select-none"
          >
            <h1 
              className="text-6xl md:text-7xl lg:text-9xl tracking-widest text-center leading-none"
              style={{ fontFamily: '"Silkscreen", cursive', textShadow: '0 10px 40px rgba(0,0,0,0.8)' }}
            >
              <span className="text-white">PIXEL</span> <br className="md:hidden" /><span className="text-blue-400">SRISHTI</span>
            </h1>
            <p className="mt-8 text-slate-300 text-lg md:text-xl font-light tracking-wide text-center max-w-2xl px-4 drop-shadow-md">
              Making satellite intelligence accessible to everyone through autonomous agentic orchestration.
            </p>
          </motion.div>
          
          {/* Professional Floating Helper Text */}
          <motion.div 
            style={{ opacity: heroOpacity }}
            className="absolute bottom-12 px-6 py-3 rounded-full bg-white/[0.03] backdrop-blur-md border border-white/10 text-slate-300 text-xs md:text-sm font-bold tracking-[0.2em] uppercase shadow-[0_0_30px_rgba(0,0,0,0.5)] pointer-events-none flex items-center gap-3"
          >
             <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]"></span>
             Click to deploy • Drag to orbit
          </motion.div>
        </section>
         
         {/* SECTIONS */}
         <div id="mission-control" className="absolute top-[100vh] w-full flex justify-center">
            <motion.div style={{ opacity: section1Opacity }} className="pointer-events-none select-none text-center max-w-3xl px-6 pt-32">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white" style={{ fontFamily: '"Silkscreen", cursive' }}>Mission Control</h2>
              <p className="text-slate-300 text-xl leading-relaxed">Centralized command interface for geospatial orchestration. Manage your satellite constellations and tasking parameters directly from orbit with unprecedented ease.</p>
            </motion.div>
         </div>

         <div id="neural-sync" className="absolute top-[200vh] w-full flex justify-center">
            <motion.div style={{ opacity: section2Opacity }} className="pointer-events-none select-none text-center max-w-3xl px-6 pt-32">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white" style={{ fontFamily: '"Silkscreen", cursive' }}>Neural Sync</h2>
              <p className="text-slate-300 text-xl leading-relaxed">Cross-modal AI pipeline. Automatically fuses SAR (Synthetic Aperture Radar) and Optical RGB data for all-weather intelligence gathering.</p>
            </motion.div>
         </div>

         <div id="telemetry" className="absolute top-[300vh] w-full flex justify-center">
            <motion.div style={{ opacity: section3Opacity }} className="pointer-events-none select-none text-center max-w-3xl px-6 pt-32">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white" style={{ fontFamily: '"Silkscreen", cursive' }}>Telemetry Downlink</h2>
              <p className="text-slate-300 text-xl leading-relaxed mb-8">Real-time downlink analytics. Stream massive datasets straight to the Agentic Router for on-the-fly Visual Question Answering (VQA).</p>
              <Link to="/app" className="inline-block pointer-events-auto bg-blue-600 text-white px-8 py-4 rounded-full text-lg font-bold hover:bg-blue-500 transition-colors shadow-[0_0_30px_rgba(37,99,235,0.5)]">
                Initialize Sequence
              </Link>
            </motion.div>
         </div>

      </div>

      {/* Z-50: TOP NAVBAR */}
      <div className="fixed top-6 w-full px-8 md:px-12 pointer-events-auto z-50">
        <div className="flex justify-between items-center w-full relative">
          
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl overflow-hidden bg-black border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.1)] shrink-0">
              <img src="/logo.jpg?v=3" alt="PIXEL Srishti" className="w-full h-full object-cover" />
            </div>
            <span className="text-2xl tracking-widest mt-1 drop-shadow-md" style={{ fontFamily: '"Silkscreen", cursive' }}>
              <span className="text-white">PIXEL</span> <span className="text-blue-400">SRISHTI</span>
            </span>
          </div>
          
          <div className="absolute left-1/2 -translate-x-1/2 hidden lg:flex items-center gap-8 bg-white/[0.03] border border-white/10 px-10 py-3.5 rounded-full backdrop-blur-md shadow-2xl">
            <a href="#mission-control" onClick={(e) => handleNavClick(e, 'mission-control')} className="text-[13px] uppercase tracking-widest font-bold text-slate-300 hover:text-white transition-colors cursor-pointer">Mission Control</a>
            <a href="#neural-sync" onClick={(e) => handleNavClick(e, 'neural-sync')} className="text-[13px] uppercase tracking-widest font-bold text-slate-300 hover:text-white transition-colors cursor-pointer">Neural Sync</a>
            <a href="#telemetry" onClick={(e) => handleNavClick(e, 'telemetry')} className="text-[13px] uppercase tracking-widest font-bold text-slate-300 hover:text-white transition-colors cursor-pointer">Telemetry</a>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="text-[13px] uppercase tracking-widest font-bold text-slate-300 hover:text-white transition-colors cursor-pointer">Documentation</a>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/app" className="bg-white text-black px-7 py-3.5 rounded-full text-sm font-extrabold tracking-wide hover:bg-slate-200 transition-all shadow-[0_0_20px_rgba(255,255,255,0.4)] hover:shadow-[0_0_30px_rgba(255,255,255,0.6)]">
              INITIATE APP
            </Link>
          </div>
        </div>
      </div>

    </div>
  );
}