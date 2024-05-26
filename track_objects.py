import numpy as np
from sort_utils import *
import time
from utils import printProgressBar
import multiprocessing
import copy

#Intersection over union threshold
IOU_THRESHOLD_FORCE = 0.5

def MPLinkProcess(old_state,state,k,DATA,iou_threshold):
    l = []
    for i,c in enumerate(state):
        l.append(c.findParent(old_state,iou_threshold=iou_threshold,cell_index=i))
    DATA[k] = (k,l)

def verifyShape(cell,cell2):
    if(cell.space is None or cell2.space is None):
        print("Error: Cell space matrix not defined")
        return False
    if(np.shape(cell.space) != np.shape(cell2.space)):
        print("Error: Space matrix have not the same shape")
        return False
    return True

def createCellsUsingMask(mask,outlines,time):
    ids = np.unique(mask)
    cells = []
    for id in ids:
        if(id <= 0):
            continue
        flags = mask == id
        space = np.zeros(np.shape(mask))
        for i in range(np.shape(mask)[0]):
            for j in range(np.shape(mask)[1]):
                if(flags[i,j]):
                    space[i,j]=1
        c = Cell(space,time,outlines[id-1])
        cells.append(c)
    return cells

class Clip():
    """Manages all the frames and gives coherence"""
    def __init__(self,masks,outlines,times=None,iou_threshold=0.2):
        if(times is None):
            times=range(1,len(masks)+1)
        self.times = times
        
        print("Create Cells")
        tic = time.time() 
        states = []
        for m in range(len(masks)):
            printProgressBar(m,len(masks))
            states.append(createCellsUsingMask(masks[m],outlines[m],times[m]))
        self.states = states
        net_time = time.time() - tic

        print(f'Cells Creation done ({np.round(net_time,2)}s)')

        print("Tracking")
        tic = time.time() 
        self.linkCells(iou_threshold=iou_threshold)
        net_time = time.time() - tic
        print(f'Cells Tracking done ({np.round(net_time,2)}s)')

        #self.mergeSporadicsCells()

        print("FAM Weights")
        fam_weights = []
        tic = time.time() 
        for m in range(len(masks)):
            printProgressBar(m,len(masks))
            l = []
            for cell in self.states[m]:
                l.append((cell,cell.computeFAMWeight()))
            fam_weights.append(l)
        net_time = time.time() - tic
        self.fam_weights = fam_weights
        print(f'FAM Computing done({np.round(net_time,2)}s)')

    def linkCells(self,iou_threshold=0.2):

        i = 1

        #counter recursive error
        states_clone = copy.deepcopy(self.states)
        manager = multiprocessing.Manager()
        DATA = manager.dict()
        while(i < len(self.times)):
            printProgressBar(i,len(self.times))

            jobs = []
            for k in range(16):
                if(i+k<len(self.times)):
                    p = multiprocessing.Process(target=MPLinkProcess,args=(states_clone[i+k-1],states_clone[i+k],k,DATA,iou_threshold))
                    jobs.append(p)
            for j in jobs:
                j.start()
            for j in jobs:
                j.join()
            
            sorted_rslt = [[] for _ in range(len(list(DATA.values())))]
            for kl in list(DATA.values()):
                k = kl[0]
                sorted_rslt[k] = kl[1]
            for k,l in enumerate(sorted_rslt):
                if(i+k<len(self.times)):
                    for tpl in l:
                        cell = self.states[i+k][tpl[0]]
                        
                        cell.parent = self.states[i+k-1][tpl[1]]
                        cell.parent.children.append(cell)
                        cell.color = cell.parent.color
            i += len(list(DATA.values()))
            DATA.clear()

    def mergeSporadicsCells(self):
        for i in range(len(self.times)):
            s = self.states[i]
            for c in s:
                getCtrdGradient()
                




class Cell():
    """Contains the information about one cell at one time point"""
    def __init__(self,space,time,outline):
        self.time = time
        #space is the mask matrix  with only this cell (0: empty, 1: cell)
        self.space = np.clip(space,0,1)
        self.outline = outline
        self.rect = self.getRect(outline)
        self.center = None
        self.center = self.computeCenter()
        self.parent = None
        self.color = np.random.rand(3,)*0.6+0.4
        self.children = []

    def getRect(self, outline):
        T = np.array(outline).T
        return (np.max(T[0])-np.min(T[0]),np.max(T[1])-np.min(T[1]))

    def getCellTrajectory(self,past=True):
        cells_path = [[self]]
        cell_f = self
        while(past and not(cell_f.parent is None)):
            cell_f = cell_f.parent
            cells_path.insert(0,[cell_f])
        cell_f = self
        if(not(cell_f.children is None) and len(cell_f.children) > 0):
            trajs = []
            max_time = 0
            for c in cell_f.children:
                traj = c.getCellTrajectory(past=False)
                trajs.append(traj)
                max_time = max(len(traj),max_time)
            for i in range(max_time):
                l = []
                for t in trajs:
                    for q in t[i]:
                        l.append(q)
                cells_path.append(l)
        return cells_path
                
    def findParent(self,cells,iou_threshold=0.2,cell_index=0):
        score = []
        for i in range(len(cells)):
            cell = cells[i]
            if(np.linalg.norm(self.center - cell.center) >= 1.*(np.max(self.rect)+np.max(cell.rect))):
                score.append(0.)
                continue
            I = self.inter(cell)
            if(np.sum(I) <= 0):
                score.append(0.)
                continue
            U = self.union(cell)
            s = np.sum(I) / np.sum(U)

            if(s >= IOU_THRESHOLD_FORCE):
                score.append(s)
                break

            if(s < iou_threshold):
                score.append(0.)
            else:
                score.append(s)
        parent = cells[np.argmax(score)]
        #self.parent = parent
        #self.parent.children.append(self)
        #self.color = self.parent.color
        return (cell_index,np.argmax(score))
        


    def computeCenter(self,force=False):
        if(not(force) and not(self.center is None)):
            return self.center
        sp_shape = np.shape(self.space)
        pos = np.array([0,0])
        c = 0
        for i in range(sp_shape[0]):
            for j in range(sp_shape[1]):
                if(self.space[i,j] <= 0):
                    continue
                pos[0] += i
                pos[1] += j
                c += 1
        pos = pos / c
        return pos

    def union(self,cell2):
        if(not(verifyShape(self,cell2))):return
        return np.clip(self.space + cell2.space,0,1)
    def inter(self,cell2):
        if(not(verifyShape(self,cell2))):return
        
        rslt = self.space * cell2.space
        return rslt
    
    def computeFAMWeight(self):
        links = self.computeFAMWeight_Main()
        modif_links = []
        for l in links:
            modif_links.append((l[0],1/l[1]))
        return modif_links
    
    def computeFAMWeight_Main(self):
        c_f = self
        steps = 1
        links = []
        while(not(c_f.parent is None)):
            links.append((c_f.parent,steps))
            for child in c_f.parent.children:
                if(child.center[0]==c_f.center[0] and child.center[1]==c_f.center[1]):
                    continue
                rslt = child.computeFAMWeight_Sub()
                for tupl in rslt:
                    links.append((tupl[0],tupl[1]+steps))
            c_f = c_f.parent
            steps += 1
        steps = 1
        for child in self.children:
            rslt = child.computeFAMWeight_Sub()
            for tupl in rslt:
                links.append((tupl[0],tupl[1]+steps))
        return links
    
    def computeFAMWeight_Sub(self):
        links = []
        links.append((self,1))
        for child in self.children:
            rslt = child.computeFAMWeight_Sub()
            for tupl in rslt:
                links.append((tupl[0],tupl[1]+1))
        return links