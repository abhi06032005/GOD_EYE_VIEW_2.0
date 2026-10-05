import { rememberFirstRunSessionDismissed } from '../firstRunExperience.js';

const resolveCesium = () => globalThis.Cesium || null;

/**
 * Built-in rich regional profiles for instant offline/keyless navigation and telemetry.
 */
export const REGION_PROFILES = Object.freeze({
  bangalore: {
    id: 'bangalore',
    aliases: ['bangalore', 'bengaluru', 'blr', 'banglore'],
    name: 'Bengaluru (Bangalore)',
    country: 'Karnataka, India',
    flag: '🇮🇳',
    coordinates: { lat: 12.9716, lon: 77.5946 },
    elevation: '920m WGS84',
    camera: {
      lat: 12.9716,
      lon: 77.5946,
      altitude: 2800,
      pitch: -42,
      heading: 0,
    },
    summary:
      "India's premier high-tech & aerospace capital on the Deccan Plateau. Major commercial aviation hub (Kempegowda Int'l - BLR / VOBL), space telemetry operations (ISRO), and central communications infrastructure.",
    landmarks: [
      { name: 'Kempegowda Int\'l Airport (BLR)', lat: 13.1986, lon: 77.7066, alt: 1400, pitch: -22, heading: 0 },
      { name: 'Vidhana Soudha', lat: 12.9796, lon: 77.5907, alt: 650, pitch: -28, heading: 90 },
      { name: 'UB City & CBD', lat: 12.9716, lon: 77.5960, alt: 550, pitch: -22, heading: 45 },
      { name: 'ISRO Satellite Telemetry Centre', lat: 13.0334, lon: 77.5640, alt: 750, pitch: -30, heading: 180 },
      { name: 'Electronic City Tech Hub', lat: 12.8452, lon: 77.6602, alt: 850, pitch: -25, heading: 315 },
    ],
    availableDataFeeds: [
      {
        layerId: 'flights',
        name: 'Live Airspace & Flights (ADS-B)',
        icon: '✈️',
        source: 'OpenSky Network ADS-B',
        description: 'Live commercial, cargo and regional flight telemetry across Bangalore (BLR) sector and southern transit corridors.',
        defaultActive: true,
      },
      {
        layerId: 'weather',
        name: 'Atmospheric Radar & Cloud Cover',
        icon: '🌦️',
        source: 'NOAA GFS / Open-Meteo',
        description: 'Real-time weather radar, precipitation, cloud ceiling, temperature and atmospheric sounding.',
        defaultActive: true,
      },
      {
        layerId: 'wind',
        name: 'Dynamic Wind Vector Flow',
        icon: '💨',
        source: 'ECMWF / GFS Wind Dynamics',
        description: 'Particle wind flow vectors animating atmospheric currents over the Deccan plateau.',
        defaultActive: false,
      },
      {
        layerId: 'satellites',
        name: 'Active Satellite Overpasses',
        icon: '🛰️',
        source: 'CelesTrak / Space-Track NORAD',
        description: 'Live orbital telemetry for satellites (ISS, Starlink, Earth observation, GPS) overhead.',
        defaultActive: true,
      },
      {
        layerId: 'traffic',
        name: 'Road Network & Arterial Traffic',
        icon: '🚦',
        source: 'Overpass / OSM Live Flow',
        description: 'Real-time road flow, congestion speeds on Outer Ring Road, Hosur Road and expressways.',
        defaultActive: false,
      },
      {
        layerId: 'cctv',
        name: 'Live Traffic CCTV Network (BTP)',
        icon: '📹',
        source: 'Bangalore Traffic Police (BTP) & Indian Highway Cams',
        description: 'Real-time traffic camera video streams & optical perception at Silk Board, MG Road, Hebbal, and Electronic City.',
        defaultActive: true,
      },
      {
        layerId: 'local-firms',
        altLayerId: 'firms',
        name: 'NASA FIRMS Thermal Hotspots & Fires',
        icon: '🔥',
        source: 'NASA MODIS / VIIRS Satellites',
        description: 'Real-time thermal anomaly and wildfire satellite detections in Karnataka and southern India.',
        defaultActive: false,
      },
      {
        layerId: 'earthquakes',
        name: 'USGS Seismic Activity',
        icon: '🌍',
        source: 'USGS Real-Time Earthquake Catalog',
        description: 'Global and regional seismic fault line sensors and earthquake monitoring.',
        defaultActive: false,
      },
      {
        layerId: 'radio',
        name: 'Regional Audio & Aviation Comms',
        icon: '📻',
        source: 'LiveATC / Regional Streams',
        description: 'Air traffic control radio feeds and regional broadcast audio.',
        defaultActive: false,
      },
      {
        layerId: 'installations',
        name: 'Defense & Aerospace Sites',
        icon: '🏛️',
        source: 'Global Geospatial Installations Registry',
        description: 'Defense installations, radar sites, and aerospace space facilities.',
        defaultActive: false,
      },
    ],
  },

  tokyo: {
    id: 'tokyo',
    aliases: ['tokyo', 'tyo', 'haneda', 'narita'],
    name: 'Tokyo',
    country: 'Kanto, Japan',
    flag: '🇯🇵',
    coordinates: { lat: 35.6762, lon: 139.6503 },
    elevation: '40m WGS84',
    camera: {
      lat: 35.6895,
      lon: 139.6917,
      altitude: 20000,
      pitch: -28,
      heading: 0,
    },
    summary:
      'Greater Tokyo megalopolis. Dense high-speed rail, busy coastal airspace anchored by Haneda (HND) and Narita (NRT), maritime bay traffic, and seismic monitoring.',
    landmarks: [
      { name: 'Tokyo Tower', lat: 35.6586, lon: 139.7454, alt: 850, pitch: -25, heading: 0 },
      { name: 'Tokyo Skytree', lat: 35.7101, lon: 139.8107, alt: 900, pitch: -25, heading: 30 },
      { name: 'Imperial Palace', lat: 35.6852, lon: 139.7528, alt: 900, pitch: -35, heading: 0 },
      { name: 'Shinjuku Center', lat: 35.6929, lon: 139.6925, alt: 750, pitch: -22, heading: 45 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'Live Airspace & Flights (ADS-B)', icon: '✈️', source: 'OpenSky Network ADS-B', description: 'Dense commercial aviation over Haneda, Narita and Tokyo Bay.', defaultActive: true },
      { layerId: 'vessels', name: 'Marine AIS Vessel Traffic', icon: '🚢', source: 'Global AIS Marine Network', description: 'Cargo and container vessels in Tokyo Bay and Pacific shipping lanes.', defaultActive: true },
      { layerId: 'weather', name: 'Atmospheric Radar & Typhoons', icon: '🌦️', source: 'NOAA / JMA Weather Radar', description: 'Precipitation radar, coastal storm tracks and cloud ceiling.', defaultActive: true },
      { layerId: 'earthquakes', name: 'USGS / JMA Seismic Activity', icon: '🌍', source: 'USGS Real-Time Catalog', description: 'Active subduction zone and fault line seismic monitoring.', defaultActive: true },
      { layerId: 'satellites', name: 'Satellite Passes', icon: '🛰️', source: 'CelesTrak', description: 'Orbital assets passing over Japan.', defaultActive: false },
      { layerId: 'traffic', name: 'Tokyo Shuto Expressway Flow', icon: '🚦', source: 'Overpass / OSM', description: 'Metropolitan road velocity.', defaultActive: false },
    ],
  },

  sanfrancisco: {
    id: 'sanfrancisco',
    aliases: ['san francisco', 'sf', 'bay area', 'silicon valley'],
    name: 'San Francisco',
    country: 'California, USA',
    flag: '🇺🇸',
    coordinates: { lat: 37.7749, lon: -122.4194 },
    elevation: '15m WGS84',
    camera: {
      lat: 37.7749,
      lon: -122.4194,
      altitude: 18000,
      pitch: -28,
      heading: 30,
    },
    summary:
      'San Francisco Bay Area. Maritime traffic through the Golden Gate, SFO/OAK/SJC commercial air corridors, and San Andreas fault seismic instrumentation.',
    landmarks: [
      { name: 'Golden Gate Bridge', lat: 37.8199, lon: -122.4783, alt: 1400, pitch: -20, heading: 45 },
      { name: 'Salesforce Tower', lat: 37.7897, lon: -122.3972, alt: 680, pitch: -25, heading: 330 },
      { name: 'Alcatraz Island', lat: 37.8267, lon: -122.4230, alt: 800, pitch: -30, heading: 0 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'Live Flights & SFO Airspace', icon: '✈️', source: 'OpenSky ADS-B', description: 'Arrivals and departures at SFO, OAK and San Jose.', defaultActive: true },
      { layerId: 'vessels', name: 'Bay & Golden Gate Marine AIS', icon: '🚢', source: 'AIS Live', description: 'Container shipping through the Golden Gate strait.', defaultActive: true },
      { layerId: 'weather', name: 'Atmospheric Radar & Marine Fog', icon: '🌦️', source: 'NOAA HRRR / GFS', description: 'Radar precipitation and marine layer fog dynamics.', defaultActive: true },
      { layerId: 'earthquakes', name: 'San Andreas Fault Sensors', icon: '🌍', source: 'USGS Earthquakes', description: 'Real-time seismic sensors along the Northern California fault lines.', defaultActive: true },
      { layerId: 'local-firms', altLayerId: 'firms', name: 'NASA FIRMS Wildfire Thermal Hotspots', icon: '🔥', source: 'NASA Satellite Hotspots', description: 'Active wildfire detection in California.', defaultActive: false },
      { layerId: 'satellites', name: 'Orbital Satellites Overhead', icon: '🛰️', source: 'CelesTrak', description: 'Real-time satellite passes.', defaultActive: false },
    ],
  },

  london: {
    id: 'london',
    aliases: ['london', 'heathrow', 'gatwick', 'uk'],
    name: 'London',
    country: 'United Kingdom',
    flag: '🇬🇧',
    coordinates: { lat: 51.5074, lon: -0.1278 },
    elevation: '15m WGS84',
    camera: {
      lat: 51.5074,
      lon: -0.1278,
      altitude: 18000,
      pitch: -28,
      heading: 0,
    },
    summary:
      'United Kingdom capital. High-volume European airspace hub (Heathrow, Gatwick, Stansted), River Thames navigation, and North Sea weather dynamics.',
    landmarks: [
      { name: 'Tower Bridge', lat: 51.5055, lon: -0.0754, alt: 400, pitch: -25, heading: 270 },
      { name: 'The Shard', lat: 51.5045, lon: -0.0865, alt: 850, pitch: -20, heading: 0 },
      { name: 'Big Ben / Parliament', lat: 51.5007, lon: -0.1246, alt: 600, pitch: -25, heading: 180 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'London TMA Flight Vectors', icon: '✈️', source: 'OpenSky ADS-B', description: 'Major European air corridor connecting LHR, LGW and STN.', defaultActive: true },
      { layerId: 'weather', name: 'UK Met Office / NOAA Radar', icon: '🌦️', source: 'NOAA GFS', description: 'Live precipitation radar and cloud layers.', defaultActive: true },
      { layerId: 'traffic', name: 'London M25 & City Road Flow', icon: '🚦', source: 'Overpass / OSM', description: 'Congestion and velocity tracking on Greater London routes.', defaultActive: false },
      { layerId: 'satellites', name: 'Satellite Passes', icon: '🛰️', source: 'CelesTrak', description: 'ISS and polar orbiters passing over the British Isles.', defaultActive: false },
    ],
  },

  dubai: {
    id: 'dubai',
    aliases: ['dubai', 'dxb', 'uae', 'emirates'],
    name: 'Dubai',
    country: 'United Arab Emirates',
    flag: '🇦🇪',
    coordinates: { lat: 25.2048, lon: 55.2708 },
    elevation: '5m WGS84',
    camera: {
      lat: 25.2048,
      lon: 55.2708,
      altitude: 16000,
      pitch: -28,
      heading: 45,
    },
    summary:
      'Middle Eastern global crossroads. World\'s busiest international passenger airport (DXB / OMDB), Persian Gulf maritime container corridors, and extreme desert atmospheric conditions.',
    landmarks: [
      { name: 'Burj Khalifa', lat: 25.1972, lon: 55.2744, alt: 600, pitch: -20, heading: 200 },
      { name: 'Burj Al Arab', lat: 25.1412, lon: 55.1853, alt: 500, pitch: -25, heading: 90 },
      { name: 'Palm Jumeirah', lat: 25.1124, lon: 55.1390, alt: 1200, pitch: -40, heading: 0 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'DXB International Air Traffic', icon: '✈️', source: 'OpenSky ADS-B', description: 'Global long-haul flight connections over the Persian Gulf.', defaultActive: true },
      { layerId: 'vessels', name: 'Persian Gulf & Strait of Hormuz AIS', icon: '🚢', source: 'AIS Live', description: 'Crude tankers and container shipping traffic.', defaultActive: true },
      { layerId: 'weather', name: 'Desert Atmospheric Conditions', icon: '🌦️', source: 'NOAA GFS', description: 'Thermal winds, sandstorm tracking and surface temperatures.', defaultActive: true },
      { layerId: 'satellites', name: 'Satellite Overpasses', icon: '🛰️', source: 'CelesTrak', description: 'Satellite tracking over the Arabian peninsula.', defaultActive: false },
    ],
  },

  newyork: {
    id: 'newyork',
    aliases: ['new york', 'nyc', 'manhattan', 'jfk'],
    name: 'New York City',
    country: 'New York, USA',
    flag: '🇺🇸',
    coordinates: { lat: 40.7128, lon: -74.0060 },
    elevation: '10m WGS84',
    camera: {
      lat: 40.7128,
      lon: -74.0060,
      altitude: 18000,
      pitch: -28,
      heading: 30,
    },
    summary:
      'Global financial capital and dense tri-state airspace (JFK, LGA, EWR). Massive port maritime traffic and dense metropolitan road network.',
    landmarks: [
      { name: 'Empire State Building', lat: 40.7484, lon: -73.9857, alt: 850, pitch: -12, heading: 30 },
      { name: 'One World Trade Center', lat: 40.7127, lon: -74.0134, alt: 850, pitch: -25, heading: 0 },
      { name: 'Statue of Liberty', lat: 40.6892, lon: -74.0445, alt: 450, pitch: -25, heading: 315 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'Tri-State Air Corridor (JFK/LGA/EWR)', icon: '✈️', source: 'OpenSky ADS-B', description: 'Heavy commercial flight traffic across the Atlantic coast.', defaultActive: true },
      { layerId: 'vessels', name: 'New York Harbor Marine Traffic', icon: '🚢', source: 'AIS Live', description: 'Tug, ferry and container vessel positioning.', defaultActive: true },
      { layerId: 'weather', name: 'Atlantic Coastal Weather Radar', icon: '🌦️', source: 'NOAA NEXRAD', description: 'Precipitation bands, winter storms and cloud cover.', defaultActive: true },
      { layerId: 'traffic', name: 'Metropolitan Road & Bridge Flow', icon: '🚦', source: 'Overpass / OSM', description: 'Bridge, tunnel and highway speeds.', defaultActive: false },
    ],
  },

  mumbai: {
    id: 'mumbai',
    aliases: ['mumbai', 'bombay', 'bom'],
    name: 'Mumbai',
    country: 'Maharashtra, India',
    flag: '🇮🇳',
    coordinates: { lat: 19.0760, lon: 72.8777 },
    elevation: '14m WGS84',
    camera: {
      lat: 19.0760,
      lon: 72.8777,
      altitude: 20000,
      pitch: -28,
      heading: 0,
    },
    summary:
      'India\'s commercial and financial hub on the Arabian Sea coast. High-density coastal flight operations (BOM / VABB) and heavy maritime port movements.',
    landmarks: [
      { name: 'Gateway of India', lat: 18.9220, lon: 72.8347, alt: 500, pitch: -25, heading: 90 },
      { name: 'Bandra-Worli Sea Link', lat: 19.0300, lon: 72.8180, alt: 1100, pitch: -25, heading: 330 },
      { name: 'Chhatrapati Shivaji Airport (BOM)', lat: 19.0896, lon: 72.8656, alt: 1200, pitch: -25, heading: 0 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'Mumbai (BOM) Airspace Feeds', icon: '✈️', source: 'OpenSky ADS-B', description: 'Arabian Sea arrival corridors and subcontinent routes.', defaultActive: true },
      { layerId: 'vessels', name: 'Jawaharlal Nehru Port AIS', icon: '🚢', source: 'AIS Live', description: 'Container and tanker shipping in Mumbai Harbour.', defaultActive: true },
      { layerId: 'weather', name: 'Monsoon & Coastal Weather Radar', icon: '🌦️', source: 'IMD / NOAA', description: 'Tropical precipitation radar and coastal winds.', defaultActive: true },
      { layerId: 'traffic', name: 'Western Express Highway Flow', icon: '🚦', source: 'Overpass / OSM', description: 'Real-time road transit speeds.', defaultActive: false },
    ],
  },

  paris: {
    id: 'paris',
    aliases: ['paris', 'cdg', 'france'],
    name: 'Paris',
    country: 'Île-de-France, France',
    flag: '🇫🇷',
    coordinates: { lat: 48.8566, lon: 2.3522 },
    elevation: '35m WGS84',
    camera: {
      lat: 48.8566,
      lon: 2.3522,
      altitude: 18000,
      pitch: -28,
      heading: 0,
    },
    summary:
      'Capital of France. Major European air corridor anchored by Charles de Gaulle (CDG) and Orly (ORY), Seine waterways, and continental meteorological systems.',
    landmarks: [
      { name: 'Eiffel Tower', lat: 48.8584, lon: 2.2945, alt: 750, pitch: -25, heading: 315 },
      { name: 'Arc de Triomphe', lat: 48.8738, lon: 2.2950, alt: 400, pitch: -28, heading: 45 },
      { name: 'Louvre Pyramid', lat: 48.8606, lon: 2.3376, alt: 500, pitch: -35, heading: 0 },
    ],
    availableDataFeeds: [
      { layerId: 'flights', name: 'CDG & Orly Air Corridor', icon: '✈️', source: 'OpenSky ADS-B', description: 'Commercial aircraft vectors across Western Europe.', defaultActive: true },
      { layerId: 'weather', name: 'Météo-France / NOAA Radar', icon: '🌦️', source: 'NOAA GFS', description: 'Real-time rainfall radar and cloud layers.', defaultActive: true },
      { layerId: 'traffic', name: 'Boulevard Périphérique Flow', icon: '🚦', source: 'Overpass / OSM', description: 'Paris arterial traffic velocities.', defaultActive: false },
      { layerId: 'satellites', name: 'Satellite Passes', icon: '🛰️', source: 'CelesTrak', description: 'Spacecraft overflying continental Europe.', defaultActive: false },
    ],
  },
});

/**
 * Universal default layer catalog used when dynamically resolving any place on Earth.
 */
export const GLOBAL_DATA_FEEDS = Object.freeze([
  {
    layerId: 'flights',
    name: 'Live Airspace & Flights (ADS-B)',
    icon: '✈️',
    source: 'OpenSky Network ADS-B',
    description: 'Real-time commercial and regional aircraft tracking in local and transit airspace.',
    defaultActive: true,
  },
  {
    layerId: 'weather',
    name: 'Atmospheric Radar & Clouds',
    icon: '🌦️',
    source: 'NOAA GFS / Open-Meteo',
    description: 'Precipitation radar, temperature, cloud cover and barometric pressure.',
    defaultActive: true,
  },
  {
    layerId: 'wind',
    name: 'Dynamic Wind Vector Flow',
    icon: '💨',
    source: 'ECMWF / GFS Dynamics',
    description: 'Global dynamic vector wind flow lines animating atmospheric currents.',
    defaultActive: false,
  },
  {
    layerId: 'satellites',
    name: 'Active Satellite Overpasses',
    icon: '🛰️',
    source: 'CelesTrak NORAD',
    description: 'Live orbital telemetry of satellites (ISS, Starlink, Earth observation) overhead.',
    defaultActive: true,
  },
  {
    layerId: 'local-firms',
    altLayerId: 'firms',
    name: 'NASA FIRMS Thermal Hotspots',
    icon: '🔥',
    source: 'NASA MODIS / VIIRS Satellites',
    description: 'Real-time thermal anomaly and wildfire satellite detections.',
    defaultActive: false,
  },
  {
    layerId: 'earthquakes',
    name: 'USGS Real-Time Earthquakes',
    icon: '🌍',
    source: 'USGS Seismic Network',
    description: 'Worldwide tectonic fault line sensors and earthquake monitoring.',
    defaultActive: false,
  },
  {
    layerId: 'traffic',
    name: 'Road Network Traffic Flow',
    icon: '🚦',
    source: 'Overpass / OSM Live Flow',
    description: 'Live road congestion speeds on arterial routes and expressways.',
    defaultActive: false,
  },
  {
    layerId: 'cctv',
    name: 'Live CCTV Camera Network',
    icon: '📹',
    source: 'Municipal & Highway Camera Proxies',
    description: 'Real-time urban and highway traffic camera video streams and optical coverage.',
    defaultActive: false,
  },
]);

export const DEFAULT_GROQ_API_KEY =
  (typeof import.meta !== 'undefined' &&
    (import.meta.env?.VITE_GROQ_API_KEY || import.meta.env?.GROQ_API_KEY)) ||
  '';
export const DEFAULT_GROQ_MODEL = 'openai/gpt-oss-120b';

/**
 * AI Regional Intelligence Assistant Controller.
 */
export class AiBotController {
  constructor(options = {}) {
    const { viewer, styleManager, dataManager, placeSearch, scene } = options;
    this.viewer = viewer;
    this.styleManager = styleManager;
    this.dataManager = dataManager;
    this.placeSearch = placeSearch;
    this.scene = scene;

    this.groqApiKey =
      options.groqApiKey ||
      (typeof window !== 'undefined' && window.__GROQ_API_KEY__) ||
      (typeof process !== 'undefined' && process.env?.VITE_GROQ_API_KEY) ||
      (typeof import.meta !== 'undefined' && import.meta.env?.VITE_GROQ_API_KEY) ||
      DEFAULT_GROQ_API_KEY;
    this.groqModel =
      options.groqModel ||
      (typeof window !== 'undefined' && window.__GROQ_MODEL__) ||
      DEFAULT_GROQ_MODEL;

    this.currentRegion = null;
    this.activeLayers = new Set();
    this.isCollapsed = false;

    this._bindElements();
    this._attachEvents();
    this._listenToLayerChanges();

    // Ensure legacy intrusive first-run launcher is suppressed
    rememberFirstRunSessionDismissed();
    const legacyLauncher = document.getElementById('first-run-launcher');
    if (legacyLauncher) {
      legacyLauncher.classList.remove('visible');
      legacyLauncher.setAttribute('hidden', '');
    }

    // Hide unnecessary noisy cards to keep view clean
    const scenePanel = document.getElementById('scene-panel');
    if (scenePanel) {
      scenePanel.style.display = 'none';
    }

    // Default start open
    this.expand();
  }

  _bindElements() {
    this.sidebar = document.getElementById('ai-bot-sidebar');
    this.toggleBtn = document.getElementById('ai-bot-toggle-btn');
    this.messagesContainer = document.getElementById('ai-bot-messages');
    this.form = document.getElementById('ai-bot-form');
    this.input = document.getElementById('ai-bot-input');
    this.clearBtn = document.getElementById('ai-bot-clear-btn');
    this.minimizeBtn = document.getElementById('ai-bot-minimize-btn');
    this.voiceBtn = document.getElementById('ai-bot-voice-btn');
    this.activeRegionBar = document.getElementById('ai-active-region-bar');
    this.activeRegionName = document.getElementById('ai-active-region-name');
    this.activeLayersNum = document.getElementById('ai-active-layers-num');
    this.navBtn = document.getElementById('ai-bot-nav-btn');
  }

  _attachEvents() {
    if (this.navBtn) {
      this.navBtn.addEventListener('click', () => {
        if (this.isCollapsed) {
          this.expand();
        } else {
          this.collapse();
        }
      });
    }

    if (this.form) {
      this.form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = this.input?.value?.trim();
        if (text) {
          this.handleUserQuery(text);
          this.input.value = '';
        }
      });
    }

    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => {
        this.clearMessages();
      });
    }

    if (this.minimizeBtn) {
      this.minimizeBtn.addEventListener('click', () => {
        this.collapse();
      });
    }

    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => {
        this.expand();
      });
    }

    if (this.voiceBtn) {
      this.voiceBtn.addEventListener('click', () => {
        this.promptVoiceInput();
      });
    }

    // Fullscreen Map toggle button in top chrome
    const topMapToggleBtn = document.getElementById('toggle-fullscreen-map');
    if (topMapToggleBtn) {
      topMapToggleBtn.addEventListener('click', () => {
        this.toggleFullscreenMap();
      });
    }

    // Quick region clicks and feed row toggles (delegated)
    if (this.messagesContainer) {
      this.messagesContainer.addEventListener('click', (e) => {
        const fullscreenBtn = e.target.closest('[data-action="toggle-fullscreen-map"]');
        if (fullscreenBtn) {
          this.toggleFullscreenMap();
          return;
        }

        const presetBtn = e.target.closest('[data-preset-filter]');
        if (presetBtn) {
          const filter = presetBtn.dataset.presetFilter;
          this.applyFeedPreset(filter);
          return;
        }

        const regionBtn = e.target.closest('[data-region-query]');
        if (regionBtn) {
          const query = regionBtn.dataset.regionQuery;
          this.handleUserQuery(`I want ${query} data`);
          return;
        }

        const landmarkBtn = e.target.closest('[data-landmark-lat]');
        if (landmarkBtn) {
          const lat = parseFloat(landmarkBtn.dataset.landmarkLat);
          const lon = parseFloat(landmarkBtn.dataset.landmarkLon);
          const alt = parseFloat(landmarkBtn.dataset.landmarkAlt) || 600;
          const pitch = parseFloat(landmarkBtn.dataset.landmarkPitch) || -25;
          const heading = parseFloat(landmarkBtn.dataset.landmarkHeading) || 0;
          const name = landmarkBtn.dataset.landmarkName;
          this.flyToLandmarkTarget(lat, lon, alt, pitch, heading, name);
          return;
        }

        const batchBtn = e.target.closest('[data-batch-action]');
        if (batchBtn) {
          const action = batchBtn.dataset.batchAction;
          if (action === 'activate-all') {
            this.activateAllFeeds();
          } else if (action === 'activate-selected') {
            this.activateSelectedFeeds();
          } else if (action === 'clear-all') {
            this.clearAllFeeds();
          }
          return;
        }

        // ONE-TAP INSTANT FEED ROW TOGGLE
        const feedRow = e.target.closest('.ai-feed-row');
        if (feedRow && !e.target.matches('input[type="checkbox"]')) {
          const layerId = feedRow.dataset.layerId;
          if (layerId) {
            const cb = feedRow.querySelector('.ai-feed-cb');
            const newState = cb ? !cb.checked : !feedRow.classList.contains('active');
            if (cb) cb.checked = newState;
            this.setLayerState(layerId, newState);
            this._syncCheckboxState(layerId, newState);
            return;
          }
        }
      });

      // Checkbox changes for layers
      this.messagesContainer.addEventListener('change', (e) => {
        const cb = e.target.closest('.ai-feed-cb');
        if (cb) {
          const layerId = cb.dataset.layerId;
          const shouldEnable = cb.checked;
          this.setLayerState(layerId, shouldEnable);
          this._syncCheckboxState(layerId, shouldEnable);
        }
      });
    }
  }

  _listenToLayerChanges() {
    if (this.dataManager && typeof this.dataManager.subscribe === 'function') {
      this.dataManager.subscribe((event) => {
        if (event && event.layerId) {
          this._syncCheckboxState(event.layerId, event.enabled);
          this._updateActiveBar();
        }
      });
    }
  }

  _syncCheckboxState(layerId, isEnabled) {
    if (!this.messagesContainer) return;
    const rows = this.messagesContainer.querySelectorAll(
      `.ai-feed-row[data-layer-id="${layerId}"]`
    );
    rows.forEach((row) => {
      row.classList.toggle('active', isEnabled);
      const cb = row.querySelector('.ai-feed-cb');
      if (cb) cb.checked = isEnabled;
      const sw = row.querySelector('.ai-switch');
      if (sw) sw.classList.toggle('checked', isEnabled);
      const statusBadge = row.querySelector('.ai-feed-status');
      if (statusBadge) {
        statusBadge.textContent = isEnabled ? '● STREAMING' : '○ TAP TO STREAM';
        statusBadge.className = `ai-feed-status ${isEnabled ? 'streaming' : 'available'}`;
      }
    });
  }

  _updateActiveBar() {
    if (!this.activeLayersNum || !this.dataManager) return;
    let count = 0;
    if (this.dataManager.layers) {
      for (const [id, entry] of this.dataManager.layers) {
        if (entry.enabled) count++;
      }
    }
    this.activeLayersNum.textContent = String(count);
  }

  collapse() {
    this.isCollapsed = true;
    if (this.sidebar) {
      this.sidebar.classList.add('collapsed');
      this.sidebar.setAttribute('aria-hidden', 'true');
    }
    if (this.toggleBtn) {
      this.toggleBtn.classList.add('visible');
      this.toggleBtn.setAttribute('aria-expanded', 'false');
    }
  }

  expand() {
    this.isCollapsed = false;
    if (this.sidebar) {
      this.sidebar.classList.remove('collapsed');
      this.sidebar.setAttribute('aria-hidden', 'false');
    }
    if (this.toggleBtn) {
      this.toggleBtn.classList.remove('visible');
      this.toggleBtn.setAttribute('aria-expanded', 'true');
    }
    this.input?.focus();
  }

  clearMessages() {
    if (!this.messagesContainer) return;
    this.messagesContainer.innerHTML = '';
    this.appendBotMessage(`
      <div class="ai-welcome-badge">CONSOLE CLEARED</div>
      <p class="ai-welcome-desc">
        Ask for any region on Earth (e.g. <em>"I want Bangalore data"</em>, <em>"Tokyo"</em>, <em>"London"</em>, <em>"San Francisco"</em>) to fly the globe and discover all available data feeds.
      </p>
    `);
  }

  toggleFullscreenMap() {
    if (!this.viewer?.scene) return;
    const Cesium = resolveCesium();
    const is2D = this.viewer.scene.mode === (Cesium.SceneMode?.SCENE2D ?? 2);
    if (is2D) {
      this.viewer.scene.morphTo3D(1.2);
      this.appendBotMessage('🌐 <strong>Switched to 3D Globe Projection.</strong>');
    } else {
      this.viewer.scene.morphTo2D(1.2);
      this.appendBotMessage('🗺️ <strong>Switched to Fullscreen Flat Map (2D).</strong> The map fills the entire screen edge-to-edge without sphere curvature.');
    }
  }

  applyFeedPreset(preset) {
    if (!this.currentRegion) return;
    const feeds = this.currentRegion.availableDataFeeds || [];

    if (preset === 'all') {
      feeds.forEach((f) => {
        const id = this._resolveRealLayerId(f.layerId, f.altLayerId);
        this.setLayerState(id, true);
        this._syncCheckboxState(id, true);
      });
      this.appendBotMessage(`⚡ <strong>Activated all ${feeds.length} live feeds</strong> for ${this._escapeHtml(this.currentRegion.name)}.`);
    } else if (preset === 'cctv-traffic') {
      const targets = ['cctv', 'traffic'];
      feeds.forEach((f) => {
        const id = this._resolveRealLayerId(f.layerId, f.altLayerId);
        const shouldEnable = targets.includes(f.layerId);
        if (shouldEnable) {
          this.setLayerState(id, true);
          this._syncCheckboxState(id, true);
        }
      });
      this.appendBotMessage(`📹 <strong>Activated Live Traffic CCTV & Road Flow</strong> for ${this._escapeHtml(this.currentRegion.name)}.`);
    } else if (preset === 'airspace-weather') {
      const targets = ['flights', 'weather', 'wind', 'radio'];
      feeds.forEach((f) => {
        const id = this._resolveRealLayerId(f.layerId, f.altLayerId);
        const shouldEnable = targets.includes(f.layerId);
        if (shouldEnable) {
          this.setLayerState(id, true);
          this._syncCheckboxState(id, true);
        }
      });
      this.appendBotMessage(`✈️ <strong>Activated Live Airspace, Flights & Radar</strong> for ${this._escapeHtml(this.currentRegion.name)}.`);
    } else if (preset === 'clear') {
      this.clearAllFeeds();
    }
  }

  appendUserMessage(text) {
    const el = document.createElement('div');
    el.className = 'ai-message ai-message-user';
    el.dataset.messageRole = 'user';
    el.innerHTML = `<div class="ai-message-bubble">${this._escapeHtml(text)}</div>`;
    this.messagesContainer.appendChild(el);
    this._scrollToBottom();
  }

  appendBotMessage(htmlContent) {
    const el = document.createElement('div');
    el.className = 'ai-message ai-message-bot';
    el.dataset.messageRole = 'bot';
    el.innerHTML = `<div class="ai-message-bubble">${htmlContent}</div>`;
    this.messagesContainer.appendChild(el);
    this._scrollToBottom();
  }

  _scrollToBottom() {
    if (this.messagesContainer) {
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
  }

  _escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /**
   * Main query processor: handles natural language questions and region requests.
   */
  async handleUserQuery(query) {
    this.appendUserMessage(query);

    const q = query.toLowerCase().trim();

    // 1. Check if user is asking for general actions (zoom, weather, night vision, etc.)
    if (q.includes('night vision') || q.includes('nvg')) {
      this.styleManager?.applyStyle?.('surveillance');
      this.appendBotMessage(`🌙 <strong>Surveillance / NVG Mode Engaged.</strong> Night-vision green phosphor enhancement enabled on the globe.`);
      return;
    }

    if (q.includes('thermal') || q.includes('flir')) {
      this.styleManager?.applyStyle?.('thermal');
      this.appendBotMessage(`🌡️ <strong>FLIR Thermal Contrast Engaged.</strong> Infrared thermal gradient applied.`);
      return;
    }

    if (q.includes('crt') || q.includes('retro')) {
      this.styleManager?.applyStyle?.('retro');
      this.appendBotMessage(`▦ <strong>CRT Phosphor Mode Engaged.</strong> Green phosphor scanlines enabled.`);
      return;
    }

    if (q.includes('normal') || q.includes('reset style') || q.includes('standard')) {
      this.styleManager?.applyStyle?.('normal');
      this.appendBotMessage(`◯ <strong>Standard Globe View Restored.</strong>`);
      return;
    }

    if (q.includes('reset globe') || q.includes('full globe') || q.includes('world view')) {
      this.flyToFullGlobe();
      this.appendBotMessage(`🌍 <strong>Camera returned to global orbit view.</strong>`);
      return;
    }

    // 2. Extract potential region name from the query
    const regionName = this._extractRegionName(query);

    // Show scanning indicator
    const scanningMsg = document.createElement('div');
    scanningMsg.className = 'ai-message ai-message-bot';
    scanningMsg.innerHTML = `<div class="ai-message-bubble" style="color: var(--accent);"><span class="ai-bot-avatar-ring" style="display:inline-block;width:12px;height:12px;margin-right:8px;vertical-align:middle;"></span> <span style="font-size:9px;font-family:var(--font-mono);background:rgba(0,255,170,0.15);color:#00ffaa;padding:1px 5px;border-radius:3px;margin-right:6px;">GROQ AI</span> Analyzing spatial intelligence for <strong>${this._escapeHtml(regionName || query)}</strong>...</div>`;
    this.messagesContainer.appendChild(scanningMsg);
    this._scrollToBottom();

    try {
      // 3. First attempt fast Groq AI analysis
      const groqResult = await this._queryGroqIntelligence(query);

      if (groqResult && groqResult.isRegionRequest && Number.isFinite(groqResult.lat) && Number.isFinite(groqResult.lon)) {
        scanningMsg.remove();
        const profile = this._buildProfileFromGroq(groqResult);
        await this.presentRegion(profile, groqResult.conversationalAnswer);
        return;
      }

      if (groqResult && !groqResult.isRegionRequest && groqResult.conversationalAnswer) {
        scanningMsg.remove();
        this.appendBotMessage(`
          <div class="ai-welcome-badge" style="background:rgba(0,255,170,0.15);color:#00ffaa;border-color:rgba(0,255,170,0.3);">⚡ GROQ AI INTELLIGENCE</div>
          <p style="font-size: 13px; line-height: 1.5; color: var(--text-primary); margin-top: 6px;">
            ${this._escapeHtml(groqResult.conversationalAnswer)}
          </p>
        `);
        return;
      }

      // 4. Fallback to local resolver if Groq is unavailable
      const profile = await this._resolveRegion(regionName || query);
      scanningMsg.remove();

      if (profile) {
        await this.presentRegion(profile);
      } else {
        this.appendBotMessage(`
          ⚠️ <strong>Region not found.</strong> I couldn't pinpoint "<em>${this._escapeHtml(query)}</em>".
          <p>Please try a city name (e.g. <em>"Bangalore"</em>, <em>"Tokyo"</em>, <em>"New York"</em>, <em>"London"</em>, <em>"San Francisco"</em>, <em>"Dubai"</em>) or GPS coordinates.</p>
        `);
      }
    } catch (error) {
      console.error('Regional intelligence query failed:', error);
      scanningMsg.remove();
      this.appendBotMessage(`
        ⚠️ <strong>Search error:</strong> ${this._escapeHtml(error.message || 'Unable to resolve region')}.
      `);
    }
  }

  async _queryGroqIntelligence(userQuery) {
    if (!this.groqApiKey) return null;

    const systemPrompt = `You are the God's Eye View AI Regional Intelligence Copilot, an advanced geospatial intelligence AI.
Your purpose is to assist users in exploring planet Earth, its cities, regions, airspace, and live telemetry data feeds.
The available data feeds in God's Eye View are:
- "flights": Live Commercial & Regional Flights (OpenSky Network ADS-B)
- "weather": Real-time Atmospheric Radar, Cloud Cover & Precipitation (NOAA GFS)
- "wind": Dynamic Vector Wind Particle Currents
- "satellites": Real-time Orbital Tracking of Satellites (ISS, Starlink, Earth observation)
- "traffic": Road Network Flow & Highway Congestion (Overpass / OpenStreetMap)
- "local-firms": Satellite Wildfire & Thermal Hotspot Detections (NASA FIRMS)
- "earthquakes": Live Global Seismic Activity & Fault Lines (USGS)
- "cctv": Real-Time Municipal & Highway Traffic CCTV Streams (Video feeds, Optical CV perception)
- "radio": Airport ATC & Maritime Radio Broadcasts
- "installations": Defense Installations & Aerospace Telemetry Facilities

When the user gives a prompt:
1. Determine if this involves a specific location or region (e.g., "Bangalore", "I want Bangalore data", "Tokyo", "London", etc.) or a general intelligence query.
2. Return a valid JSON object ONLY, with these fields:
{
  "isRegionRequest": true,
  "targetName": "Bengaluru (Bangalore)",
  "country": "Karnataka, India",
  "flag": "🇮🇳",
  "lat": 12.9716,
  "lon": 77.5946,
  "elevationM": 920,
  "cameraAltM": 24000,
  "summary": "High-altitude Deccan Plateau aerospace and technology hub. Primary airspace anchored by Kempegowda International Airport (BLR/VOBL) and space telemetry operations (ISRO).",
  "recommendedLayers": ["flights", "weather", "satellites", "traffic", "cctv", "local-firms", "earthquakes"],
  "landmarks": [
    { "name": "Kempegowda Int'l Airport (BLR)", "lat": 13.1986, "lon": 77.7066, "alt": 1400 },
    { "name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5907, "alt": 650 },
    { "name": "UB City & CBD", "lat": 12.9716, "lon": 77.5960, "alt": 550 }
  ],
  "conversationalAnswer": "I have acquired Bengaluru (Bangalore). The 3D globe is navigating to the Deccan Plateau. Here are the live telemetry streams ready for activation."
}

If the user is asking a conversational question:
{
  "isRegionRequest": false,
  "conversationalAnswer": "Detailed answer explaining the topic or intelligence question..."
}
Do not include any text outside the JSON object.`;

    try {
      const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.groqApiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: this.groqModel || DEFAULT_GROQ_MODEL,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userQuery },
          ],
          temperature: 0.1,
          response_format: { type: 'json_object' },
        }),
      });

      if (!res.ok) {
        console.warn('Groq API error status:', res.status);
        return null;
      }

      const data = await res.json();
      const content = data?.choices?.[0]?.message?.content;
      if (!content) return null;
      return JSON.parse(content);
    } catch (e) {
      console.warn('Groq query failed:', e);
      return null;
    }
  }

  _buildProfileFromGroq(groqResult) {
    const rawName = groqResult.targetName || 'Region Target';
    const cleanKey = rawName.toLowerCase().replace(/[^a-z0-9]/g, '');

    // Check if we have hand-tuned high-res landmarks for this city (like Bangalore!)
    let matchedProfile = null;
    for (const [key, p] of Object.entries(REGION_PROFILES)) {
      if (p.aliases.some((a) => cleanKey.includes(a.replace(/[^a-z0-9]/g, '')))) {
        matchedProfile = p;
        break;
      }
    }

    if (matchedProfile) {
      return {
        ...matchedProfile,
        summary: groqResult.summary || matchedProfile.summary,
      };
    }

    // Build dynamic profile from Groq
    const landmarks = Array.isArray(groqResult.landmarks)
      ? groqResult.landmarks
          .filter((l) => l && l.name && Number.isFinite(l.lat) && Number.isFinite(l.lon))
          .map((l) => ({
            name: l.name,
            lat: l.lat,
            lon: l.lon,
            alt: Number.isFinite(l.alt) && l.alt > 0 ? l.alt : 750,
            pitch: -25,
            heading: 0,
          }))
      : [];

    return {
      id: cleanKey || 'custom-region',
      name: groqResult.targetName || 'Region Target',
      country: groqResult.country || 'Global Sector',
      flag: groqResult.flag || '🌐',
      coordinates: { lat: groqResult.lat, lon: groqResult.lon },
      elevation: Number.isFinite(groqResult.elevationM) ? `${groqResult.elevationM}m WGS84` : 'Surface WGS84',
      camera: {
        lat: groqResult.lat,
        lon: groqResult.lon,
        altitude: Number.isFinite(groqResult.cameraAltM) ? groqResult.cameraAltM : 22000,
        pitch: -28,
        heading: 15,
      },
      summary: groqResult.summary || `Spatial intelligence sector centered at ${groqResult.lat.toFixed(4)}°, ${groqResult.lon.toFixed(4)}°.`,
      landmarks,
      availableDataFeeds: GLOBAL_DATA_FEEDS,
    };
  }

  _extractRegionName(text) {
    let clean = text.toLowerCase()
      .replace(/i want\s+/gi, '')
      .replace(/give me\s+/gi, '')
      .replace(/show me\s+/gi, '')
      .replace(/find me\s+/gi, '')
      .replace(/what data do you have for\s+/gi, '')
      .replace(/what data for\s+/gi, '')
      .replace(/can you show\s+/gi, '')
      .replace(/telemetry of\s+/gi, '')
      .replace(/telemetry for\s+/gi, '')
      .replace(/\btelemetry\b/gi, '')
      .replace(/data of\s+/gi, '')
      .replace(/data for\s+/gi, '')
      .replace(/data in\s+/gi, '')
      .replace(/\bdata\b/gi, '')
      .replace(/fly to\s+/gi, '')
      .replace(/go to\s+/gi, '')
      .replace(/take me to\s+/gi, '')
      .replace(/\bregion\b/gi, '')
      .replace(/\bcity\b/gi, '')
      .trim();

    return clean;
  }

  async _resolveRegion(query) {
    const q = query.toLowerCase().replace(/[^a-z0-9]/g, '');

    // Match built-in profiles first
    for (const [key, profile] of Object.entries(REGION_PROFILES)) {
      if (profile.aliases.some((alias) => alias.replace(/[^a-z0-9]/g, '') === q)) {
        return profile;
      }
      if (profile.name.toLowerCase().includes(query.toLowerCase())) {
        return profile;
      }
    }

    // Loose match
    for (const [key, profile] of Object.entries(REGION_PROFILES)) {
      if (profile.aliases.some((alias) => query.toLowerCase().includes(alias))) {
        return profile;
      }
    }

    // Dynamic Geocoder Fallback
    if (this.placeSearch && typeof this.placeSearch.geocode === 'function') {
      try {
        const outcome = await this.placeSearch.geocode(query);
        const place = outcome?.place;
        if (place && Number.isFinite(place.lat) && Number.isFinite(place.lng)) {
          return this._synthesizeProfile(place.label || query, place.lat, place.lng);
        }
      } catch (e) {
        console.warn('PlaceSearch geocode error:', e);
      }
    }

    // Direct Photon Fallback (keyless global geocoder)
    try {
      const res = await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=1`);
      if (res.ok) {
        const data = await res.json();
        const feat = data?.features?.[0];
        if (feat && feat.geometry && feat.geometry.coordinates) {
          const lon = feat.geometry.coordinates[0];
          const lat = feat.geometry.coordinates[1];
          const props = feat.properties || {};
          const label = [props.name, props.city, props.state, props.country].filter(Boolean).join(', ');
          return this._synthesizeProfile(label || query, lat, lon);
        }
      }
    } catch {
      /* ignore network fallback errors */
    }

    return null;
  }

  _synthesizeProfile(name, lat, lon) {
    return {
      id: name.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      name,
      country: 'Global Region',
      flag: '🌐',
      coordinates: { lat, lon },
      elevation: 'WGS84 Surface',
      camera: {
        lat,
        lon,
        altitude: 25000,
        pitch: -30,
        heading: 0,
      },
      summary: `Geospatial coordinates centered at ${lat.toFixed(4)}°, ${lon.toFixed(4)}°. Live global satellite, airspace, atmospheric and seismic feeds mapped to this sector.`,
      landmarks: [],
      availableDataFeeds: GLOBAL_DATA_FEEDS,
    };
  }

  /**
   * Presents the region dossier in the AI Bot, flies the globe to the area,
   * and renders the interactive data selector.
   */
  async presentRegion(profile, conversationalIntro = null) {
    this.currentRegion = profile;

    // 1. Immediately fly the Cesium camera in the background
    this.flyToRegionCamera(profile);

    // 2. Update active region indicator bar
    if (this.activeRegionBar) {
      this.activeRegionBar.hidden = false;
    }
    if (this.activeRegionName) {
      this.activeRegionName.textContent = profile.name;
    }
    this._updateActiveBar();

    // 3. Build the rich interactive dossier HTML
    const feedsHtml = profile.availableDataFeeds
      .map((feed) => {
        // Resolve real layer id (handling alt layer IDs)
        const realLayerId = this._resolveRealLayerId(feed.layerId, feed.altLayerId);
        const isStreaming = this.dataManager?.isEffectivelyEnabled?.(realLayerId) ?? false;

        return `
          <div class="ai-feed-row ${isStreaming ? 'active' : ''}" data-layer-id="${realLayerId}" role="button" tabindex="0" title="Tap to toggle live telemetry">
            <div class="ai-feed-checkbox-wrap">
              <input
                type="checkbox"
                class="ai-feed-cb"
                data-layer-id="${realLayerId}"
                ${isStreaming || feed.defaultActive ? 'checked' : ''}
                style="display:none;"
              />
              <div class="ai-switch ${isStreaming || feed.defaultActive ? 'checked' : ''}">
                <div class="ai-switch-handle"></div>
              </div>
            </div>
            <div class="ai-feed-content">
              <div class="ai-feed-meta-line">
                <span class="ai-feed-name">${feed.icon} ${this._escapeHtml(feed.name)}</span>
                <span class="ai-feed-status ${isStreaming ? 'streaming' : 'available'}">
                  ${isStreaming ? '● STREAMING' : '○ TAP TO STREAM'}
                </span>
              </div>
              <div class="ai-feed-desc">${this._escapeHtml(feed.description)}</div>
            </div>
          </div>
        `;
      })
      .join('');

    const landmarksHtml = (profile.landmarks || [])
      .map(
        (lm) => `
          <button
            type="button"
            class="ai-landmark-btn"
            data-landmark-name="${this._escapeHtml(lm.name)}"
            data-landmark-lat="${lm.lat}"
            data-landmark-lon="${lm.lon}"
            data-landmark-alt="${lm.alt}"
            data-landmark-pitch="${lm.pitch}"
            data-landmark-heading="${lm.heading || 0}"
          >
            📍 ${this._escapeHtml(lm.name)}
          </button>
        `
      )
      .join('');

    const cardHtml = `
      <div class="ai-dossier">
        ${
          conversationalIntro
            ? `
          <div class="ai-groq-dossier-intro">
            <span class="ai-groq-pill">⚡ GROQ DISPATCH</span>
            <span class="ai-groq-text">${this._escapeHtml(conversationalIntro)}</span>
          </div>
        `
            : ''
        }
        <div class="ai-target-header">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <div class="ai-target-kicker">🎯 TARGET ACQUIRED · GLOBE LOCKED</div>
            <button type="button" class="ai-fullscreen-map-btn" data-action="toggle-fullscreen-map" title="Switch between Fullscreen 2D Flat Map and 3D Globe">
              🗺️ FULLSCREEN MAP
            </button>
          </div>
          <div class="ai-target-name">${profile.flag} ${this._escapeHtml(profile.name)}</div>
          <div class="ai-target-geo">
            ${profile.coordinates.lat.toFixed(4)}° N, ${profile.coordinates.lon.toFixed(4)}° E · Elevation: ${profile.elevation}
          </div>
        </div>

        <p class="ai-dossier-summary">${this._escapeHtml(profile.summary)}</p>

        <div class="ai-feeds-header">
          <span class="ai-feeds-title">AVAILABLE LIVE DATA FEEDS:</span>
          <span class="ai-feeds-badge">${profile.availableDataFeeds.length} FEEDS DISCOVERED</span>
        </div>

        <div class="ai-preset-chips">
          <button type="button" class="ai-preset-btn" data-preset-filter="all">⚡ ALL ON</button>
          <button type="button" class="ai-preset-btn" data-preset-filter="cctv-traffic">📹 CCTV + TRAFFIC</button>
          <button type="button" class="ai-preset-btn" data-preset-filter="airspace-weather">✈️ AIR + WEATHER</button>
          <button type="button" class="ai-preset-btn" data-preset-filter="clear">✕ ALL OFF</button>
        </div>

        <div class="ai-feeds-list">
          ${feedsHtml}
        </div>

        <div class="ai-feed-actions">
          <button type="button" class="ai-btn-activate" data-batch-action="activate-selected">
            ⚡ ACTIVATE SELECTED
          </button>
          <button type="button" class="ai-btn-subaction" data-batch-action="activate-all">
            ✓ SELECT ALL
          </button>
          <button type="button" class="ai-btn-subaction" data-batch-action="clear-all">
            ✕ CLEAR
          </button>
        </div>

        ${
          landmarksHtml
            ? `
          <div class="ai-landmarks-header">LOCAL POINTS OF INTEREST (CLICK TO INSPECT):</div>
          <div class="ai-landmarks-chips">
            ${landmarksHtml}
          </div>
        `
            : ''
        }
      </div>
    `;

    this.appendBotMessage(cardHtml);
  }

  _resolveRealLayerId(primaryId, altId) {
    if (this.dataManager?.layers?.has(primaryId)) {
      return primaryId;
    }
    if (altId && this.dataManager?.layers?.has(altId)) {
      return altId;
    }
    return primaryId;
  }

  /**
   * Smooth camera flight to the queried region in the 3D globe.
   * Clamps altitude to close tactical range so city terrain fills the full screen!
   */
  flyToRegionCamera(profile) {
    if (!this.viewer) return;

    const { lat, lon, altitude = 2800, pitch = -38, heading = 0 } = profile.camera;
    const targetAltitude = Math.min(altitude, 3200);
    const Cesium = resolveCesium();

    try {
      this.viewer.camera.cancelFlight();
      if (Cesium?.Cartesian3?.fromDegrees && Cesium?.Math?.toRadians) {
        this.viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(lon, lat, targetAltitude),
          orientation: {
            heading: Cesium.Math.toRadians(heading),
            pitch: Cesium.Math.toRadians(pitch),
            roll: 0,
          },
          duration: 2.2,
        });
      } else if (this.viewer?.camera?.flyTo) {
        this.viewer.camera.flyTo({
          destination: { x: lon, y: lat, z: targetAltitude },
          duration: 2.2,
        });
      }
    } catch (e) {
      console.warn('Cesium flyTo error:', e);
    }
  }

  flyToLandmarkTarget(lat, lon, alt, pitch, heading, name) {
    if (!this.viewer) return;

    const Cesium = resolveCesium();
    try {
      this.viewer.camera.cancelFlight();
      if (Cesium?.Cartesian3?.fromDegrees && Cesium?.Math?.toRadians) {
        this.viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(lon, lat, alt || 750),
          orientation: {
            heading: Cesium.Math.toRadians(heading || 0),
            pitch: Cesium.Math.toRadians(pitch || -25),
            roll: 0,
          },
          duration: 2.0,
        });
      } else if (this.viewer?.camera?.flyTo) {
        this.viewer.camera.flyTo({
          destination: { x: lon, y: lat, z: alt || 750 },
          duration: 2.0,
        });
      }
      this.appendBotMessage(`🎯 <strong>Camera centered on ${this._escapeHtml(name)}.</strong> Altitude: ${alt}m.`);
    } catch (e) {
      console.warn('Landmark flight error:', e);
    }
  }

  flyToFullGlobe() {
    if (!this.viewer) return;
    const Cesium = resolveCesium();
    try {
      this.viewer.camera.cancelFlight();
      if (Cesium?.Cartesian3?.fromDegrees && Cesium?.Math?.toRadians) {
        this.viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(0, 20, 18000000),
          orientation: {
            heading: 0,
            pitch: Cesium.Math.toRadians(-90),
            roll: 0,
          },
          duration: 2.5,
        });
      } else if (this.viewer?.camera?.flyTo) {
        this.viewer.camera.flyTo({
          destination: { x: 0, y: 20, z: 18000000 },
          duration: 2.5,
        });
      }
    } catch (e) {
      console.warn('Full globe flight error:', e);
    }
  }

  /**
   * Toggle a single data layer on the Cesium globe.
   */
  async setLayerState(layerId, shouldEnable) {
    if (!this.dataManager) return;

    try {
      await this.dataManager.setEnabled(layerId, shouldEnable, { origin: 'user' });
      this._syncCheckboxState(layerId, shouldEnable);
      this._updateActiveBar();
    } catch (e) {
      console.warn(`Failed to set layer ${layerId} to ${shouldEnable}:`, e);
    }
  }

  /**
   * Activates all checked layers in the current dossier.
   */
  async activateSelectedFeeds() {
    if (!this.messagesContainer) return;
    const checkedBoxes = [
      ...this.messagesContainer.querySelectorAll('.ai-feed-cb:checked'),
    ];

    if (!checkedBoxes.length) {
      this.appendBotMessage(`ℹ️ No feeds currently checked. Select one or more feeds above to activate.`);
      return;
    }

    const activatedNames = [];
    for (const cb of checkedBoxes) {
      const layerId = cb.dataset.layerId;
      await this.setLayerState(layerId, true);
      const row = cb.closest('.ai-feed-row');
      const name = row?.querySelector('.ai-feed-name')?.textContent || layerId;
      activatedNames.push(name.trim());
    }

    this.appendBotMessage(`
      ⚡ <strong>Telemetry feeds streaming live on the 3D globe:</strong>
      <div style="font-family: var(--font-mono); font-size: 11px; margin-top: 6px; color: #00ffaa;">
        ${activatedNames.map((n) => `✓ ${this._escapeHtml(n)}`).join('<br>')}
      </div>
    `);
  }

  /**
   * Selects all feeds and enables them.
   */
  async activateAllFeeds() {
    if (!this.messagesContainer) return;
    const checkboxes = [...this.messagesContainer.querySelectorAll('.ai-feed-cb')];
    checkboxes.forEach((cb) => (cb.checked = true));
    await this.activateSelectedFeeds();
  }

  /**
   * Clears and disables all feeds.
   */
  async clearAllFeeds() {
    if (!this.messagesContainer) return;
    const checkboxes = [...this.messagesContainer.querySelectorAll('.ai-feed-cb')];
    for (const cb of checkboxes) {
      cb.checked = false;
      const layerId = cb.dataset.layerId;
      await this.setLayerState(layerId, false);
    }
    this.appendBotMessage(`✕ All regional telemetry feeds cleared from the globe.`);
  }

  promptVoiceInput() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      this.appendBotMessage(`🎙️ Voice recognition not supported in this browser. Please type your query in the text box below.`);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;

      this.appendBotMessage(`🎙️ <em>Listening for regional destination or query... Speak now.</em>`);

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          this.handleUserQuery(transcript);
        }
      };

      recognition.onerror = (event) => {
        this.appendBotMessage(`🎙️ Voice error: ${event.error}. Please type your query.`);
      };

      recognition.start();
    } catch (e) {
      this.appendBotMessage(`🎙️ Voice recognition could not be started: ${e.message}`);
    }
  }
}

/** Global singleton instance */
let aiBotInstance = null;

export function initAiBot({ viewer, styleManager, dataManager, placeSearch, scene }) {
  if (aiBotInstance) return aiBotInstance;
  aiBotInstance = new AiBotController({
    viewer,
    styleManager,
    dataManager,
    placeSearch,
    scene,
  });
  window._gevAiBot = aiBotInstance;
  return aiBotInstance;
}

export function getAiBot() {
  return aiBotInstance;
}
