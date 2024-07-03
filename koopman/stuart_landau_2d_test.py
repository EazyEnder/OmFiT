import pykoopman as pk
import numpy as np 
import matplotlib.pyplot as plt

import numpy.random as rnd
from random import random
np.random.seed(41)
import sdeint

def StuartLandau(x,a,b,D1,D2):
    x1,x2 = x 
    x1dot = a*x1-x2-a*(x1*x1+x2*x2)*(x1+b*x2) + np.sqrt(2*D1)*(random()-.5)
    x2dot = a*x2+x1-a*(x1*x1+x2*x2)*(x2-b*x1) + np.sqrt(2*D2)*(random()-.5)
    return [x1dot,x2dot]
N = 1000
NTraj = 1
t = np.linspace(0, 50, N)
x = 2*rnd.random([2, NTraj])-1

from scipy.integrate import odeint

R = []
for i in range(NTraj):
    y = odeint(lambda t,x: StuartLandau(x,1.,0.713,0.0995,0.0995), [x[0,i],x[1,i]], tspan=t, tfirst=True, full_output=1)
    R.append(y)
print(R)

fig,(ax1,ax2) = plt.subplots(2,1)
for i,traj in enumerate(R):
    ax1.scatter(traj[20:,0], traj[20:,1], marker="+")
    ax2.scatter(t[20:],traj[20:,0], marker="+")

plt.show()
