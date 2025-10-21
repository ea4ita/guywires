from dotenv import load_dotenv
import os
import logging
import numpy as np
import locale
from typing import Any

# region: Initialize environment
load_dotenv()

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger.info(f"Guy Wires - Logging level: {logger.getEffectiveLevel()}")

# Initialize locale using current environment
locale.setlocale(locale.LC_ALL, '')

curlocale: dict[str, Any] = dict(locale.localeconv())
list_sep = ';' if curlocale['decimal_point'] == ',' else ','
# endregion

# region: Tensions
def get_tensions(
    wind_presure: float, wind_angle: float, guy_wires_angles: list[float], tolerance: float = 1e-9
) -> list[float]:
    """
    Get tensions for each guy wire for a given wind pressure and angle

    :param wind_presure: Wind pressure in Newtons
    :param wind_angle: Wind angle in sexagesimal degrees
    :param guy_wires_angles: List of guy wires angles in degrees
    :return tensions: List of tensions for each guy wire
    """

    guy_wires_count: int = len(guy_wires_angles)
    tensions: np.ndarray = np.zeros(guy_wires_count, dtype=float)
    rad_wind_angle: float = wind_angle * np.pi / 180
    rad_tension_angle: float = (
        rad_wind_angle + np.pi
    )  # Force tension angle to be opposite to wind angle
    rad_guy_wires_angles: np.ndarray = np.array(
        [angle * np.pi / 180 for angle in guy_wires_angles]
    )

    # Get wind pressure vector. NOTICE: 0º is North, positive angles are clockwise
    F: np.ndarray = wind_presure * np.array(
        [np.sin(rad_tension_angle), np.cos(rad_tension_angle)]
    )

    # Get guy wires vectors and traspose
    U: np.ndarray = np.vstack(
        [np.sin(rad_guy_wires_angles), np.cos(rad_guy_wires_angles)]
    ).T

    # Initialize active wires
    active_wires: list[int] = list(range(guy_wires_count))

    # Solve linear system
    while True:
        active_wires_count: int = len(active_wires)
        if active_wires_count == 0:
            # No active wires left
            return tensions.tolist()
        U_actives: np.ndarray = U[active_wires, :]

        T_actives: np.ndarray
        if active_wires_count >= 2: # At least 2 active wires
            try:
                # Solve linear system U_actives^T * tensions = -F
                M = np.linalg.inv(U_actives.T @ U_actives)  # 2x2 (U^T·U)^−1
                # invM = np.linalg.inv(M)
                T_actives: np.ndarray  = - (U_actives @ (M @ F))
            except np.linalg.LinAlgError:
                # No direct solution, approximate with least squares 
                logger.warning("No direct solution, approximate with least squares. THIS CANNOT HAPPEN WITH ONLY 3 WIRES")               
                T_actives, _, _, _  = np.linalg.lstsq(U_actives, -F, rcond=None)
        else:
            # Only 1 active wire. Project F on it
            T_value = max(0.0, - np.dot(F, U_actives[0]))
            T_activesy = np.array([T_value])


        # If any tension is negative, remove active wire and recalculate
        if np.all(T_actives >= -tolerance):
            # fijar en vector de salida y terminar
            for i, value in zip(active_wires, T_actives):
                tensions[i] = max(0.0, float(value))  # evitar pequeñas negativas por error numérico
            return tensions.tolist()
        else:
            # Remove the most negative tension (can be more than 1)
            min_tension_wire = int(np.argmin(T_actives))   # posición en T_act
            wire_to_remove = active_wires[min_tension_wire]   # índice real en tensiones
            # quitarlo del conjunto activo y volver a iterar
            active_wires.remove(wire_to_remove)
            # bucle continúa y resolverá con nuevos activos

    return tensions.tolist()


# endregion: Tensions


# region: Input parameters
def get_input_parameters_float(param_name: str, default_value: float = 0.0) -> float:
    param_str = input(f"{param_name} [{locale.format_string('%.1f',default_value,grouping=True)}]: ")
    try:
        return locale.atof(param_str)
    except ValueError:
        return default_value


wind_presure = get_input_parameters_float("Wind pressure (N)", 100.0)
# wind_angle = get_input_parameters_int("Wind angle (deg)", 30)
guy_wires_angles: list[float] = [0.0, 120.0, 240.0]
i: int
angle: float
prev_angle: float = 0.0
for i, angle in enumerate(guy_wires_angles):
    while True:
        guy_wires_angles[i] = get_input_parameters_float(f"Guy wires heading angle {i} (deg)", angle)
        if guy_wires_angles[i] >= prev_angle and guy_wires_angles[i] <= 360.0:
            prev_angle = guy_wires_angles[i]
            break
        else:
            print(f"Invalid angle. It has to be between {prev_angle} and 360 degrees. Try again.")

# endregion: Input parameters



# region: Output

print(f"Wind pressure: {locale.format_string('%3.0f',wind_presure, grouping=True)} N")
print(f"Guy wires angles: ", end="")
for angle in guy_wires_angles:
    print(f"{locale.format_string('%.1f',angle,grouping=True)}{list_sep}", end="")
print("")
print(f"Angle{list_sep}  Tension 1{list_sep} Tension 2{list_sep} Tension 3{list_sep}")
for angle in np.arange(0.0, 360.0, 10.0):
    tensions = get_tensions(wind_presure, angle, guy_wires_angles)
    print(f"  {locale.format_string('%3.0f',angle,grouping=True)}{list_sep} ", end="")
    for tension in tensions:
        print(f"{locale.format_string('%10.1f',tension,grouping=True)}{list_sep}", end="")
    print("")
# endregion
