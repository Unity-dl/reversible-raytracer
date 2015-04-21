import os
import numpy as np
from scenemaker import simple_scene
from grad_descent import GDOptimizer
import theano
from util import *

if not os.path.exists('output'):
    os.makedirs('output')

scene = simple_scene()
#scene.translate(scene.objects[2], (0.,2,7))
scene.translate(scene.objects[1], (6.,1,1))
scene.translate(scene.objects[0], (10,-1,1))
scene.scale(scene.objects[0], (1,2,1.5), np.zeros((3,)))
#scene.rotate(scene.objects[2], 'x', 90)

opt = GDOptimizer(scene)

print 'Rendering initial scene'
variables, values, image = scene.build()
render_fn = theano.function([], image, on_unused_input='ignore')

drawWithMarkers('output/0.png', render_fn())

print 'Building gradient functions'
train = opt.optimize(-image[90, 85].sum()-image[50, 90].sum(),
                     0.0008, 0.1)

for i in range(90):
    print 'Step', i+1
    print train()
    drawWithMarkers('output/%d.png' % (i+1,), render_fn())
