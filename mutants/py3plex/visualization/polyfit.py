import numpy as np

# this file contains functions for polynome fitting


def draw_order3(networks, p1, p2):

    midpoint = p2[0] + 1, p1[1] + 1
    x = [p1[0], midpoint[0], p1[1]]
    y = [p2[0], midpoint[1], p2[1]]
    z = np.polyfit(x, y, 3)
    f = np.poly1d(z)
    space_x = np.linspace(0, networks, 10)
    space_y = f(space_x)

    return (space_x, space_y)


def draw_piramidal(networks, p1, p2):

    midpoint = p2[0] + 1, p1[1] + 1
    x = [p1[0], midpoint[0], p1[1]]
    y = [p2[0], midpoint[1], p2[1]]

    return (x, y)
