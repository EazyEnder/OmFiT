import pykoopman as pk
import numpy as np
import matplotlib.pyplot as plt
from random import random

fig,(ax1,ax2,ax3) = plt.subplots(3,1)

N = 500
t = np.linspace(2,20,N)

a = 1.+1j
l=1.+1.j
D = 1.
stuart_landau = lambda t,x: a*x-l/2*x*np.power(np.abs(x),2)+D*(random()-.5)

from scipy.integrate import solve_ivp
result = solve_ivp(stuart_landau, (0,20), [1], t_eval=t)

x = np.real(np.exp(6.j*t)+0.5*np.exp(8.41j*t))
xdot = np.gradient(x)
dt = t[1] - t[0]

ax1.scatter(t,x,marker="+")
#xdot = stuart_landau(t,x)

from pydmd import DMD

dmd=DMD(svd_rank=5)

model = pk.Koopman(regressor=dmd)
model.fit(x,dt=dt)

K = model.A

evals, evecs = np.linalg.eig(K)
evals_cont = np.log(evals)/dt
print(evals_cont)

ax2.plot(evals_cont.real, evals_cont.imag, 'bo', label='estimated',markersize=5)


#ax.set_xlim([-1,1])
#ax.set_ylim([-1,1])
ax2.legend()
ax2.set_xlabel(r'$Re(\lambda)$')
ax2.set_ylabel(r'$Im(\lambda)$')

#x0_fit = np.array([[x[0][0]]])
#print(x0_fit.ndim)
x_fit = model.simulate(np.array([x[0]]), n_steps=x.shape[0] - 1)
ax3.scatter(x,xdot,marker="+")

plt.show()