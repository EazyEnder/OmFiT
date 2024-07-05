import pykoopman as pk
import numpy as np 
import matplotlib.pyplot as plt

import numpy.random as rnd
from random import random
np.random.seed(41)

from analyse import Measure

measure = Measure("wt5c2")

traj = measure.trees[0][0]
FLUO = measure.FLUO
CELLS = measure.CELLS

R = [[FLUO[t]["net_mean"] for t in traj]]
R = [np.array(R[0])]

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

t = [CELLS[t]["time"] / (3600) for t in traj]
t = np.array(t)
dt = t[1]-t[0]

R[0] = applyBaseline([2.91,14.83,29.89,40.11,54.63,64.50],[286,286,465,450,507,499],t,R)

kws = dict(kind='kalman', alpha=.1)
gradient = np.array(pk.differentiation.Derivative(**kws)(R[0], t))[:,0]
R.append(gradient)

R[1] = R[1]*np.max(R[0])/np.max(R[1])
R = np.array(R)
R = R.T


fig,axs = plt.subplots(2,1)
ax1 = axs[0]
ax1.axis('equal')
ax1.set_xlim([-1,1])
ax2 = axs[1]

ax1.set_xlabel(r'$x_1$')
ax1.set_ylabel(r'$x_2$')
ax1.set_title("Mesure")

from pydmd import DMD
x1 = R[40:,0]
x2 = R[40:,1]
t = t[40:]
x1 = np.array(x1)
x2 = np.array(x2)
        
ax1.plot(x1,x2)
ax2.plot(t,x1)
ax2.plot(t,x2)

X = np.array([x1,x2]).T

dmd=DMD(svd_rank=2)

model = pk.Koopman(regressor=dmd)
model.fit(X, dt=dt)

K = model.A

evals, evecs = np.linalg.eig(K)
evals_cont = np.log(evals)/dt
print(evals_cont)

plt.show()

