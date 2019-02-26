## this class of functions defines bezier curve npecifications
## each curve needs 4 points, each of those points is computed via Bernstein polynomials

import numpy as np # this is used for vectorized bezier computation
from scipy.interpolate import CubicSpline


def draw_bezier(total_size,p1,p2,mode="quadratic",inversion=False,path_height=2, linemode="both",resolution=0.1):
    if mode == "quadratic":

        if p1[0] < p1[1]:
            x0, x1 = p1
            y0, y1 = p2
        else:
            x1, x0 = p1
            y1, y0 = p2

        ## coordinate init phase
        dfx = np.arange(x0, x1, resolution)
        slope = (y1-y0)/(x1-x0)
        midpoint_x = (x0+x1) / 2
        mp_y = (y0 + y1) / 2

        midpoint_y = None
        ## x0 x1, y0 y1                
        if linemode == "both":

            r1 = np.round(y0, 0)
            r2 = np.round(y1, 0)
            try:                        
                if r1 > y0 and r2 > y1:
                    midpoint_y = mp_y*path_height
                    x_t = [x0, midpoint_x, x1]
                    y_t = [y0, midpoint_y, y1]
                    cs = CubicSpline(x_t, y_t)
                    dfy = cs(dfx)        
                else:
                    midpoint_y = 1/(mp_y*path_height)
                    x_t = [x0, midpoint_x, x1]
                    y_t = [y0, midpoint_y, y1]
                    cs = CubicSpline(x_t, y_t)
                    dfy = cs(dfx)
            except Exception as err:
                #TODO: takle exception catching ni ok za koncno verzijo...
                print([x0, midpoint_x, x1], [y0, midpoint_y, y1])

        elif linemode == "upper":
            try:
                midpoint_y = mp_y*path_height
                x_t = [x0, midpoint_x, x1]
                y_t = [y0, midpoint_y, y1]
                cs = CubicSpline(x_t, y_t)
                dfy = cs(dfx)        
            except Exception as err:
                print([x0, midpoint_x, x1],[y0,midpoint_y,y1])
            
        elif linemode == "bottom":
            try:
                midpoint_y = 1/(mp_y*path_height)
                x_t = [x0, midpoint_x, x1]
                y_t = [y0, midpoint_y, y1]
                cs = CubicSpline(x_t, y_t)
                dfy = cs(dfx)
            except Exception as err:
                print([x0, midpoint_x, x1], [y0, midpoint_y, y1])

        return (dfx,dfy)
    
    elif mode == "cubic":

        pass
    
    else:
        print ("Mode incorrect, please use quad or cubic.")

        pass
    
def draw_multi_berzier(multiedge_list):

    for edge in multi_edge_list:
        draw_berzier(p1,p1)
    
    pass

