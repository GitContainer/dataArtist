# this example needs an image display!

# just-in-time compilation:
from numba import njit


@njit
def mandelbrot_calc(c, maxiter):
    z = c
    for n in range(maxiter):
        if abs(z) > 2:
            return n
        z = z * z + c
    return 0


@njit
def mandelbrot(n3, xmin, xmax, ymin, ymax,
               width, height, maxiter):
    r1 = xmin
    r2 = ymin
    dx = (xmax - xmin) / width
    dy = (ymax - ymin) / height
    for i in range(width):
        for j in range(height):
            n3[i, j] = mandelbrot_calc(r1 + 1j * r2,
                                       maxiter)
            r2 += dy
        r2 = ymin
        r1 += dx
    return n3


# let's define some variables:
l_val, r_val = -2.12, 0.1247627
t_val, b_val = -1.223, 0.01124
l_inc, r_inc = .015, -.01
t_inc, b_inc = .015, -.0025
res = (300, 300)  # image resolution
iterations = 71  # image depth - shouldn't be to high

# make it fullscreen:
d.setFullscreen()
d.hideTitleBar()

arr = np.empty(res)


def update():
    # updates mandelbrod via varying variables
    # TODO: mandelbrot really global?
    global l_val, l_inc, r_val, r_inc, t_val, t_inc, b_val, b_inc, \
        mandelbrot, res, iterations
    d.l = mandelbrot(arr, l_val, r_val, t_val, b_val,
                     res[0], res[1], iterations)
    l_val += l_inc
    r_val += r_inc
    t_val += t_inc
    b_val += b_inc


def done():
    d.setFullscreen()
    d.showTitleBar()


# create a timer to coll 'update' every 20 ms:
timed(update, 20, 10000, done)
