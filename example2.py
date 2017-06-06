#### This is an example for the py3plex multiplex network visualization library
#### CUSTOM MULTIEDGE

from py3plex.multilayer import *

x = generate_random_networks(3)
draw_multilayer_default(x,display=False,background_shape="circle")
mel = [((1,1),(2,12))]
draw_multiplex_default(x,mel,input_type="tuple")
plt.show()
