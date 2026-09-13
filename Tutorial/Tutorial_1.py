from math import pi

from rocketpy import Environment, GenericMotor, Rocket, Flight

import numpy as np
import pandas as pd
from rocketpy import Function

# all values should be in SI units (m, kg, s, N, Pa, rad, K, etc.)
# edit - Preferences - units to change the default units

env = Environment(
    latitude = 28.61,
    longitude = -80.6,
    elevation = 0,
)

# env.set_atmospheric_model(type = "standard_atmosphere")

weather_data = pd.read_csv("Tutorial/Wind.csv")
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

print("Environment created")

rocket = Rocket(
    radius = 0.157/2.0,
    mass = 22.6, # dry mass
    inertia = (19.403, 19.403, 0.111),
    # transverse, transverse, inertia around the rocket's long axis
    # Longitudinal moment of inertia
    # Rotational moment of inertia 
    # flight Simulations, plot/export
    # dummy motor
    # Longitudinal & rotational moment of inertia

    power_off_drag = "Tutorial/power_off_drag.csv",
    power_on_drag = "Tutorial/power_on_drag.csv",
    # Values in drag curve before burnout for power_on_drag
    # then burnout to apogee for power_off_drag

    center_of_mass_without_motor = 1.44,
    coordinate_system_orientation = "nose_to_tail",
)

motor = GenericMotor.load_from_eng_file(
    "Tutorial/AeroTech_N4000W-PS.eng",
)

# motor.info()

rocket.add_motor(
    motor = motor,
    position = 3.47, # nozzle exit from the tip of the rocket
)

rocket.add_nose(
    length = 0.381,
    kind = "ogive",
    position = 0,
)

fin_points = [
    (0.0, 0.0),            # P0: forward root
    (0.127, 0.140),        # P1: leading-edge bend
    (0.254, 0.140),        # P2: upper leading corner
    (0.305, 0.000),        # P3: upper trailing corner
]

rocket.add_free_form_fins(
    n = 4,
    shape_points = fin_points,
    position = 3.11,
    cant_angle = 0,
    radius = 0.178 / 2.0,
    name ="Tutorial Fins",
)

cannard_points = [
    (0.000, 0.000),   # forward root
    (0.025, 0.030),   # outer tip
    (0.025, 0.000),   # rear root
]

rocket.add_free_form_fins(
    n = 2,
    shape_points = cannard_points,
    position = 0.432,
    cant_angle = 0,
    radius = 0.157 / 2.0,
    name ="Cannard Fins",
)

rocket.set_rail_buttons(
    upper_button_position = 2.31,
    lower_button_position = 3.37,
    angular_position = 0,
)

Cd_main = 0.8
r_main = 2.29 / 2.0

rocket.add_parachute(
    name = "Main",
    cd_s = Cd_main * pi * r_main**2, # Cd * pi * r^2
    trigger = 457,
    sampling_rate=100,
    lag=0.01,
)

Cd_drogue = 0.8
r_drogue = 0.762 / 2.0

rocket.add_parachute(
    name = "Drogue",
    cd_s = Cd_drogue * pi * r_drogue**2,
    trigger = "apogee",
    sampling_rate=100,
    lag=0.01,
)

flight = Flight(
    rocket = rocket, # rocket object name
    environment = env, # environment object name
    rail_length = 1,
    inclination = 90, # degrees
    # OpenRocket angle is measured away from vertical
    # RocketPy inclination is measured from the horizontal
    heading = 90,
    # RocketPy:
    # 0°   = North
    # 90°  = East
    # 180° = South
    # 270° = West
)

print(f"Apogee: {flight.apogee:.1f} m")
print(f"Time to apogee: {flight.apogee_time:.2f} s")
print(f"Landing time: {flight.t_final:.2f} s")

flight.plots.trajectory_3d()
flight.z.plot()
flight.speed.plot() 
flight.plots.linear_kinematics_data()
flight.plots.angular_kinematics_data()
flight.plots.flight_path_angle_data()
flight.plots.aerodynamic_forces()
flight.plots.stability_and_control_data()
flight.plots.energy_data()


# flight.all_info()