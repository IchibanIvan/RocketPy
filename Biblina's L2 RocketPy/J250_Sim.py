import numpy as np
import pandas as pd
from pathlib import Path
from rocketpy import Environment, SolidMotor, Rocket, Flight, Function
import datetime

# from rocketpy.simulation import FlightDataExporter

lat = 42.7037283
lon = -77.1911343
elev = 270.8

env = Environment(
    date = (2026, 7, 12, 14),
    timezone="America/New_York",
    latitude = lat,
    longitude = lon,
    elevation = elev
)

# Folder containing this Python file
current_folder = Path(__file__).resolve().parent

era5_file = current_folder / "era5_2026-07-12_18UTC.nc"


env.set_atmospheric_model(
    type = "reanalysis",
    file = str(era5_file),
    dictionary = "ECMWF",
)

env.max_expected_height = 2000


# HISTORICAL FLIGHT RECONSTRUCTION ONLY
#
# The ERA5 wind was reversed and empirically scaled to reproduce
# the recorded July 12 flight. Do not use these wind modifications
# to predict future flights.

profile_heights = np.linspace(
    0.0,       # 0 m ASL
    3000.0,    # safely above this rocket's apogee
    601,       # one point every 5 m
)

pressure_values = np.array([
    float(env.pressure(height))
    for height in profile_heights
])

temperature_values = np.array([
    float(env.temperature(height))
    for height in profile_heights
])

original_u_values = np.array([
    float(env.wind_velocity_x(height))
    for height in profile_heights
])

original_v_values = np.array([
    float(env.wind_velocity_y(height))
    for height in profile_heights
])

# Empirical wind calibration for reconstructing this flight
WIND_U_SCALE = 1.04
WIND_V_SCALE = 1.27

reversed_u_values = (
    -original_u_values * WIND_U_SCALE
)

reversed_v_values = (
    -original_v_values * WIND_V_SCALE
)

# Combine altitude and atmospheric values into two-column arrays.
pressure_profile = np.column_stack((
    profile_heights,
    pressure_values,
))

temperature_profile = np.column_stack((
    profile_heights,
    temperature_values,
))

reversed_u_profile = np.column_stack((
    profile_heights,
    reversed_u_values,
))

reversed_v_profile = np.column_stack((
    profile_heights,
    reversed_v_values,
))

# Create a SEPARATE environment so the original ERA5 environment
# is not overwritten.
reversed_env = Environment(
    date=(2026, 7, 12, 14),
    timezone="America/New_York",
    latitude=lat,
    longitude=lon,
    elevation=elev,
)

reversed_env.set_atmospheric_model(
    type="custom_atmosphere",
    pressure=pressure_profile,
    temperature=temperature_profile,
    wind_u=reversed_u_profile,
    wind_v=reversed_v_profile,
)

reversed_env.max_expected_height = 3000

#env.plots.atmospheric_model()
#env.info()

Lxx = 0.00015100 # kg·m² axial inertia
Lyy = 0.00131406 # transverse inertia
Lzz = 0.00131406 # transverse inertia

motor_file = current_folder / "AeroTech_J250W.eng"

j250 = SolidMotor(
    thrust_source = str(motor_file),
    dry_mass = 0.345, 
    dry_inertia = (Lyy, Lzz, Lxx),
    nozzle_radius = 0.0174752 / 2.0,
    grain_number = 2,
    grain_density = 1733.45,
    grain_outer_radius = 1.87 * 0.0254 / 2.0,
    grain_initial_inner_radius = 0.625 * 0.0254 / 2.0,
    grain_initial_height = 2.619 * 0.0254,
    grain_separation = (1.0 / 16.0) * 0.0254,
    grains_center_of_mass_position = 0.10116185,
    center_of_dry_mass_position =  0.11844842,
    nozzle_position = 0,
    # burn_time read from the .eng file
    throat_radius = 0.313 * 0.0254 / 2.0,
    coordinate_system_orientation = "nozzle_to_combustion_chamber",
    )

#j250.info()
#j250.draw()

Lxx_rocket = 1.29971576
Lyy_rocket = 0.00774450
Lzz_rocket = 1.29971576

drag_file = current_folder / "biblina_data.csv"

# left column = Mach number
# right column = drag coefficient
drag_data = pd.read_csv(
    drag_file,
    header=None,
    names=["mach", "cd"],
    encoding="utf-8-sig"
)

# Sort the rows from lowest Mach number to highest
drag_data = drag_data.sort_values("mach")

# Add a Mach 0 point using the lowest-Mach drag coefficient
if drag_data["mach"].min() > 0:
    first_cd = drag_data.iloc[0]["cd"]

    drag_data = pd.concat(
        [
            pd.DataFrame({"mach": [0.0], "cd": [first_cd]}),
            drag_data
        ],
        ignore_index=True
    )

# Empirically calibrated using the July 12 flight.
# Original aerodynamic Cd curve remains unchanged in the CSV.
DRAG_SCALE = 0.51

mach_values = drag_data["mach"].to_numpy(dtype=float)
cd_values = drag_data["cd"].to_numpy(dtype=float)

scaled_cd_values = cd_values * DRAG_SCALE

drag_curve = Function(
    np.column_stack((mach_values, scaled_cd_values)),
    inputs = "Mach Number",
    outputs = "Drag Coefficient",
    interpolation = "linear",
    extrapolation = "constant",
)

body_radius = 2.0 * 0.0254

malicious_fetus = Rocket(
    radius = body_radius,
    mass = 3.81951921,
    inertia = (Lxx_rocket, Lzz_rocket, Lyy_rocket),
    power_off_drag = drag_curve,
    power_on_drag = drag_curve,
    center_of_mass_without_motor =  0.92827591,
    coordinate_system_orientation = "tail_to_nose",
)

malicious_fetus.add_motor(j250, position = 0)

nose_length = 16.00 * 0.0254
nose_tip_position = 1.61391099

nose_cone = malicious_fetus.add_nose(
    length = nose_length,
    kind = "elliptical",
    position = nose_tip_position,
    base_radius = body_radius,
    name = "Biblina Nose Cone",
)

fin_points_in = [
    (0.0, 0.0),            # P0: forward root
    (6.25, 1.5),           # P1: leading-edge bend
    (10.75, 4.45),         # P2: upper leading corner
    (14.6, 4.75),          # P3: upper trailing corner
    (12.12, 0.0),          # P4: rear root
]

fin_points = [
    (x * 0.0254, y * 0.0254)
    for x, y in fin_points_in
]

fins = malicious_fetus.add_free_form_fins(
    n = 3,
    shape_points = fin_points,
    position = 0.31271142,
    cant_angle = 0,
    radius = 0.106 / 2.0,
    name ="Biblina Fins",
)

diameter_m = 50 * 0.0254
parachute_cd = 0.8

main_cd_s = 1.70

main = malicious_fetus.add_parachute(
    name = "Main",
    cd_s = main_cd_s,
    trigger = "apogee",
    sampling_rate = 100,
    lag = 0,
    noise = (0, 0, 0),
    radius = diameter_m / 2,
    drag_coefficient = parachute_cd,
)

rail_buttons = malicious_fetus.set_rail_buttons(
    upper_button_position = 0.5 * 0.0254,
    lower_button_position = 12.5 * 0.0254,
    angular_position = 0,
)

# malicious_fetus.draw()

RAIL_LENGTH = 3.048
RAIL_INCLINATION = 88.0
RAIL_HEADING = 240.0

urrg_flight = Flight(
    rocket = malicious_fetus,
    environment = reversed_env,
    max_time_step = 0.001,
    rail_length = RAIL_LENGTH, 
    inclination = RAIL_INCLINATION,          # Rail inclination angle (degrees from horizontal)
    heading = RAIL_HEADING,            # Launch direction (degrees from North)
)

landing_time = urrg_flight.solution[-1][0]
apogee_time = urrg_flight.apogee_time

landing_latitude = float(urrg_flight.latitude(landing_time))
landing_longitude = float(urrg_flight.longitude(landing_time))

apogee_lat = float(urrg_flight.latitude(apogee_time))
apogee_lon = float(urrg_flight.longitude(apogee_time))
apogee_elev = float(urrg_flight.apogee)

# GPS VALUES:
# Apogee: 42.7031246, -77.1925453 at 1176 m above sea level
# Landing: 42.7043755, -77.1906316

print(f"Landing coordinates: {landing_latitude:f}, {landing_longitude:f}")
print(f"Apogee coordinates: {apogee_lat:f}, {apogee_lon:f}")
print(f"Apogee elevation above sea level: {apogee_elev:f}")

print(f"Apogee time: {urrg_flight.apogee_time:.2f} s")
print(f"Landing time: {urrg_flight.t_final:.2f} s")
print(
    f"Descent time: "
    f"{urrg_flight.t_final - urrg_flight.apogee_time:.2f} s"
)
print(f"Impact velocity: {urrg_flight.impact_velocity:.2f} m/s")
print(f"Parachute events: {urrg_flight.parachute_events}")

# =========================================================
# COMPLETE FLIGHT CALIBRATION REPORT
# Place this AFTER urrg_flight = Flight(...)
# =========================================================

# The atmosphere used in the Flight:
active_env = reversed_env       # Current reversed-wind diagnostic
original_weather_env = env      # Original ERA5 reanalysis

# Recorded flight values
recorded_launch_lat = 42.7037283
recorded_launch_lon = -77.1911345

recorded_apogee_lat = 42.7031246
recorded_apogee_lon = -77.1925453
recorded_apogee_asl = 1176.0

recorded_landing_lat = 42.7043755
recorded_landing_lon = -77.1906316

recorded_apogee_time_approx = 15.28
recorded_descent_time = 139.17
recorded_descent_speed = 6.50


def horizontal_displacement(lat_1, lon_1, lat_2, lon_2):
    """Return east, north, distance and bearing from point 1 to point 2."""

    earth_radius = 6_371_000.0

    mean_latitude = np.radians((lat_1 + lat_2) / 2)

    east = (
        np.radians(lon_2 - lon_1)
        * earth_radius
        * np.cos(mean_latitude)
    )

    north = (
        np.radians(lat_2 - lat_1)
        * earth_radius
    )

    distance = np.hypot(east, north)

    bearing = (
        np.degrees(np.arctan2(east, north)) + 360
    ) % 360

    return east, north, distance, bearing


def print_wind_report(label, atmosphere, bottom_asl, top_asl):
    """Print wind samples and altitude-averaged wind."""

    print(f"\n--- {label} WIND PROFILE ---")
    print("Positive U = east; negative U = west")
    print("Positive V = north; negative V = south\n")

    sample_altitudes = np.array([
        bottom_asl,
        bottom_asl + 100,
        bottom_asl + 300,
        bottom_asl + 500,
        bottom_asl + 700,
        top_asl,
    ])

    sample_altitudes = np.unique(
        np.clip(sample_altitudes, bottom_asl, top_asl)
    )

    for altitude_asl in sample_altitudes:
        u = float(atmosphere.wind_velocity_x(altitude_asl))
        v = float(atmosphere.wind_velocity_y(altitude_asl))

        speed = np.hypot(u, v)

        toward = (
            np.degrees(np.arctan2(u, v)) + 360
        ) % 360

        wind_from = (toward + 180) % 360

        print(
            f"{altitude_asl:7.1f} m ASL | "
            f"{altitude_asl - elev:6.1f} m AGL | "
            f"U={u:6.2f} m/s | "
            f"V={v:6.2f} m/s | "
            f"Speed={speed:5.2f} m/s | "
            f"From={wind_from:6.1f}° | "
            f"Toward={toward:6.1f}°"
        )

    profile_altitudes = np.linspace(
        bottom_asl,
        top_asl,
        1000,
    )

    u_values = np.array([
        float(atmosphere.wind_velocity_x(height))
        for height in profile_altitudes
    ])

    v_values = np.array([
        float(atmosphere.wind_velocity_y(height))
        for height in profile_altitudes
    ])

    average_u = np.mean(u_values)
    average_v = np.mean(v_values)

    average_speed = np.hypot(average_u, average_v)

    average_toward = (
        np.degrees(
            np.arctan2(average_u, average_v)
        ) + 360
    ) % 360

    average_from = (average_toward + 180) % 360

    print(f"\nAverage U:       {average_u:.3f} m/s")
    print(f"Average V:       {average_v:.3f} m/s")
    print(f"Average speed:   {average_speed:.3f} m/s")
    print(f"Average from:    {average_from:.1f}°")
    print(f"Average toward:  {average_toward:.1f}°")

    return average_u, average_v


# =========================================================
# EXTRACT SIMULATION RESULTS
# =========================================================

landing_time = float(urrg_flight.solution[-1][0])
apogee_time = float(urrg_flight.apogee_time)
descent_time = landing_time - apogee_time

apogee_lat = float(
    urrg_flight.latitude(apogee_time)
)

apogee_lon = float(
    urrg_flight.longitude(apogee_time)
)

landing_lat = float(
    urrg_flight.latitude(landing_time)
)

landing_lon = float(
    urrg_flight.longitude(landing_time)
)

simulated_apogee_asl = float(urrg_flight.apogee)
simulated_apogee_agl = simulated_apogee_asl - elev

average_descent_speed = (
    simulated_apogee_agl / descent_time
)


# =========================================================
# CONFIGURATION
# =========================================================

print("\n" + "=" * 65)
print("ROCKETPY FLIGHT CALIBRATION REPORT")
print("=" * 65)

print("\n--- CONFIGURATION ---")
print(f"Drag scale:             {DRAG_SCALE:.3f}")
print(f"Body radius:            {body_radius:.4f} m")
print(f"Body diameter:          {2 * body_radius:.4f} m")
print(f"Parachute CdS:          {main_cd_s:.4f} m²")
print(f"Rail length:            {RAIL_LENGTH:.3f} m")
print(f"Rail inclination:       {RAIL_INCLINATION:.2f}°")
print(f"Rail heading:           {RAIL_HEADING:.2f}°")


# =========================================================
# TIME AND ATMOSPHERE
# =========================================================

print("\n--- ENVIRONMENT AND TIME ---")
print(f"Launch elevation:       {elev:.2f} m ASL")
print(f"Local launch time:      {active_env.local_date}")
print(f"UTC launch time:        {active_env.datetime_date}")
print(
    f"Active atmosphere:      "
    f"{active_env.atmospheric_model_type}"
)

print(
    f"Original atmosphere:    "
    f"{original_weather_env.atmospheric_model_type}"
)

print(
    f"Original ERA5 file:     "
    f"{getattr(original_weather_env, 'atmospheric_model_file', None)}"
)

print(
    f"ERA5 first time:        "
    f"{getattr(original_weather_env, 'atmospheric_model_init_date', None)}"
)

print(
    f"ERA5 last time:         "
    f"{getattr(original_weather_env, 'atmospheric_model_end_date', None)}"
)


# =========================================================
# MASS
# =========================================================

print("\n--- MODELED MASS ---")
print(
    f"Rocket without motor:   "
    f"{malicious_fetus.mass:.4f} kg"
)

print(
    f"Motor dry mass:         "
    f"{j250.dry_mass:.4f} kg"
)

print(
    f"Motor propellant mass:  "
    f"{j250.propellant_initial_mass:.4f} kg"
)

print(
    f"Loaded motor mass:      "
    f"{float(j250.total_mass(0)):.4f} kg"
)

print(
    f"Complete launch mass:   "
    f"{float(malicious_fetus.total_mass(0)):.4f} kg"
)


# =========================================================
# MOTOR
# =========================================================

print("\n--- MOTOR ---")
print(f"Burn duration:          {j250.burn_duration:.3f} s")
print(f"Total impulse:          {j250.total_impulse:.2f} N·s")
print(f"Average thrust:         {j250.average_thrust:.2f} N")
print(f"Maximum thrust:         {j250.max_thrust:.2f} N")


# =========================================================
# ASCENT
# =========================================================

print("\n--- ASCENT RESULTS ---")
print(
    f"Rail-exit velocity:     "
    f"{urrg_flight.out_of_rail_velocity:.2f} m/s"
)

print(
    f"Maximum speed:          "
    f"{urrg_flight.max_speed:.2f} m/s"
)

print(
    f"Maximum Mach:           "
    f"{urrg_flight.max_mach_number:.3f}"
)

print(f"Apogee time:            {apogee_time:.2f} s")
print(f"Apogee ASL:             {simulated_apogee_asl:.2f} m")
print(f"Apogee AGL:             {simulated_apogee_agl:.2f} m")

print(
    f"Apogee coordinates:     "
    f"{apogee_lat:.7f}, {apogee_lon:.7f}"
)


# =========================================================
# DESCENT
# =========================================================

print("\n--- DESCENT RESULTS ---")
print(f"Landing time:           {landing_time:.2f} s")
print(f"Descent time:           {descent_time:.2f} s")

print(
    f"Average descent speed:  "
    f"{average_descent_speed:.2f} m/s"
)

print(
    f"Impact velocity:        "
    f"{urrg_flight.impact_velocity:.2f} m/s"
)

print(
    f"Landing coordinates:    "
    f"{landing_lat:.7f}, {landing_lon:.7f}"
)

print(
    f"Parachute events:       "
    f"{urrg_flight.parachute_events}"
)


# =========================================================
# SIMULATED DRIFT
# =========================================================

(
    sim_east_drift,
    sim_north_drift,
    sim_drift_distance,
    sim_drift_bearing,
) = horizontal_displacement(
    apogee_lat,
    apogee_lon,
    landing_lat,
    landing_lon,
)

print("\n--- SIMULATED APOGEE-TO-LANDING DRIFT ---")
print(f"East drift:             {sim_east_drift:.1f} m")
print(f"North drift:            {sim_north_drift:.1f} m")
print(f"Drift distance:         {sim_drift_distance:.1f} m")
print(f"Drift bearing:          {sim_drift_bearing:.1f}°")


# =========================================================
# RECORDED DRIFT
# =========================================================

(
    recorded_east_drift,
    recorded_north_drift,
    recorded_drift_distance,
    recorded_drift_bearing,
) = horizontal_displacement(
    recorded_apogee_lat,
    recorded_apogee_lon,
    recorded_landing_lat,
    recorded_landing_lon,
)

print("\n--- RECORDED APOGEE-TO-LANDING DRIFT ---")
print(f"East drift:             {recorded_east_drift:.1f} m")
print(f"North drift:            {recorded_north_drift:.1f} m")
print(f"Drift distance:         {recorded_drift_distance:.1f} m")
print(f"Drift bearing:          {recorded_drift_bearing:.1f}°")

print(
    f"Effective east speed:   "
    f"{recorded_east_drift / recorded_descent_time:.3f} m/s"
)

print(
    f"Effective north speed:  "
    f"{recorded_north_drift / recorded_descent_time:.3f} m/s"
)


# =========================================================
# ERRORS AGAINST RECORDED FLIGHT
# =========================================================

(
    apogee_error_east,
    apogee_error_north,
    apogee_coordinate_error,
    _,
) = horizontal_displacement(
    recorded_apogee_lat,
    recorded_apogee_lon,
    apogee_lat,
    apogee_lon,
)

(
    landing_error_east,
    landing_error_north,
    landing_coordinate_error,
    _,
) = horizontal_displacement(
    recorded_landing_lat,
    recorded_landing_lon,
    landing_lat,
    landing_lon,
)

print("\n--- RECORDED-VERSUS-SIMULATED ERRORS ---")

print(
    f"Apogee altitude error:  "
    f"{simulated_apogee_asl - recorded_apogee_asl:+.2f} m"
)

print(
    f"Apogee-time error:      "
    f"{apogee_time - recorded_apogee_time_approx:+.2f} s "
    f"(recorded value approximate)"
)

print(
    f"Apogee position error:  "
    f"{apogee_coordinate_error:.1f} m"
)

print(
    f"  East component:       "
    f"{apogee_error_east:+.1f} m"
)

print(
    f"  North component:      "
    f"{apogee_error_north:+.1f} m"
)

print(
    f"Descent-time error:     "
    f"{descent_time - recorded_descent_time:+.2f} s"
)

print(
    f"Descent-speed error:    "
    f"{average_descent_speed - recorded_descent_speed:+.2f} m/s"
)

print(
    f"Landing position error: "
    f"{landing_coordinate_error:.1f} m"
)

print(
    f"  East component:       "
    f"{landing_error_east:+.1f} m"
)

print(
    f"  North component:      "
    f"{landing_error_north:+.1f} m"
)


# =========================================================
# WIND COMPARISON
# =========================================================

original_average_u, original_average_v = print_wind_report(
    label="ORIGINAL ERA5",
    atmosphere=original_weather_env,
    bottom_asl=elev,
    top_asl=recorded_apogee_asl,
)

active_average_u, active_average_v = print_wind_report(
    label="ACTIVE / REVERSED ERA5",
    atmosphere=active_env,
    bottom_asl=elev,
    top_asl=recorded_apogee_asl,
)

print(f"Wind U scale:           {WIND_U_SCALE:.3f}")
print(f"Wind V scale:           {WIND_V_SCALE:.3f}")

print("\n--- AVERAGE WIND COMPARISON ---")
print(
    f"Original ERA5:          "
    f"U={original_average_u:+.3f}, "
    f"V={original_average_v:+.3f} m/s"
)

print(
    f"Active atmosphere:      "
    f"U={active_average_u:+.3f}, "
    f"V={active_average_v:+.3f} m/s"
)

print(
    f"Recorded effective:     "
    f"U={recorded_east_drift / recorded_descent_time:+.3f}, "
    f"V={recorded_north_drift / recorded_descent_time:+.3f} m/s"
)

print("\n" + "=" * 65)
print("END OF REPORT")
print("=" * 65)


# urrgFlight.plots.all()

# Export trajectory to KML
# kml_file = "Phoenix_URRG_trajectory.kml"

# FlightDataExporter(urrgFlight).export_kml(
    # file_name=kml_file,
    # extrude=True,
    # altitude_mode="relativetoground",)

# print(f"KML saved here: {Path(kml_file).resolve()}")

