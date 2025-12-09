# this class of functions defines bezier curve npecifications
# each curve needs 4 points, each of those points is computed via Bernstein polynomials

from typing import Tuple

import numpy as np  # this is used for vectorized bezier computation
from scipy.interpolate import CubicSpline


def bezier_calculate_dfy(
    mp_y: float,
    path_height: float,
    x0: float,
    midpoint_x: float,
    x1: float,
    y0: float,
    y1: float,
    dfx: np.ndarray,
    mode: str = "upper",
) -> np.ndarray:
    """
    Calculate y-coordinates for bezier curve.

    Args:
        mp_y: Midpoint y-coordinate
        path_height: Height of the path
        x0: Start x-coordinate
        midpoint_x: Midpoint x-coordinate
        x1: End x-coordinate
        y0: Start y-coordinate
        y1: End y-coordinate
        dfx: Array of x-coordinates
        mode: Mode for curve calculation ("upper" or "bottom")

    Returns:
        Array of y-coordinates
    """
    if mode == "upper":
        midpoint_y = mp_y * path_height
    elif mode == "bottom":
        midpoint_y = mp_y * (2 - path_height)
    else:
        raise ValueError(
            "Unknown mode in dfy calculation (value must be one of 'upper', 'bottom'"
        )
    x_t = [x0, midpoint_x, x1]
    y_t = [y0, midpoint_y, y1]
    cs = CubicSpline(x_t, y_t)
    result: np.ndarray = cs(dfx)
    return result


def draw_bezier(
    total_size: int,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    mode: str = "quadratic",
    inversion: bool = False,
    path_height: float = 2,
    linemode: str = "both",
    resolution: float = 0.1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Draw bezier curve between two points.

    Args:
        total_size: Total size of the drawing area
        p1: First point coordinates (x0, x1)
        p2: Second point coordinates (y0, y1)
        mode: Drawing mode (default: "quadratic")
        inversion: Whether to invert the curve
        path_height: Height of the path
        linemode: Line drawing mode ("upper", "bottom", or "both")
        resolution: Resolution for curve sampling

    Returns:
        Tuple of (x-coordinates, y-coordinates) arrays
    """
    if mode == "quadratic":
        if p1[0] < p1[1]:
            x0, x1 = p1
            y0, y1 = p2
        else:
            x1, x0 = p1
            y1, y0 = p2

        # coordinate init phase
        dfx = np.arange(x0, x1, resolution)
        midpoint_x = (x0 + x1) / 2
        mp_y = (y0 + y1) / 2

        if linemode == "both":

            r1 = np.round(y0, 0)
            r2 = np.round(y1, 0)
            try:
                if r1 > y0 and r2 > y1:
                    dfy = bezier_calculate_dfy(
                        mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="upper"
                    )
                else:
                    dfy = bezier_calculate_dfy(
                        mp_y,
                        path_height,
                        x0,
                        midpoint_x,
                        x1,
                        y0,
                        y1,
                        dfx,
                        mode="bottom",
                    )
            except Exception:
                raise Exception(
                    "Unable to calculate coordinate for points "
                    + str((x0, y0))
                    + ", "
                    + str((x1, y1))
                )

        elif linemode == "upper":
            try:
                dfy = bezier_calculate_dfy(
                    mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="upper"
                )
            except Exception:
                raise Exception(
                    "Unable to calculate coordinate for points "
                    + str((x0, y0))
                    + ", "
                    + str((x1, y1))
                )

        elif linemode == "bottom":
            try:
                dfy = bezier_calculate_dfy(
                    mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="bottom"
                )
            except Exception:
                raise Exception(
                    "Unable to calculate coordinate for points "
                    + str((x0, y0))
                    + ", "
                    + str((x1, y1))
                )
        else:
            msg = "Unknown linemode '{lm}' in curve calculation (value must be one of 'upper', 'bottom', 'both')"
            raise ValueError(msg.format(lm=linemode))
        return dfx, dfy

    elif mode == "cubic":
        # Cubic mode not implemented yet
        raise NotImplementedError("Cubic bezier mode is not yet implemented")

    else:
        msg = "Unknown mode '{mode}' in curve calculation (value must be one of 'quadratic', 'cubic', 'quad'"
        raise ValueError(msg.format(mode=mode))
