from rocketpy import Environment, GenericMotor, Rocket, Flight

from math import pi

env = Environment(
    latitude = 28.61,
    longitude = -80.6,
    elevation = 0,
 )

env.set_atmospheric_model(type = "standard_atmosphere")

env.plots.atmospheric_model()

rocket = Rocket(
    radius = 0.157 / 2.0,
    mass = 22.6, 
    inertia = (19.403, 19.403, 0.111),
    power_off_drag = "power_off_drag.csv",
    power_on_drag = "power_on_drag.csv",
    center_of_mass_without_motor = 1.44,
    coordinate_system_orientation = "nose_to_tail",
)

rocket.add_nose(
    length = 0.381,
    kind = "ogive", 
    position = 0, 
)

fin_points = [(0.0, 0.0), (0.127, 0.14), (0.254, 0.14), (0.305, 0.0)]

rocket.add_free_form_fins(
    n = 4,
    shape_points = fin_points,
    position = 3.11,
    cant_angle = 0,
    radius = 0.178 / 2.0, 
    name = "Fins",
)

rocket.set_rail_buttons(
    upper_button_position = 2.31,
    lower_button_position = 3.37,
    angular_position = 0,
)

cd = 0.8
r = 0.762 / 2.0

rocket.add_parachute(
    name = "Drogue",
    cd_s = cd * pi * r**2, 
    # cd * pi * r^2
    trigger = "apogee", 
    sampling_rate = 100, # 100 times per second
    lag = 0.1,
)

m = GenericMotor.load_from_eng_file(
    "Motor.eng"
)

rocket.add_motor(
    motor = m, 
    position = 3.47,
)

flight = Flight(
    rocket = rocket,
    environment = env,
    rail_length = 1,
    inclination = 30,
    heading = 90,
)

rocket.draw()

flight.plots.trajectory_3d()