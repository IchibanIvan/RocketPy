import numpy as np
import pandas as pd
from rocketpy import Environment, SolidMotor, Rocket, Flight, Function


env = Environment(
    latitude=43.6532,
    longitude=-79.3832,
    elevation=76
)

weather_data = pd.read_csv("Paul's L1 RocketPy/wind_2026-07-11T15.csv")

alt = weather_data["altitude"].values
speed = weather_data["speed"].values
direction = weather_data["direction"].values

direction_rad = np.radians(direction)

wind_u = -speed * np.sin(direction_rad) 
wind_v = -speed * np.cos(direction_rad) 

wind_u_func = Function(np.column_stack((alt, wind_u)))

wind_v_func = Function(np.column_stack((alt, wind_v)))

env.set_atmospheric_model(
    type = "custom_atmosphere",
    wind_u = wind_u_func,
    wind_v = wind_v_func,
)

env.plots.atmospheric_model()
env.info()

print("ORWind weather data loaded")
print("Environment created")


motor = SolidMotor(
    thrust_source = "Paul's L1 RocketPy/AeroTech_HP-H550ST.eng",
    dry_mass = 0.140,
    dry_inertia = (0.00260, 0.00260, 0.000111),
    nozzle_radius = 0.012446,
    grain_number = 3,
    grain_density = 1880,
    grain_outer_radius = 0.0332232 / 2,
    grain_initial_inner_radius = 0.0154686 / 2,
    grain_initial_height = 0.046101,
    grain_separation = 0.0015875,
    grains_center_of_mass_position = 0.11049,
    center_of_dry_mass_position = 0.10287,
    nozzle_position = 0,
    burn_time = 0.57,
    throat_radius = 0.00622040816,
    coordinate_system_orientation = "nozzle_to_combustion_chamber",
)

print("Motor created")

rocket = Rocket(
    radius = 0.0508,
    mass = 1.497,
    inertia = (0.193465243, 0.193515502, 0.000334175),
    power_off_drag = 0.75,
    power_on_drag = 0.65,
    center_of_mass_without_motor = 0.52986,
    coordinate_system_orientation = "tail_to_nose",
)


rocket.add_motor(motor, position = 0)

print("Rocket created")

rocket.add_nose(
    length = 0.32385,
    kind = "ogive",
    position = 1.187,
)


rocket.add_trapezoidal_fins(
    n = 3,
    root_chord = 0.200025,
    tip_chord = 0.0635,
    span = 0.1063752,
    position = 0.20157,
    cant_angle = 0,
)


rocket.set_rail_buttons(
    upper_button_position = 0.4700016,
    lower_button_position = 0.0254,
    angular_position = 0,
)


rocket.add_parachute(
    name = "Main",
    cd_s = 0.4922,
    trigger = "apogee",
)


flight = Flight(
    rocket = rocket,
    environment = env,
    rail_length = 3.048,
    inclination = 86,
    heading = 35,
    max_time_step = 0.01,
)


print(f"Apogee: {flight.apogee:.1f} m")
print(f"Max Speed: {flight.max_speed:.1f} m/s")
print(f"Time to Apogee: {flight.apogee_time:.2f} s")


flight.plots.trajectory_3d()
flight.plots.linear_kinematics_data()
flight.plots.angular_kinematics_data()
flight.plots.flight_path_angle_data()
flight.plots.aerodynamic_forces()
flight.plots.stability_and_control_data()
flight.plots.energy_data()


# flight.plots.all() 
# Generates all available plots again.
# Leave it commented out if you already generated the plots above.

# flight.all_info()
# This prints detailed results and generates all plots.
# Leave it commented out unless you want the complete output.