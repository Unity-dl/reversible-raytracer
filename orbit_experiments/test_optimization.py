import os
import numpy as np
import theano.tensor as T
import theano
from scipy import misc

from linear_encoder import LinEncoder
from autoencoder_2ly import Autoencoder2ly
from variational_ae import VAE
from convolutional_encoder import Conv_encoder
from transform import *
from scene import *
from shader import *
from optimize import *


def scene(capsules, obj_params, cam_loc, cam_dir):

    shapes = []
    #TODO move the material information to attribute of capsule instance
    material1 = Material((0.0, 0.9, 0.0), 0.3, 0.7, 0.5, 50.)
    material2 = Material((0.9, 0.0, 0.0), 0.3, 0.9, 0.4, 50.)
    center2 = theano.shared(np.asarray([0, 0, 48], dtype=theano.config.floatX), borrow=True)

    for i in xrange(len(capsules)):

        capsule     = capsules[i]
        obj_param   = obj_params[i]
        t1 = translate(obj_param) #* scale(obj_param[1,:])
        if capsule.name == 'sphere':
            shapes.append(Sphere(t1 * scale((4, 4, 4)), material1))
        elif capsule.name == 'square':
            shapes.append(Square(t1, material1))
        elif capsule.name == 'light':
            shapes.append(Light(t1, material1))

    shapes.append(Sphere(translate(center2) * scale((6, 6, 6)), material2))
    light = Light((-0., -0., 1), (1., 1., 1.)) # (0.961, 1., 0.87)
    camera = Camera(img_sz, img_sz, cam_loc, cam_dir)
    shader = PhongShader()
    #shader = DepthMapShader()

    scene = Scene(shapes, [light], camera, shader)
    return [scene, scene.build()]


def test_1image(num_capsule  = 1,
                epsilon      = 0.00001,
                epsilon_adam = 0.0001,
                num_epoch    = 5000,
                opt_image    = './orbit_dataset/40.png'):

    if not os.path.exists('./output/one_imgs'):
        os.makedirs('./output/one_imgs')

    data = np.load('orbit_dataset.npz')['arr_0'] / 255.0
    data = data.astype('float32')
    train_data = data[2,:,:,:]  
    N2,D,D,K = train_data.shape
    train_data = theano.shared(train_data.reshape(1, N2,D*D*K))

    global img_sz
    img_sz = D 

    #ae = LinEncoder(scene, D, 300,  num_capsule)
    ae = Autoencoder2ly(scene, img_sz*img_sz*3, 600, 30, num_capsule)
    opt = MGDAutoOptimizer(ae)

    lam = 2,
    train_ae = opt.optimize(train_data, lam)
    #train_aeADAM = opt.optimizeADAM(train_data)
    get_recon1 = theano.function([], ae.get_reconstruct(train_data[0,0], train_data[0,1]))
    get_center1= theano.function([], ae.encoder(train_data[0,0].dimshuffle('x',0), \
                                                        train_data[0,1].dimshuffle('x',0))[0][0].flatten())

    center = get_center1()    
    imsave('output/two_imgs/1_test_balls0.png', get_recon1()[0].reshape(D,D,3))
    imsave('output/two_imgs/2_test_balls0.png', get_recon1()[1].reshape(D,D,3))
    print '...Initial center1 (%g,%g,%g)' % (center[0], center[1], center[2])
    
    n=0;
    while (n<num_epoch):
    
        n+=1
        eps = get_epsilon(epsilon, num_epoch, n)
        train_loss  = train_ae(0, eps)
    
        if n % 50 ==0 or n < 5:
            center = get_center1()
            print '...Epoch %d Eps %g, Train loss %g, Center (%g, %g, %g)' \
                    % (n, eps, train_loss, center[0], center[1], center[2])
    
            imsave('output/one_imgs/test_balls%d_1.png' % n, get_recon1()[0].reshape(D,D,3))
            imsave('output/one_imgs/test_balls%d_1.png' % n, get_recon1()[1].reshape(D,D,3))




def test_2images(epsilon,
               epsilon_adam = 0.0001,
               num_epoch    = 6000,
               num_capsule  = 1,
                lam         = 2,
               ae_type      = 'vae'):

    if not os.path.exists('./output/two_imgs'):
        os.makedirs('./output/two_imgs')

    data = np.load('orbit_dataset.npz')['arr_0'] / 255.0
    data = data.astype('float32')
    num_points = 4
    train_data = data[2:2+num_points ,:,:,:] 
    N1,N2,D,D,K = train_data.shape
    train_data = theano.shared(train_data.reshape(N1, N2,D*D*K))
    global img_sz 
    img_sz = D 

    #ae = LinEncoder(scene, img_sz*img_sz*3, 300,  num_capsule)
    ae = Autoencoder2ly(scene, img_sz*img_sz*3, 600, 30, num_capsule)
    #ae = Conv_encoder(scene, img_sz*img_sz*3, num_capsule)
    #ae = VAE(scene, img_sz*img_sz*3, 300, 30, 10, num_capsule)
    #ae = Autoencoder(scene, img_sz*img_sz*3, 300, 30, 10, num_capsule)

    opt = MGDAutoOptimizer(ae)
    train_ae = opt.optimize(train_data, lam)
    #train_aeADAM = opt.optimizeADAM(train_data)

    get_recon1 = theano.function([], ae.get_reconstruct(train_data[0,0], train_data[0,1]))
    get_recon2 = theano.function([], ae.get_reconstruct(train_data[1,0], train_data[1,1]))
    get_center1= theano.function([], ae.encoder(train_data[0,0].dimshuffle('x',0), \
                                                        train_data[0,1].dimshuffle('x',0))[0][0].flatten())
    get_center2= theano.function([], ae.encoder(train_data[1,0].dimshuffle('x',0), \
                                                        train_data[1,1].dimshuffle('x',0))[1][0].flatten())

    center = get_center1()
    imsave('output/two_imgs/1_test_balls0.png', get_recon1()[0].reshape(D,D,3))
    imsave('output/two_imgs/2_test_balls0.png', get_recon2()[0].reshape(D,D,3))
    print '...Initial center1 (%g,%g,%g)' % (center[0], center[1], center[2])

    n=0;
    while (n<num_epoch):
        n+=1
        eps = get_epsilon(epsilon, num_epoch, n)
        train_loss = 0 
        for i in xrange(num_points):
            train_loss += train_ae(i, eps) 


            if n % 100 == 0 or n < 5:
                center1 = get_center1()
                center2 = get_center2()
                print '...Epoch %d Train loss %g, Center (%g, %g, %g), Center (%g, %g, %g)' \
                    % (n, train_loss, center1[0], center1[1], center1[2], center2[0], center2[1], center2[2])

        if n % 100 == 0 or n < 5:   
            imsave('output/two_imgs/test_balls%d_1.png' % (n,), get_recon1()[0].reshape(D,D,3))
            imsave('output/two_imgs/test_balls%d_2.png' % (n,), get_recon2()[0].reshape(D,D,3))
 
    pass
   
    
if __name__ == '__main__':

    global RGBflag
    RGBflag = True
    A = 0

    if A:
        test_1image()
    else: 
        ae_type      = 'ae'
        if ae_type=='vae': #Note: training with VAE doesn't work yet
            epsilon      = 0.0000001 
        elif ae_type=='ae':
            epsilon      = 0.00001
        else:
            epsilon      = 0.00002
        test_2images(epsilon, ae_type=ae_type)
   


