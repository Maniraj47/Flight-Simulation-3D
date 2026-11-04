import os
import math
import json
import numpy as np
import jsbsim

def run_f4n_simulation():
    base = os.path.dirname(jsbsim.__file__)
    fdm = jsbsim.FGFDMExec(base)
    
    # Disable JSBSim verbose logging to stdout
    fdm.set_debug_level(0)
    
    # Load F4N model
    fdm.load_model('F4N')
    
    # Load initial conditions: on runway
    ic_path = os.path.join(base, 'aircraft', 'F4N', 'reset00.xml')
    fdm.load_ic(ic_path, False)
    
    # Runway setting: Edwards AFB Runway 04/22 (Elevation 2,302 ft ASL)
    fdm['ic/lat-gc-deg'] = 34.9055
    fdm['ic/long-gc-deg'] = -117.8836
    fdm['ic/psi-true-deg'] = 90.0  # Heading East (090)
    fdm['ic/h-agl-ft'] = 3.73
    fdm['ic/vc-kts'] = 0.0
    
    fdm.run_ic()
    
    # Start twin J79-GE-11A engines
    fdm['propulsion/engine/set-running'] = 1
    fdm['propulsion/engine[1]/set-running'] = 1
    
    # Full Afterburner (100% command with reheat)
    fdm['fcs/throttle-cmd-norm'] = 1.0
    fdm['fcs/throttle-cmd-norm[1]'] = 1.0
    
    # Brakes released for immediate takeoff roll
    fdm['fcs/left-brake-cmd-norm'] = 0.0
    fdm['fcs/right-brake-cmd-norm'] = 0.0
    
    # Initial configuration: gear down, takeoff flaps (0.5)
    fdm['gear/gear-cmd-norm'] = 1.0
    fdm['fcs/flap-cmd-norm'] = 0.5
    fdm['fcs/elevator-cmd-norm'] = 0.0
    fdm['fcs/aileron-cmd-norm'] = 0.0
    fdm['fcs/rudder-cmd-norm'] = 0.0
    
    dt = 0.01  # 100 Hz simulation rate
    fdm.set_dt(dt)
    
    total_time = 120.0  # 120 seconds flight
    steps = int(total_time / dt)
    
    telemetry_records = []
    events = [
        {"time": 0.0, "name": "Brakes Release & Full Afterburner", "desc": "Twin J79-GE-11A engines at max reheat (31,500+ lbs thrust)"},
    ]
    
    v1_recorded = False
    vr_recorded = False
    liftoff_recorded = False
    gear_up_recorded = False
    mach1_recorded = False
    
    print(f"Executing F-4N 6-DOF simulation for {total_time}s ({steps} steps)...")
    
    for step in range(steps):
        t = step * dt
        
        vc_kts = float(fdm['velocities/vc-kts'])
        alt_agl_ft = float(fdm['position/h-agl-ft'])
        pitch_deg = float(fdm['attitude/pitch-rad']) * 57.2958
        mach = float(fdm['velocities/mach'])
        
        # Flight phase control logic
        if vc_kts >= 120.0 and not v1_recorded:
            events.append({
                "time": round(t, 2),
                "name": "V1 Decision Speed",
                "desc": f"Speed: {vc_kts:.0f} kts, runway takeoff committed"
            })
            v1_recorded = True
            
        if vc_kts >= 160.0 and alt_agl_ft < 15.0:
            # Rotate nose up smoothly
            fdm['fcs/elevator-cmd-norm'] = -0.32
            phase = "ROTATION"
            if not vr_recorded:
                events.append({
                    "time": round(t, 2),
                    "name": "Vr Rotation Speed",
                    "desc": f"Airspeed: {vc_kts:.0f} kts, pulling stick back for rotation"
                })
                vr_recorded = True
        elif alt_agl_ft >= 15.0 and alt_agl_ft < 80.0:
            phase = "LIFTOFF"
            if not liftoff_recorded:
                events.append({
                    "time": round(t, 2),
                    "name": "Main Wheels Liftoff",
                    "desc": f"Speed: {vc_kts:.0f} kts, positive rate of climb established"
                })
                liftoff_recorded = True
            # Maintain initial climb attitude
            target_pitch = 14.0
            pitch_err = target_pitch - pitch_deg
            fdm['fcs/elevator-cmd-norm'] = max(-0.4, min(0.2, -0.05 - 0.02 * pitch_err))
        elif alt_agl_ft >= 80.0:
            # Retract gear & flaps
            fdm['gear/gear-cmd-norm'] = 0.0
            fdm['fcs/flap-cmd-norm'] = 0.0
            if not gear_up_recorded:
                events.append({
                    "time": round(t, 2),
                    "name": "Landing Gear & Flaps Retracted",
                    "desc": f"Altitude: {alt_agl_ft:.0f} ft, Clean configuration"
                })
                gear_up_recorded = True
                
            # Climb / acceleration pitch schedule
            if alt_agl_ft > 14000:
                target_pitch = 4.0
            elif alt_agl_ft > 8000:
                target_pitch = 7.0
            else:
                target_pitch = 14.0
                
            pitch_err = target_pitch - pitch_deg
            elev = -0.01 - 0.03 * pitch_err
            fdm['fcs/elevator-cmd-norm'] = max(-0.5, min(0.3, elev))
            
            if mach >= 1.0 and not mach1_recorded:
                events.append({
                    "time": round(t, 2),
                    "name": "Transonic Breakthrough (Mach 1.0)",
                    "desc": f"Altitude: {alt_agl_ft:.0f} ft, Speed: {vc_kts:.0f} kts (Supersonic flight)"
                })
                mach1_recorded = True
                
            if mach >= 1.0:
                phase = "SUPERSONIC_DASH"
            else:
                phase = "HIGH_RATE_CLIMB"
        else:
            phase = "TAKEOFF_ROLL"
            
        fdm.run()
        
        # Sample telemetry at 10 Hz
        if step % 10 == 0:
            alt_m = alt_agl_ft * 0.3048
            thrust_lbs = float(fdm['propulsion/engine/thrust-lbs']) + float(fdm['propulsion/engine[1]/thrust-lbs'])
            thrust_n = thrust_lbs * 4.44822
            roll_deg = float(fdm['attitude/roll-rad']) * 57.2958
            heading_deg = float(fdm['attitude/heading-true-rad']) * 57.2958
            alpha_deg = float(fdm['aero/alpha-deg'])
            beta_deg = float(fdm['aero/beta-deg'])
            q_psf = float(fdm['aero/qbar-psf'])
            q_pa = q_psf * 47.8803
            g_force = float(fdm['accelerations/n-pilot-z-norm'])
            vs_fpm = float(fdm['velocities/v-down-fps']) * -60.0
            lat = float(fdm['position/lat-gc-deg'])
            lon = float(fdm['position/long-gc-deg'])
            fuel_lbs = float(fdm['propulsion/tank[0]/contents-lbs'])
            dist_east_m = float(fdm['position/distance-from-start-lon-mt'])
            dist_north_m = float(fdm['position/distance-from-start-lat-mt'])
            gear_pos = float(fdm['gear/gear-pos-norm'])
            
            telemetry_records.append({
                "t": round(t, 2),
                "x": round(dist_east_m, 1),
                "y": round(dist_north_m, 1),
                "z": round(alt_m, 1),
                "alt_ft": round(alt_agl_ft, 1),
                "speed_kts": round(vc_kts, 1),
                "speed_ms": round(vc_kts * 0.514444, 1),
                "speed_kmh": round(vc_kts * 1.852, 1),
                "mach": round(mach, 3),
                "vs_fpm": round(vs_fpm, 0),
                "g_force": round(g_force, 2),
                "pitch": round(pitch_deg, 2),
                "roll": round(roll_deg, 2),
                "heading": round(heading_deg, 1),
                "alpha": round(alpha_deg, 2),
                "beta": round(beta_deg, 2),
                "dyn_p": round(q_pa, 0),
                "thrust_lbs": round(thrust_lbs, 0),
                "thrust_n": round(thrust_n, 0),
                "fuel_lbs": round(fuel_lbs, 1),
                "gear": round(gear_pos, 2),
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "phase": phase
            })
            
    events.append({
        "time": round(total_time, 2),
        "name": "End of Flight Profile",
        "desc": f"Final Mach: {telemetry_records[-1]['mach']:.2f}, Altitude: {telemetry_records[-1]['alt_ft']:.0f} ft"
    })
    events.sort(key=lambda x: x["time"])
    
    sim_data = {
        "metadata": {
            "aircraft_name": "McDonnell Douglas F-4N Phantom II",
            "simulation_engine": "JSBSim 6-DOF Flight Dynamics Engine",
            "engines": "2x General Electric J79-GE-11A with Afterburner",
            "empty_weight_lbs": 28000.0,
            "takeoff_weight_lbs": 41000.0,
            "fuel_capacity_lbs": 13160.0,
            "wingspan_ft": 38.4,
            "wing_area_sqft": 530.0,
            "airfield": "Edwards AFB Runway 04/22",
            "max_speed_kts": max(r['speed_kts'] for r in telemetry_records),
            "max_speed_kmh": max(r['speed_kmh'] for r in telemetry_records),
            "max_mach": max(r['mach'] for r in telemetry_records),
            "max_altitude_ft": max(r['alt_ft'] for r in telemetry_records),
            "max_altitude_m": max(r['z'] for r in telemetry_records),
            "max_g_force": max(r['g_force'] for r in telemetry_records),
            "max_thrust_lbs": max(r['thrust_lbs'] for r in telemetry_records),
            "total_downrange_km": telemetry_records[-1]['x'] / 1000.0,
            "duration": total_time
        },
        "events": events,
        "frames": telemetry_records
    }
    
    with open("f4n_telemetry_3d.json", "w") as f:
        json.dump(sim_data, f)
        
    print(f"\n=======================================================")
    print(f"F-4N 6-DOF SIMULATION COMPLETED")
    print(f"=======================================================")
    print(f"Frames recorded: {len(telemetry_records)}")
    print(f"Max Mach Achieved: {sim_data['metadata']['max_mach']:.2f} (Supersonic)")
    print(f"Max Calibrated Airspeed: {sim_data['metadata']['max_speed_kts']:.1f} kts ({sim_data['metadata']['max_speed_kmh']:.1f} km/h)")
    print(f"Max Altitude Reached: {sim_data['metadata']['max_altitude_ft']:.0f} ft ({sim_data['metadata']['max_altitude_m']:.0f} m)")
    print(f"Total Afterburning Thrust: {sim_data['metadata']['max_thrust_lbs']:.0f} lbs ({sim_data['metadata']['max_thrust_lbs']*4.44822:.0f} N)")
    print(f"Total Ground Distance Traveled: {sim_data['metadata']['total_downrange_km']:.1f} km")
    print(f"Exported: f4n_telemetry_3d.json")

if __name__ == "__main__":
    run_f4n_simulation()
