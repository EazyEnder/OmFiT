"""
Import data
"""

COLONY_NAME = "wt0Tc1"
DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

#Define a circle region, if the bact is in à the end then we'll keep it, else she'll be removed.
KEEP_REGION = None
KEEP_DISTANCE = 0

#Each "independant" tree (~different ancestor) has his own row in the figure
DIVIDE_PER_TREE = True
#Effect only if divide per tree is False; if this is false, each branch is a Tree
COMBINE_INTO_ONE_TREE = False

#Smoothing using moving average method
SMOOTH=0

#Apply a baseline using moving average, if this is <=0 -> no baseline applied
BASELINE_Y = 48
BASELINE_R = 0
#If this is true, the baseline will be ploted instead of applied
DRAW_BASELINE = True

#Plot or scatter
LINE_STYLE = True
LINE_STYLE_ELLIPSE = False

PLOT_ELLIPSE = True

import json
import os
import numpy as np
import matplotlib.pyplot as plt

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

def plotFluo(CELLS,FLUO,traj,ax,ax_r,baseline_Y=BASELINE_Y,baseline_R=BASELINE_R,draw_baseline=DRAW_BASELINE):
        Fy = [FLUO[t]["net_mean"] for t in traj]
        Fr = [FLUO[t]["net_mean_r"] for t in traj]
        t = [CELLS[t]["time"] / (24*3600) for t in traj]
        if SMOOTH > 1:
            Fy = movingAverage(Fy,n=SMOOTH)
            Fr = movingAverage(Fr,n=SMOOTH)
            t = movingAverage(t,n=SMOOTH)
        ax.set_ylim([0,1000])
        ax_r.set_ylim([0,1000])
        if baseline_Y > 0:
            mty = movingAverage(t,n=baseline_Y)
            mFy = movingAverage(Fy,n=baseline_Y)
            if draw_baseline:
                ax.plot(mty,mFy,color="black")
            else:
                ax.set_ylim([-500,500])
                Fy = applyBaseline(mty,mFy,t,[Fy])
        if baseline_R > 0:
            mtr = movingAverage(t,n=baseline_R)
            mFr = movingAverage(Fy,n=baseline_R)
            if draw_baseline:
                ax_r.plot(mtr,mFr,color="black")
            else:
                ax_r.set_ylim([-500,500])
                Fr = applyBaseline(mtr,mFr,t,[Fr])
            
        if LINE_STYLE:
            ax.plot(t, Fy)
            ax_r.plot(t, Fr)
        else:
            ax.scatter(t, Fy, s=3.)
            ax_r.scatter(t, Fr, s=3.)

def plotEllipseMajor(CELLS,cells,ax):
    if not(LINE_STYLE_ELLIPSE):
        ax.scatter([CELLS[c]["time"] / (3600*24) for c in cells], [CELLS[c]["ellipse"][0] for c in cells], s=3.)
    else:
        ax.plot([CELLS[c]["time"] / (3600*24) for c in cells], [CELLS[c]["ellipse"][0] for c in cells])

class Measure():
    def __init__(self,COLONY_NAME=COLONY_NAME,DATA_DIR=None):
        self.COLONY_NAME = COLONY_NAME
        self.DATA_DIR = DATA_DIR
        if DATA_DIR is None:
            self.DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

        file_name = "spots_features.json"
        f = open(os.path.join(self.DATA_DIR,file_name))
        self.CELLS = json.load(f)
        f.close()

        file_name = "fluo_features.json"
        f = open(os.path.join(self.DATA_DIR,file_name))
        self.FLUO = json.load(f)
        f.close()

        self.ending_cells = self.getEndingCells()

        #Array of list of trajectory
        trees = []
        for e_cell in self.ending_cells:
            traj = self.getTrajectory(e_cell)
            flag = False
            if not(DIVIDE_PER_TREE):
                if COMBINE_INTO_ONE_TREE:
                    if len(trees) == 0:
                        trees.append([])
                    trees[0].append(traj)
                else:
                    trees.append([traj])
                continue
            for tree in trees:
                if traj[0] in [traj[0] for traj in tree]:
                    flag = True
                    tree.append(traj)
                    break
            if not(flag):
                trees.append([traj])
        self.trees = trees

    def plot(self):
        #graph number
        rows_number = len(self.trees)
        columns_number = 2
        if PLOT_ELLIPSE:
            columns_number = 3 
        if rows_number == 1:
            rows_number = columns_number
            columns_number = 1
        fig,axs = plt.subplots(rows_number,columns_number)
        if axs.ndim == 1:
            axs = np.array([axs])

        fig.suptitle(self.COLONY_NAME, fontsize=16)
        if len(self.trees) > 1:
            fig.suptitle(self.COLONY_NAME +" : Each row is a tree")

        for i,tree in enumerate(self.trees):
            for traj in tree:
                plotFluo(self.CELLS,self.FLUO,traj,axs[i,0],axs[i,1])
            if PLOT_ELLIPSE:
                for traj in tree:
                    cells = {}
                    for c in traj:
                        cells[c] = self.CELLS[c]
                    plotEllipseMajor(self.CELLS,cells,axs[i,2])
                if i == 0:
                    axs[i,2].set_title("Ellipse major vs time")
                if i == len(self.trees)-1:
                    axs[i,2].set_xlabel("time (days)")
                axs[i,2].set_ylabel("width (px)")
                axs[i,2].set_ylim([0,100])
            if i == 0:
                axs[i,0].set_title("Net Y Fluorescence vs Time")
                axs[i,1].set_title("Net R Fluorescence vs Time")
            if i == len(self.trees)-1:
                axs[i,0].set_xlabel("time (days)")
                axs[i,1].set_xlabel("time (days)")
            axs[i,0].set_ylabel("Y fluo")
            axs[i,1].set_ylabel("R fluo")

    def getEndingCells(self):
        ending_cells = []
        for cell_id in self.CELLS.keys():
            cell = self.CELLS[cell_id]
            if cell["children"] is None or len(cell["children"]) == 0:

                if not(KEEP_REGION is None or KEEP_DISTANCE <= 0):
                    if np.linalg.norm(np.array(KEEP_REGION)-np.array(cell["center"])) < KEEP_DISTANCE:
                        ending_cells.append(cell_id)
                    continue
                ending_cells.append(cell_id)
        return ending_cells

    def getTrajectory(self,cell_id):
        parent = self.CELLS[cell_id]["parent"]
        cells_branch = [cell_id]
        while not(parent is None):
            cells_branch.insert(0,parent)
            parent = self.CELLS[parent]["parent"]
        return cells_branch
    
if __name__ == "__main__":
    m = Measure(COLONY_NAME,DATA_DIR=DATA_DIR)
    m.plot()
    plt.show()
    


