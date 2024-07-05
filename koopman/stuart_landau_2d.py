import pykoopman as pk
import numpy as np 
import matplotlib.pyplot as plt

import numpy.random as rnd
from random import random
np.random.seed(41)


def euler(f,x0,t,dt=None):
    X = [x0]
    T = [t[0]]
    if dt is None:
        dt = t[1]-t[0]
    for i in range(int((t[-1]-t[0])/dt)):
        T.append(T[-1]+dt)
        X.append(X[-1]+f(T[-1],X[-1])*dt)
    X = np.array(X)
    T = np.array(T)
    return T,X
        

def StuartLandau(x,a,b):
    x1,x2 = x 
    x1dot = a*x1-x2-a*(x1*x1+x2*x2)*(x1+b*x2)
    x2dot = a*x2+x1-a*(x1*x1+x2*x2)*(x2-b*x1)
    return np.array([x1dot,x2dot])
N = 2000

NTraj = 100
tmax = 80
t = np.linspace(0, tmax, N)
x = 2*rnd.random([2, NTraj])-1

a = 1
b = -0.3
T = 2*np.pi/(1+b*a)
w = 2*np.pi/T

noiseD = 0.04
D = np.linspace(noiseD*.1,noiseD*10.,NTraj)
if NTraj == 1:
    D = [noiseD]

cutTime = 10
cutIndex = int(N/tmax*cutTime)

Nw = 48
Nloss = int(1/(Nw*tmax/T/N))

from scipy.integrate import odeint
from sdeint import itoEuler, stratHeun

R = []
for i in range(NTraj):
    y = stratHeun(lambda x,t: StuartLandau(x,a, b), lambda x,tt: np.diag([np.sqrt(D[i]), np.sqrt(D[i])]), [x[0,i],x[1,i]], t)
    R.append(y)
R = np.array(R)

fig,axs = plt.subplots(2,2)
ax1 = axs[0,0]
ax3 = axs[0,1]
ax2 = axs[1,0]
ax4 = axs[1,1]

ax1.axis('equal')

ax1.set_xlim([-1,1])

ax1.set_xlabel(r'$x_1$')
ax1.set_ylabel(r'$x_2$')
ax1.set_title("Base / Intégré")

ax3.set_xlabel(r'D')
ax3.set_ylabel(r'$Re(\lambda)$')
ax3.set_title("Re lambda")

ax4.set_xlabel(r'D')
ax4.set_ylabel(r'$Im(\lambda)$')
ax4.set_title("Im lambda")

t = t[cutIndex:]
#ax4.plot([-0.048,-0.048], [0.698,-0.698],'rs', label='true for D=0.04',markersize=10)
from pydmd import DMD
for i,traj in enumerate(R):
    x1 = []
    x2 = []
    tmodif = []
    for j in range(len(traj[cutIndex:,0])):
        if j % Nloss == 0:
            x1.append(traj[cutIndex:,0][j])
            x2.append(traj[cutIndex:,1][j])
            tmodif.append(t[j])
    dt = tmodif[1]-tmodif[0]
    x1 = np.array(x1)
    x2 = np.array(x2)
    tmodif = np.array(tmodif)
            
    ax1.plot(x1,x2)
    ax2.plot(tmodif,x1, label=r'$x_1$ for $D=$'+str(np.round(D[i],3)))
    #ax2.plot(tmodif,x2,  label=r'$x_2$')

    X = np.array([x1,x2]).T

    dmd=DMD(svd_rank=10)

    model = pk.Koopman(regressor=dmd)
    model.fit(X, dt=dt)

    K = model.A

    evals, evecs = np.linalg.eig(K)
    evals_cont = np.log(evals)/dt
    print(evals_cont)

    ax3.scatter(D[i], evals_cont.real[0], marker='+')

    ax4.plot(D[i], evals_cont.imag[0], marker='+')


ax2.legend()
ax4.legend()


plt.show()

