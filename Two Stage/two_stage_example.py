from rocketpy import GenericMotor, Rocket, Environment, Function, Flight
import numpy as np
import pandas as pd
from pathlib import Path
import datetime
import math
import matplotlib.pyplot as plt

current_folder = Path(__file__).resolve().parent

m = 0.0254 # in to m

env = Environment(
    latitude = 43.65323,
    longitude = -79.38318,
    elevation = 76.5
)

env.set_atmospheric_model(type = "standard_atmosphere")

b_motor_file = current_folder / "AeroTech_I357T_Booster.eng"

booster_motor = GenericMotor.load_from_eng_file(
    file_name = str(b_motor_file)
)

s_motor_file = current_folder / "AeroTech_I59WN_Sustainer.eng"

sustainer_motor = GenericMotor.load_from_eng_file(
    file_name = str(s_motor_file)
)

full_rocket_drag = str(current_folder / "full_rocket_drag_clean.csv")

full_rocket = Rocket(
    radius = 2 * m, 
    mass = 68.998 * 0.0283495, # oz to kg
    inertia = (0.517, 0.517, 0.00685),
    power_off_drag = full_rocket_drag,
    power_on_drag = full_rocket_drag,
    center_of_mass_without_motor = 48.299 * m,
    coordinate_system_orientation = "nose_to_tail"
)

full_rocket.add_motor(
    motor = booster_motor,
    position = 80.75 * m
)

nosecone = full_rocket.add_nose(
    length = 12.75 * m,
    kind = "ogive",
    position = 0
)

booster_fins = full_rocket.add_trapezoidal_fins(
    n = 3,
    root_chord = 5.75 * m,
    tip_chord = 3 * m,
    span = 6.5 * m,
    sweep_length = 1.5 * m,
    position = (80.75 - 6) * m,
    cant_angle = 0
)

sustainer_fins = full_rocket.add_trapezoidal_fins(
    n = 3,
    root_chord = 5.75 * m,
    tip_chord = 3 * m,
    span = 6 * m,
    sweep_length = 1.5 * m,
    position = (55.75 - 6) * m,
    cant_angle = 0
)

booster_rail_b = full_rocket.set_rail_buttons(
    upper_button_position = 58.35 * m,
    lower_button_position = (58.35 + 19.791) * m,
    angular_position = 180,
)

sustainer_drag = str(current_folder / "sustainer_drag_clean.csv")

sustainer = Rocket(
    radius = 2 * m,
    mass = 39.727 * 0.0283495,
    inertia = (0.152, 0.152, 0.00396),
    power_off_drag = sustainer_drag,
    power_on_drag = sustainer_drag,
    center_of_mass_without_motor = 34.652 * m,
    coordinate_system_orientation = "nose_to_tail"
)

sustainer.add_motor(
    motor = sustainer_motor,
    position = 55.75 * m
)

nosecone = sustainer.add_nose(
    length = 12.75 * m,
    kind = "ogive",
    position = 0
)

sustainer_fins = sustainer.add_trapezoidal_fins(
    n = 3,
    root_chord = 5.75 * m,
    tip_chord = 3 * m,
    span = 6 * m,
    sweep_length = 1.5 * m,
    position = (55.75 - 6) * m,
    cant_angle = 0
)

drogue_diameter = 12 * m
drogue_cd = 0.80
drogue_cd_s = (drogue_cd * math.pi * (drogue_diameter / 2.0) ** 2)

sustainer_drogue = sustainer.add_parachute(
    name = "Sustainer Drogue",
    cd_s = drogue_cd_s,
    trigger = "apogee",
    sampling_rate = 100,
    lag = 0,
    noise = (0, 0, 0),
)

sustainer_chute_diameter = 36 * m
sustainer_chute_cd = 0.80
sustainer_chute_cd_s = sustainer_chute_cd * math.pi * (sustainer_chute_diameter / 2.0) ** 2

MAIN_DEPLOYMENT_HEIGHT = 800 * 0.3048

sustainer_main = sustainer.add_parachute(
    name ="Sustainer Main",
    cd_s = sustainer_chute_cd_s,
    trigger = MAIN_DEPLOYMENT_HEIGHT,
    sampling_rate = 100,
    lag = 0,
    noise=(0, 0, 0),
)

booster_drag = str(current_folder / "booster_drag_clean.csv")

booster_length = 25 * m

booster_structure_mass = 0.830
booster_motor_dry_mass = booster_motor.dry_mass

separated_booster_mass = booster_structure_mass + booster_motor_dry_mass

seperated_booster = Rocket(
    radius = 2 * m,
    mass = separated_booster_mass,
    inertia = (0.0424, 0.0424, 0.00297),
    power_off_drag = booster_drag,
    power_on_drag = booster_drag,
    center_of_mass_without_motor = 34.652 * m,
    coordinate_system_orientation = "nose_to_tail"
)

#seperated_booster.add_trapezoidal_fins(
    #n = 3,
    #root_chord = 5.75 * m,
    #tip_chord = 3 * m,
    #span = 6.5 * m,
    #sweep_length = 1.5 * m,
    #position = (34.652 - 6) * m,
    #cant_angle = 0
#)

booster_chute_diameter = 24 * m
booster_chute_area = math.pi * (booster_chute_diameter / 2.0) ** 2
booster_chute_cd_s = 0.80 * booster_chute_area

BOOSTER_EJECTION_AFTER_SEPARATION = 13.485

def booster_ejection_trigger(
    pressure,
    height,
    state_vector,
):
    return state_vector[0] >= BOOSTER_EJECTION_AFTER_SEPARATION

seperated_booster.add_parachute(
    name = "Booster Parachute",
    cd_s = booster_chute_cd_s,
    trigger = lambda pressure, height, state_vector: state_vector[0] >= 0.05,
    sampling_rate = 20,
    lag = 0,
    noise = (0, 0, 0)
)

separation_time = 1.515 #from openrocket

# Flight 1: complete two stage, runs untils seperation

full_rocket_flight = Flight(
    rocket = full_rocket,
    environment = env,
    rail_length = 5.2,
    inclination = 85, 
    heading = 0,
    max_time = separation_time,
    max_time_step = 0.05,
    terminate_on_apogee = False,
    name = "Full Rocket Before Seperation"
)

print("full Rocket Flight FInished")

# Final state of the full rocket at separation
separation_state = list(full_rocket_flight.solution[-1])

# Create separate copies because the two stages branch from the same state
sustainer_initial_state = separation_state.copy()
booster_initial_state = separation_state.copy()

# Reset each new flight phase to local time zero.
# Position, velocity, attitude and angular velocity remain unchanged.
sustainer_initial_state[0] = 0.0
booster_initial_state[0] = 0.0
booster_initial_state[11] = 0.0
booster_initial_state[12] = 0.0
booster_initial_state[13] = 0.0

print("Starting sustainer")

# Flight 2A: sustainer after separation

sustainer_flight = Flight(
    rocket = sustainer,
    environment = env,
    rail_length = 0.001, # has to be above 0
    initial_solution = sustainer_initial_state,
    max_time = 30,
    max_time_step = 0.2,
    # Stop at apogee for the first test
    terminate_on_apogee=False,

    # Looser tolerance for faster testing
    rtol=1e-4,

    time_overshoot=True,
    name = "Sustainer After Separation"
)

print("Finished sustainer, starting booster")

# Flight 2B: separated booster

booster_flight = Flight(
    rocket=seperated_booster,
    environment=env,
    rail_length=0.001,
    initial_solution=booster_initial_state,
    max_time=30,
    max_time_step=0.5,
    rtol=1e-3,
    atol=1e-6,
    time_overshoot=True,
    terminate_on_apogee=False,
    ode_solver="LSODA",
    name="Separated Booster",
)

print("finishhed booster")

full_rocket_flight.info()
sustainer_flight.info()
booster_flight.info()

# Full stacked rocket
#full_rocket_flight.plots.linear_kinematics_data()
#full_rocket_flight.plots.trajectory_3d()
#full_rocket_flight.plots.stability_and_control_data()

# Sustainer
#sustainer_flight.plots.linear_kinematics_data()
#sustainer_flight.plots.trajectory_3d()
#sustainer_flight.plots.pressure_signals()

# Separated booster
#booster_flight.plots.linear_kinematics_data()
#booster_flight.plots.trajectory_3d()
#booster_flight.plots.pressure_signals()

# =========================================================
# COMBINED 3D TRAJECTORY
# =========================================================

# Full rocket time values
full_time = np.array(full_rocket_flight.solution)[:, 0]

# Sustainer local time values
sustainer_time = np.array(sustainer_flight.solution)[:, 0]

# Booster local time values
booster_time = np.array(booster_flight.solution)[:, 0]


# Evaluate trajectory coordinates
full_x = np.array([full_rocket_flight.x(t) for t in full_time])
full_y = np.array([full_rocket_flight.y(t) for t in full_time])
full_z = np.array([full_rocket_flight.z(t) for t in full_time])

sustainer_x = np.array(
    [sustainer_flight.x(t) for t in sustainer_time]
)
sustainer_y = np.array(
    [sustainer_flight.y(t) for t in sustainer_time]
)
sustainer_z = np.array(
    [sustainer_flight.z(t) for t in sustainer_time]
)

booster_x = np.array(
    [booster_flight.x(t) for t in booster_time]
)
booster_y = np.array(
    [booster_flight.y(t) for t in booster_time]
)
booster_z = np.array(
    [booster_flight.z(t) for t in booster_time]
)


# Create combined 3D plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")

ax.plot(
    full_x,
    full_y,
    full_z,
    label="Full Rocket Before Separation",
)

ax.plot(
    sustainer_x,
    sustainer_y,
    sustainer_z,
    label="Sustainer After Separation",
)

ax.plot(
    booster_x,
    booster_y,
    booster_z,
    label="Separated Booster",
)

# Mark the separation point
ax.scatter(
    full_x[-1],
    full_y[-1],
    full_z[-1],
    marker="o",
    s=60,
    label="Stage Separation",
)

ax.set_xlabel("East Position (m)")
ax.set_ylabel("North Position (m)")
ax.set_zlabel("Height Above Launch Site (m)")
ax.set_title("Complete Two-Stage Rocket Flight")
ax.legend()
ax.grid(True)

plt.tight_layout()
plt.show()

# =========================================================
# COMBINED ALTITUDE VS TIME
# =========================================================

full_absolute_time = full_time

sustainer_absolute_time = (
    sustainer_time + separation_time
)

booster_absolute_time = (
    booster_time + separation_time
)

plt.figure(figsize=(10, 6))

plt.plot(
    full_absolute_time,
    full_z,
    label="Full Rocket",
)

plt.plot(
    sustainer_absolute_time,
    sustainer_z,
    label="Sustainer",
)

plt.plot(
    booster_absolute_time,
    booster_z,
    label="Booster",
)

plt.axvline(
    separation_time,
    linestyle="--",
    label="Stage Separation",
)

plt.xlabel("Time After Launch (s)")
plt.ylabel("Height Above Launch Site (m)")
plt.title("Two-Stage Rocket Altitude")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()