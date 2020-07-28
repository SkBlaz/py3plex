import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from py3plex.core import multinet
from py3plex.core import random_generators
import matplotlib.image as mgimg
import numpy as np

fig = plt.figure()
folder_tmp_files = "../datasets/animation"


def animate(mnod):
    ER_multilayer = random_generators.random_multilayer_ER(mnod,
                                                           6,
                                                           0.005,
                                                           directed=False)
    fx = ER_multilayer.visualize_network(show=False)
    plt.savefig("{}{}.png".format(folder_tmp_files, mnod))


imrange = [100, 150, 200, 300, 500, 250, 600]
for j in imrange:
    animate(j)
myimages = []
for p in imrange:
    img = mgimg.imread("{}{}.png".format(folder_tmp_files, p))
    imgplot = plt.imshow(img)
    myimages.append([imgplot])
my_anim = animation.ArtistAnimation(fig, myimages, interval=1000, blit=True)

## upload to gif maker or store as a video
my_anim.save('../example_images/animation.gif', writer='imagemagick', fps=1)
