import pykoopman as pk
import numpy as np 
import matplotlib.pyplot as plt

import numpy.random as rnd
from random import random
from pydmd import DMD

from analyse import Measure

COLONY_NAME = "wt2Tc1"

#If this is false, the time axis will just be a list incrementing each 30mins, i.e : [0,0.5,1.,1.5,2.,...]
ORIGINAL_TIMES_AXIS = True

#How many indexes we skip at the begining
BEGIN_SKIP = 0
#How many indexes we skip at the end
END_SKIP = 90

#<=1 is no smoothing
MOVING_AVERAGE_N = 0

def movingAverage(l, n=5):
    cs=np.cumsum(l, dtype=float)
    cs[n:]=cs[n:]-cs[:-n]
    return cs[n-1:]/n

def applyBaseline(t,y,T,R):
    X = R[0]
    last_t = 0
    last_y = [y[0]]

    coefs = []
    for i in range(len(y)):
        y1 = y[i]
        t1 = t[i]
        coefs.append((y1 - last_y[-1]) / (t1 - last_t))
        last_t = t1
        last_y.append(y1)
    coefs.append(0.)

    int_time = []
    for j in range(len(t)+1):
        t_left = 0
        if j > 0:
            t_left = t[j-1]
        t_right = T[-1]
        if j < len(t):
            t_right = t[j]
        int_time.append((t_left,t_right))
    for i in range(len(T)):
        for j,(tl,tr) in enumerate(int_time):
            if T[i] >= tl and T[i] <= tr:
                X[i] = X[i]-(coefs[j]*(T[i]-tl)+last_y[j])
                break
    return X

measure = Measure(COLONY_NAME)

trajs = measure.trees[0]
FLUO = measure.FLUO
CELLS = measure.CELLS

plt.suptitle(COLONY_NAME)

ax1 = plt.subplot(122)
ax1.axis('equal')

ax1.set_xlabel(r'$x_1$')
ax1.set_ylabel(r'$x_2$')
ax1.set_title(COLONY_NAME)

ax2 = plt.subplot(221)
ax2.set_title(r'$x_1$')

ax3 = plt.subplot(223)
ax3.set_title(r'$x_2$')


mean_imag_eigen = 0
for traj in trajs:
    R = [[FLUO[t]["net_mean"] for t in traj]]
    R = [np.array(R[0])]
    t = [CELLS[t]["time"] / (3600) for t in traj]
    t = np.array(t)
    sorted_indexes = np.argsort(t)
    t = t[sorted_indexes]
    if not(ORIGINAL_TIMES_AXIS):
        t = np.array(list(range(len(t))))*.5
    R = [R[0][sorted_indexes]]

    R[0] = applyBaseline(movingAverage(t,n=48),movingAverage(R[0],n=48),t,R)
    if MOVING_AVERAGE_N > 1:
        R[0] = movingAverage(R[0],n=MOVING_AVERAGE_N)
        t = movingAverage(t,n=MOVING_AVERAGE_N)
    dt = t[1]-t[0]

    kws = dict(kind='kalman', alpha=.1)
    gradient = np.array(pk.differentiation.Derivative(**kws)(R[0], t))[:,0]
    R.append(gradient)

    R[1] = R[1]*np.max(R[0])/np.max(R[1])
    R = np.array(R)


    x1 = R.T[BEGIN_SKIP:len(R[0])-END_SKIP,0]
    x2 = R.T[BEGIN_SKIP:len(R[1])-END_SKIP,1]
    t = t[BEGIN_SKIP:len(t)-END_SKIP]
    x1 = np.array(x1)
    x2 = np.array(x2)
            
    ax1.plot(x1,x2)
    ax2.plot(t,x1)
    ax3.plot(t,x2)

    X = np.array([x1,x2]).T

    dmd=DMD(svd_rank=2)

    model = pk.Koopman(regressor=dmd)
    model.fit(X, dt=dt)

    K = model.A

    evals, evecs = np.linalg.eig(K)
    evals_cont = np.log(evals)/dt
    mean_imag_eigen += np.imag(evals_cont[0])

print("Pulsation trouvée: " + str(mean_imag_eigen/len(trajs)))
plt.show()

