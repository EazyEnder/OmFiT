"""
Import data
"""

COLONY_NAME = "dt1c2"
DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

#Define a circle region, if the bact is in à the end then we'll keep it, else she'll be removed.
KEEP_REGION = None
KEEP_DISTANCE = 0

#Each "independant" tree (~different ancestor) has his own row in the figure
DIVIDE_PER_TREE = True
#Effect only if divide per tree is False; if this is false, each branch is a Tree
COMBINE_INTO_ONE_TREE = True


PLOT_ELLIPSE = True

import json
import os
import numpy as np
import matplotlib.pyplot as plt

def plotFluo(CELLS,FLUO,traj,ax,ax_r):
        ax.scatter([CELLS[t]["time"] / (24*3600) for t in traj], [FLUO[t]["net_mean"] for t in traj], s=3.)
        ax_r.scatter([CELLS[t]["time"] / (24*3600) for t in traj], [FLUO[t]["net_mean_r"] for t in traj], s=3.)

def plotEllipseMajor(CELLS,cells,ax):
    ax.scatter([CELLS[c]["time"] / (3600*24) for c in cells], [CELLS[c]["ellipse"][0] for c in cells], s=3.)

class Measure():
    def __init__(self,COLONY_NAME,DATA_DIR):
        self.COLONY_NAME = COLONY_NAME
        self.DATA_DIR = DATA_DIR

        file_name = "spots_features.json"
        f = open(os.path.join(DATA_DIR,file_name))
        self.CELLS = json.load(f)
        f.close()

        file_name = "fluo_features.json"
        f = open(os.path.join(DATA_DIR,file_name))
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

        fig.suptitle(COLONY_NAME, fontsize=16)
        if len(self.trees) > 1:
            fig.suptitle(COLONY_NAME +" : Each row is a tree")

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
    
m = Measure(COLONY_NAME,DATA_DIR)
m.plot()
plt.show()
    


