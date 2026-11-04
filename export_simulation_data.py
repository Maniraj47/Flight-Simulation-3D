import json
import math
import numpy as np
from rocketpy import Environment, Rocket, SolidMotor, Flight
from rocketpy.simulation import FlightDataExporter

# 1. Setup Environment
env = Environment(latitude=32.990254, longitude=-106.974998, elevation=1400)
env.set_atmospheric_model(type="standard_atmosphere")

# 2. Setup Motor
motor = SolidMotor(
    thrust_source="data/motors/cesaroni/Cesaroni_M1670.eng",
    dry_mass=1.815,
    dry_inertia=(0.125, 0.125, 0.002),
    center_of_dry_mass_position=0.317,
    grains_center_of_mass_position=0.397,
    burn_time=3.9,
    grain_number=5,
    grain_separation=0.005,
    grain_density=1815,
    grain_outer_radius=0.033,
    grain_initial_inner_radius=0.015,
    grain_initial_height=0.12,
    nozzle_radius=0.033,
    throat_radius=0.011,
    interpolation_method="linear",
    nozzle_position=0,
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

# 3. Setup Rocket
rocket = Rocket(
    radius=0.0635,
    mass=14.426,
    inertia=(6.321, 6.321, 0.034),
    power_off_drag="data/rockets/calisto/powerOffDragCurve.csv",
    power_on_drag="data/rockets/calisto/powerOnDragCurve.csv",
    center_of_mass_without_motor=0,
    coordinate_system_orientation="tail_to_nose",
)
rocket.set_rail_buttons(0.0818, -0.6182, 45)
rocket.add_motor(motor, position=-1.255)
rocket.add_nose(length=0.55829, kind="vonKarman", position=1.278)
rocket.add_trapezoidal_fins(
    n=4, root_chord=0.120, tip_chord=0.040, span=0.100, position=-1.04956
)
rocket.add_tail(
    top_radius=0.0635, bottom_radius=0.0435, length=0.060, position=-1.194656
)
rocket.add_parachute(
    "main", cd_s=10.0, trigger=800, sampling_rate=105, lag=1.5, noise=(0, 8.3, 0.5)
)
rocket.add_parachute(
    "drogue",
    cd_s=1.0,
    trigger="apogee",
    sampling_rate=105,
    lag=1.5,
    noise=(0, 8.3, 0.5),
)

# 4. Simulate Flight
print("Simulating Flight...")
flight = Flight(
    rocket=rocket, environment=env, rail_length=5.2, inclination=85, heading=0
)
print("Simulation complete!")

# 5. Export KML and CSV
exporter = FlightDataExporter(flight, name="Calisto Flight 1")
exporter.export_kml("flight_simulation.kml", altitude_mode="relativeToGround")
print("Exported flight_simulation.kml")

exporter.export_data(
    "flight_telemetry.csv",
    "z",
    "vx",
    "vy",
    "vz",
    "speed",
    "acceleration",
    "mach_number",
    "dynamic_pressure",
    "angle_of_attack",
    "static_margin",
    time_step=0.1,
)
print("Exported flight_telemetry.csv")

# 6. Extract Key Events
events = [
    {"time": 0.0, "name": "Ignition & Liftoff", "desc": "Cesaroni M1670 motor ignition"},
    {"time": round(float(flight.out_of_rail_time), 2), "name": "Rail Exit", "desc": f"Velocity: {flight.out_of_rail_velocity:.1f} m/s"},
    {"time": round(float(flight.max_acceleration_time), 2), "name": "Max Acceleration", "desc": f"{flight.max_acceleration / 9.80665:.1f} G ({flight.max_acceleration:.1f} m/s²)"},
    {"time": round(float(motor.burn_time[1]), 2), "name": "Motor Burnout", "desc": "Propellant depleted"},
    {"time": round(float(flight.max_speed_time), 2), "name": "Max Speed (Vmax)", "desc": f"{flight.max_speed:.1f} m/s (Mach {flight.mach_number(flight.max_speed_time):.2f})"},
    {"time": round(float(flight.apogee_time), 2), "name": "Apogee", "desc": f"Altitude: {flight.apogee:.1f} m AGL ({flight.apogee + env.elevation:.1f} m ASL)"},
]

for trigger_time, chute in flight.parachute_events:
    deploy_time = trigger_time + chute.lag
    events.append({
        "time": round(float(deploy_time), 2),
        "name": f"{chute.name.capitalize()} Chute Deployed",
        "desc": f"Altitude: {flight.z(deploy_time):.1f} m AGL, CdS = {chute.cd_s} m²"
    })

events.append({
    "time": round(float(flight.t_final), 2),
    "name": "Ground Touchdown",
    "desc": f"Impact velocity: {abs(flight.impact_velocity):.1f} m/s at x={flight.x_impact:.1f}m, y={flight.y_impact:.1f}m"
})
events.sort(key=lambda x: x["time"])

# 7. Generate adaptive time grid for 3D animation
# High fidelity (0.05s) for ascent (0 to 30s)
# Medium fidelity (0.2s) for descent (30 to t_final)
t_ascent = np.arange(0, min(30.0, flight.t_final), 0.05)
t_descent = np.arange(30.0, flight.t_final, 0.25)
time_grid = np.unique(np.concatenate([t_ascent, t_descent, [flight.t_final]]))

# Parachute deployment times
drogue_deploy_t = None
main_deploy_t = None
for trigger_time, chute in flight.parachute_events:
    t_dep = trigger_time + chute.lag
    if chute.name.lower() == "drogue":
        drogue_deploy_t = t_dep
    elif chute.name.lower() == "main":
        main_deploy_t = t_dep

burnout_t = motor.burn_time[1]
apogee_t = float(flight.apogee_time)

telemetry_frames = []

for t in time_grid:
    t_val = float(t)
    
    # Position (ENU: x=East, y=North, z=Up)
    x = float(flight.x(t_val))
    y = float(flight.y(t_val))
    z = max(0.0, float(flight.z(t_val)))
    
    # Velocity
    vx = float(flight.vx(t_val))
    vy = float(flight.vy(t_val))
    vz = float(flight.vz(t_val))
    speed = float(flight.speed(t_val))
    
    # Acceleration
    ax = float(flight.ax(t_val))
    ay = float(flight.ay(t_val))
    az = float(flight.az(t_val))
    accel = float(flight.acceleration(t_val))
    g_force = accel / 9.80665
    
    # Quaternions: RocketPy provides e0, e1, e2, e3
    # e0 is scalar, (e1, e2, e3) is vector
    e0 = float(flight.e0(t_val))
    e1 = float(flight.e1(t_val))
    e2 = float(flight.e2(t_val))
    e3 = float(flight.e3(t_val))
    
    # Flight variables
    mach = float(flight.mach_number(t_val))
    dyn_p = float(flight.dynamic_pressure(t_val))
    thrust_val = float(motor.thrust(t_val)) if t_val <= burnout_t else 0.0
    aoa = float(flight.angle_of_attack(t_val)) if hasattr(flight, "angle_of_attack") else 0.0
    
    # Determine flight phase
    if t_val < float(flight.out_of_rail_time):
        phase = "ON_RAIL"
    elif t_val <= burnout_t:
        phase = "POWERED_BOOST"
    elif t_val < apogee_t:
        phase = "COASTING_ASCENT"
    elif drogue_deploy_t and t_val < (main_deploy_t or float(flight.t_final)):
        phase = "DROGUE_DESCENT"
    elif main_deploy_t and t_val < float(flight.t_final):
        phase = "MAIN_DESCENT"
    else:
        phase = "TOUCHDOWN"
        
    telemetry_frames.append({
        "t": round(t_val, 3),
        "x": round(x, 2),
        "y": round(y, 2),
        "z": round(z, 2),
        "vx": round(vx, 2),
        "vy": round(vy, 2),
        "vz": round(vz, 2),
        "speed": round(speed, 2),
        "accel": round(accel, 2),
        "g_force": round(g_force, 2),
        "q": [round(e0, 4), round(e1, 4), round(e2, 4), round(e3, 4)],
        "mach": round(mach, 3),
        "dyn_p": round(dyn_p, 1),
        "thrust": round(thrust_val, 1),
        "aoa": round(aoa, 2),
        "phase": phase,
    })

sim_data = {
    "metadata": {
        "rocket_name": "Calisto",
        "motor_name": "Cesaroni M1670",
        "launch_site": "Spaceport America, NM",
        "latitude": 32.990254,
        "longitude": -106.974998,
        "elevation": 1400.0,
        "rail_length": 5.2,
        "rail_inclination": 85.0,
        "rail_heading": 0.0,
        "total_mass": round(float(rocket.total_mass(0)), 2),
        "dry_mass": round(float(rocket.dry_mass), 2),
        "radius": 0.0635,
        "length": 2.5,
        "apogee_agl": round(float(flight.apogee), 2),
        "apogee_asl": round(float(flight.apogee + env.elevation), 2),
        "apogee_time": round(float(flight.apogee_time), 2),
        "max_speed": round(float(flight.max_speed), 2),
        "max_mach": round(float(flight.mach_number(flight.max_speed_time)), 2),
        "max_accel": round(float(flight.max_acceleration), 2),
        "max_g": round(float(flight.max_acceleration / 9.80665), 2),
        "flight_duration": round(float(flight.t_final), 2),
        "impact_velocity": round(float(flight.impact_velocity), 2),
    },
    "events": events,
    "frames": telemetry_frames,
}

with open("telemetry_3d.json", "w") as f:
    json.dump(sim_data, f)

print(f"Exported telemetry_3d.json with {len(telemetry_frames)} frames!")
