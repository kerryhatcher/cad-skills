import inspect
from gerbonara.apertures import CircleAperture, RectangleAperture
print('circle init', inspect.signature(CircleAperture.__init__))
print('rect init', inspect.signature(RectangleAperture.__init__))
