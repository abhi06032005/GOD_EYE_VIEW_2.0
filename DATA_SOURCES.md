# SentinelAI — Data Sources, Licensing, and Attributions

SentinelAI processes only public, anonymized, and telemetry data for situational awareness, following strict privacy and open data practices.

| Source | Domain | Protocol / Format | License & Terms | Attribution & Link |
| :--- | :--- | :--- | :--- | :--- |
| **OpenSky Network** | Civilian Aviation | REST / JSON | CC BY-NC-SA 4.0 (Non-commercial research) | [OpenSky Network](https://opensky-network.org/) |
| **adsb.lol** | Aircraft ADS-B / Military | REST / JSON | Open Database License (ODbL) / Public | [adsb.lol](https://adsb.lol/) |
| **USGS Earthquake Hazards** | Global Seismology | GeoJSON / REST | Public Domain (USGS) | [USGS Earthquake API](https://earthquake.usgs.gov/) |
| **AISStream** | Maritime AIS Telemetry | WebSocket / JSON | AISStream Free Tier Terms | [AISStream.io](https://aisstream.io/) |
| **Open-Meteo** | Atmospheric & Weather | REST / JSON | CC BY 4.0 | [Open-Meteo](https://open-meteo.com/) |
| **Caltrans & TxDOT** | Highway Traffic Cameras | HLS / MJPEG / Static | Public State DOT Feeds | Caltrans / Texas DOT Open Data |
| **OpenStreetMap** | Maritime / Aero Geofencing | Overpass API / GeoJSON | Open Database License (ODbL) 1.0 | [OpenStreetMap Contributors](https://www.openstreetmap.org/) |
| **God's Eye View** | 3D Globe Visual Engine | CesiumJS / glTF | MIT License | Copyright (c) 2026 Bilawal Sidhu |

---

## Data Privacy & Public Safety Notice
SentinelAI does NOT ingest or store personally identifiable information (PII). Traffic camera processing extracts spatial bounding boxes and counts (`car`, `truck`, `person`, `bus`) directly in-memory and discards image frames immediately after inference.
