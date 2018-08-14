## this class of functions defines bezier curve npecifications
## each curve needs 4 points, each of those points is computed via Bernstein polynomials

import numpy as np # this is used for vectorized bezier computation

def draw_bezier(total_size,p1,p2,mode="quadratic",inversion=False,path_height=1,linemode="both"):
    if mode == "quadratic":
        #draw quadratic polinome
        space = np.linspace(0,8,10000)
        if inversion == False:
            x_delay = p1[1]
            y_delay = p2[0]
        else:
            y_delay = p1[1]
            x_delay = p2[0]


        if linemode == "both":

            if p1[0] > p1[1]:
                x = ((1-space)**2)*p1[0]+2*(1-space)*space*x_delay+space**2*p1[1]
                y = (1-space)**2*p2[0]+path_height*(1-space)*space*y_delay+space**2*p2[1]
                idx = np.argmin(np.abs(x - p2[0]))
                idy = np.argmin(np.abs(y - p2[1]))

            elif p1[0] < p1[1]:
                x = ((1-space)**2)*p1[1]+2*(1-space)*space*x_delay+space**2*p1[0]
                y = (1-space)**2*p2[1]+path_height*(1-space)*space*y_delay+space**2*p2[0]
                idx = np.argmin(np.abs(x - p2[1]))
                idy = np.argmin(np.abs(y - p2[0]))
            
            else:
                pass
            
        elif linemode == "upper":
            if p1[0] > p1[1]:
                x = ((1-space)**2)*p1[0]+2*(1-space)*space*x_delay+space**2*p1[1]
                y = (1-space)**2*p2[0]+path_height*(1-space)*space*y_delay+space**2*p2[1]
                idx = np.argmin(np.abs(x - p2[0]))
                idy = np.argmin(np.abs(y - p2[1]))
        else:
            pass

        return (x[1:idy],y[1:idy])
    
    elif mode == "cubic":

        pass
    
    else:
        print ("Mode incorrect, please use quad or cubic.")

        pass
    
def draw_multi_berzier(multiedge_list):

    for edge in multi_edge_list:
        draw_berzier(p1,p1)
    
    pass

