# Flight-Simulation-3D
An advanced 3D flight dynamics, aerospace telemetry, and accident reconstruction suite built with WebGL (Three.js), Python, and Quantum Sensing models.

## 🚀 Key Features

### 1. Interactive 3D Flight Simulation (`index.html`)
* **3D Aircraft Model**: Integrated **C-27J Spartan | Broken Arrow** (`.glb`) with high-resolution PBR textures, camouflage livery, and realistic dimensions.
* **Capital City International Airport (KCAP)**:
  * Full runway 09L with approach lighting systems (ALS) strobes, taxiway network, modern curved terminal, jetways, and radar tower.
  * Metropolitan skyscraper district, suspension bay bridge, moving highway traffic, dynamic river, and cumulus clouds.
* **Dual Simulation Modes**:
  * 🛫 **Normal Pattern Flight**: Autonomous closed-loop pattern circuit (Takeoff roll, rotation, climb, crosswind, downwind cruise, base turn, ILS glideslope approach, flare, and rollout).
  * 💥 **Crash Investigation Mode**: Historical Florida crash scenario of N722BD at FL350 with convective storm clouds, Mach tuck onset, 506 kts overspeed, -58,315 fpm spiral dive, and 3D altitude drop-curtains.
* **360° Mouse Look & Camera Directors**:
  * **Chase 360° View**: Spherical orbit around the aircraft from any angle with mouse wheel zoom.
  * **Cockpit POV**: Pilot perspective with glass HUD avionics overlay.
  * **Tower & Skyline Views**: Air traffic control tower cab and skyscraper panoramic views.
* **Test Flight & Mission Debriefing**:
  * Automated pre-flight checklist.
  * Dynamic **"Stop in the task"** button.
  * Chronological flight debriefing log with verified flight defaults.

### 2. N722BD Learjet 60 Crash Reconstruction & Quantum Forensics
* Forensic analysis of 15,059 granular ADS-B data points from the fatal accident on November 1, 2026.
* **Root Cause Diagnostics**:
  * Pitot-static probe icing and false airspeed indications.
  * Narrow "Coffin Corner" and transonic Mach Tuck ($M > 0.81$ up to $M 0.88$, 506 kts).
  * Aerodynamic hinge moment control freeze and aileron reversal.
  * Graveyard spiral divergence and catastrophic structural overload ($> +6\text{G}$).
* **Quantum Sensing Simulation**:
  * $^{87}\text{Rb}$ cold-atom matter-wave interferometry ($Q\text{-IMU}$) operating inside the pressure hull with zero pitot ports, completely immune to airframe icing.
  * Quantum Kalman Filtering (QKF) and anomaly detection identifying the divergence 42 seconds before aerodynamic failure.

### 3. Additional Aerospace Simulations
* **F-16 Fighting Falcon**: High-G supersonic 6-DOF simulation (`f16_3d_simulation.html`).
* **F-4N Phantom II**: Transonic carrier fighter simulation (`f4n_3d_simulation.html`).
* **RocketPy Calisto Rocket**: 6-DOF suborbital rocket trajectory with launch rail physics (`flight_3d_simulation.html`).

---

## 💻 Running the Simulation

Run a lightweight local web server to stream the 3D model:

```bash
# Start local static server
python3 -m http.server 8088

# Open in your browser
open http://localhost:8088/index.html
```

Or open `index.html` directly in any modern browser with WebGL enabled.

---

## 🛠 Project Structure

```text
Flight-Simulation-3D/
├── index.html                           # Master 3D Flight Simulation & C-27J Spartan
├── 3D_city_and_airport_simulation.html  # Mirror of master simulation
├── n722bd_3d_crash_reconstruction.html  # Standalone 3D Crash Reconstruction
├── c-27j_spartan__broken_arrow.glb      # Binary glTF 3D Aircraft Model
├── recreate_n722bd_crash.py             # Telemetry parsing & Quantum State Estimation
├── build_photorealistic_reconstruction.py # 3D Trajectory builder
├── f16_3d_simulation.html               # F-16 6-DOF Flight Visualizer
├── f4n_3d_simulation.html               # F-4N Flight Visualizer
├── flight_3d_simulation.html            # RocketPy 6-DOF Rocket Visualizer
├── data/                                # Telemetry datasets (JSON, CSV, KML)
├── models/                              # 3D assets
└── plots/                               # Flight telemetry analysis plots
```

---

## 📜 Credits & Licensing
* **C-27J Spartan Model**: "C-27J Spartan | Broken Arrow" by [xlisov](https://sketchfab.com/xlisov74), licensed under [CC Attribution-NonCommercial (CC BY-NC 4.0)](http://creativecommons.org/licenses/by-nc/4.0/).
* **JSBSim**: Flight dynamics engine licensed under LGPL v2.1.
* **RocketPy**: Trajectory simulation library.
