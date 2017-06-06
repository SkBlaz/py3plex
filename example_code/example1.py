#### This is an example for the py3plex multiplex network visualization library
#### RANDOM NETWORKS

from py3plex.multilayer import *

x = generate_random_networks(8)
draw_multilayer_default(x,display=False,background_shape="circle")
generate_random_multiedges(x,12,style="piramidal")
generate_random_multiedges(x,60,style="curve2_bezier")
plt.show()


