from math import pi
from rocketpy import Environment, GenericMotor, Rocket, Flight, MonteCarlo

from rocketpy.stochastic import (
    StochasticEnvironment,
    StochasticRocket,
    StochasticFlight,
    StochasticNoseCone, # added these two as well
    StochasticTrapezoidalFins,
)


env = Environment(
    latitude = 28.61,
    longitude = -80.6,
    elevation = 0,
)

env.set_atmospheric_model(type = "standard_atmosphere")

rocket = Rocket(
    radius = 0.102 / 2.0,
    mass = 1.126, 
    inertia = (0.204, 0.204, 0.004),
    power_off_drag = 0.75,
    power_on_drag = 0.65, 
    center_of_mass_without_motor = 0.88,
    coordinate_system_orientation = "nose_to_tail",
)

nose = rocket.add_nose(
    length = 0.324,
    kind = "ogive",
    position = 0,
)

fin_points = [(0.0,0.0) , (0.0381,0.152) , (0.114,0.152) , (0.146,0.0)]

#fins = rocket.add_free_form_fins(
#    n = 3,
#    shape_points = fin_points,
#    position = 1.26,
#    cant_angle = 0,
#    radius = 0.102 / 2.0,
#    name = "Fins",
#)

m = 0.0254 # in to m

fins = rocket.add_trapezoidal_fins(
    n = 3,
    root_chord = 5.75 * m,
    tip_chord = 3 * m,
    span = 6 * m,
    sweep_length = 1.5 * m,
    position = (55.75 - 6) * m,
    cant_angle = 0
)

rail_buttons = rocket.set_rail_buttons(
    upper_button_position = 0.845,
    lower_button_position = 1.287,
    angular_position = 0,
)

cd = 0.8
rd = 0.305 / 2.0
rm = 0.914 / 2.0

drogue = rocket.add_parachute(
    name = "Drogue",
    cd_s = cd * pi * rd**2,
    trigger = "apogee",
    sampling_rate = 100,
    lag = 0.1, 
)

main = rocket.add_parachute(
    name = "Main",
    cd_s = cd * pi * rm**2,
    trigger = 150,
    sampling_rate = 100, 
    lag = 0.1,
)

motor = GenericMotor.load_from_eng_file(
    "RocketPy Monte Carlo Sim - Ivan Bono/AeroTech_H148R.eng"
)

rocket.add_motor(
    motor = motor,
    position = 1.42,
)

flight = Flight(
    rocket = rocket,
    environment = env, 
    rail_length = 1,
    inclination = 88,
    heading = 90,
)

stochastic_env = StochasticEnvironment(
    environment = env,
)

stochastic_rocket = StochasticRocket(
    rocket = rocket,
    mass = (1.126, 0.03)
)

# What I've added
# ===============

stochastic_nose = StochasticNoseCone(
    nosecone = nose
)

stochastic_fins = StochasticTrapezoidalFins(
    trapezoidal_fins = fins
)

stochastic_rocket.add_motor(
    motor,
    position = 1.42,
)

stochastic_rocket.add_nose(
    stochastic_nose,
    position = 0,
)

stochastic_rocket.add_trapezoidal_fins(
    stochastic_fins,
    position = 1.26,
)

stochastic_rocket.set_rail_buttons(
    rail_buttons,
    lower_button_position = 1.287,
)

# =================

stochastic_flight = StochasticFlight(
    flight = flight,
    inclination = (88, 0.5),
    heading = (90, 2),
)

monte_carlo = MonteCarlo(
    filename = "monte_carlo_results",
    environment = stochastic_env,
    rocket = stochastic_rocket,
    flight = stochastic_flight, 
)


rocket.draw()

if __name__ == "__main__":

    monte_carlo.simulate(
        number_of_simulations=10,
        append=False,
        parallel=True,
        n_workers=4,
        include_function_data=False,
    )

    monte_carlo.info()

monte_carlo.info()

#flight.plots.trajectory_3d()
#flight.plots.linear_kinematics_data()
#flight.plots.angular_kinematics_data()
#flight.plots.flight_path_angle_data()
#flight.plots.aerodynamic_forces()
#flight.plots.stability_and_control_data()

