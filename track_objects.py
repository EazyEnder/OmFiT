import numpy as np
import time
from utils import printProgressBar, outlines_list
from GlobalStorage import getRUN
import multiprocessing
import copy

"""Intersection over union threshold, if the IOU found is higher than this threshold, then the parent is found.
Make it equal to one if you dont want to force things."""
IOU_THRESHOLD_FORCE = 0.5

def MPLinkProcess(old_state,state,k,DATA,iou_threshold):
    """
    MP means 'MultiProcessing', this function allows the tracking of all cells at one time step
    """
    l = []
    for i,c in enumerate(state):
        l.append(c.findParent(old_state,iou_threshold=iou_threshold,cell_index=i))
    DATA[k] = (k,l)

def verifyShape(cell,cell2):
    """
    Verify if the space shape of cell1 is similar (same size) to the cell2 shape
    \n---
    \nTakes two cells as arguments
    \nReturn a flag
    """
    if(cell.space is None or cell2.space is None):
        print("Error: Cell space matrix not defined")
        return False
    if(np.shape(cell.space) != np.shape(cell2.space)):
        print("Error: Space matrix have not the same shape")
        return False
    return True

def createCellsUsingMask(mask,outlines,time):
    """
    Transform a mask matrix to usables cells
    \n-------------------
    \n Args: mask:matrix, outlines:array of vec2, time:integer
    \n Return the cells created using the mask in a array
    """
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
    """Manages all the frames and gives coherence
    \n---------------------
    \n Args: Masks: array of matrix, outlines:Matrix of vec2, times:array of int, iou: float, auto_init:boolean
    """
    def __init__(self,masks,outlines,times=None,iou_threshold=0.2,auto_init=True):
        if(times is None):
            times=range(1,len(masks)+1)
        self.times = times
        self.iou_threshold = iou_threshold
        self.masks = masks
        self.outlines = outlines
        

        self.states = []
        if auto_init:
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

    def clone(self):
        """Return a complete clone of the clip. It is better to use this than the deepcopy
          method because deepcopy method can (will) drop a recursive error."""
        times = copy.deepcopy(self.times)
        iou_threshold = self.iou_threshold
        masks = copy.deepcopy(self.masks)
        outlines = self.outlines
        cloned_clip = Clip(masks,outlines,times,iou_threshold,auto_init=False)

        cloned_states = []
        for i,state in enumerate(self.states):
            c_state = []
            for j,cell in enumerate(state):
                c_state.append(cell.clone())
            cloned_states.append(c_state)
        
        for i,state in enumerate(self.states):
            for j, cell in enumerate(state):
                parent_index = None
                if(not(cell.parent is None)):
                    parent_index = self.getCellIndex(cell.parent,i-1)
                children_indexes = []
                for child in cell.children:
                    children_indexes.append(self.getCellIndex(child,i+1))
                cloned_cell = cloned_states[i][j]
                if not(parent_index is None) and parent_index > -1:
                    cloned_cell.parent = cloned_states[i-1][parent_index]
                for child_index in children_indexes:
                    if not(child_index is None) and child_index > -1 :
                        cloned_cell.children.append(cloned_states[i+1][child_index])
        cloned_clip.states = cloned_states

        return cloned_clip

    def post(self):
        """Apply corrections to the data and compute some utils stuffs"""
        for i in range(1):
            print("Verify " + str(i))
            tic = time.time()
            self.verifyCells()
            self.clearLinks()
            self.linkCells(iou_threshold=self.iou_threshold)
            net_time = time.time() - tic
            print(f'Cells Verif done ({np.round(net_time,2)}s)')

        print("FAM Weights")
        fam_weights = []
        tic = time.time() 
        for m in range(len(self.masks)):
            printProgressBar(m,len(self.masks))
            l = []
            for cell in self.states[m]:
                l.append((cell,cell.computeFAMWeight()))
            fam_weights.append(l)
        net_time = time.time() - tic
        self.fam_weights = fam_weights
        print(f'FAM Computing done({np.round(net_time,2)}s)')

    def buildMask(self,time):
        """Return a new mask matrix using cells"""
        spaces = [c.space for c in self.states[time]]
        mask = np.zeros(np.shape(spaces[0]))
        for i,s in enumerate(spaces):
            mask = mask+s*(i+1)
        return mask

    def getAllCells(self):
        """Return all the cells and their time in the clip (tuple: [times, cells]) """
        cells = []
        times = []
        for m in range(len(self.states)):
            for cell in self.states[m]:
                cells.append(cell)
                times.append(m)
        return (times,cells)
    
    def removeCell(self,time,cell):
        """Remove a specific cell that is present at t=time"""
        cells = self.states[time-1]
        new_cells = []
        for c in cells:
            if(np.linalg.norm(c.center-cell.center) <= 0.1):
                continue
            new_cells.append(c)
        self.states [time-1] = new_cells

    def addCell(self,time,cell):
        """Add a new cell to the time t=time"""
        self.states[time-1].append(cell)

    def verifyCells(self):
        """Verify all the cells and apply corrections.
        \n For example two cells merging is impossible so we force the cells to stay divided."""
        cloned_clip = self.clone()
        times,cells = cloned_clip.getAllCells()
        index_todivide = []
        for i in times:
            index_todivide.append([])
        for i,cell in enumerate(cells):
            #Check sporadic cells
            if(cell.parent is None and len(cell.children) <= 0):
                self.removeCell(times[i],cell)

            if(cell.parent is None):
                continue
            if(cell.parent.parent is None):
                continue
            if(len(cell.children) < 2):
                if(len(cell.children) >= 1):
                    if(len(cell.children[0].children) < 2):
                        continue
                else:
                    continue
            parent2 = cell.parent.parent
            parent_used = parent2
            up_chi = parent2.children
            ancestor=2
            flag = False
            while(ancestor < 5 and not(flag)):
                if(len(up_chi) < 2):
                    if(parent_used.parent is None):
                        flag = True
                        break
                    ancestor += 1
                    parent_used = parent_used.parent
                    up_chi = parent_used.children
                    if(len(up_chi)>=2):
                        break
                else:
                    break
            if flag:
                continue
            if(len(up_chi)<2):
                continue
            children_surf = np.sum([child.surface for child in up_chi])
            if(cell.surface < children_surf*.25):
                continue
            print("Pre "+str(times[i]) + " wth ancestor " + str(ancestor))
            index_todivide[times[i]].append((ancestor,self.getCellIndex(cell,times[i])))
        for t in times:
            for ancestor,c in index_todivide[t]:
                cloned_clip.states[t][c].forcedDivide(ancestor=ancestor)

    def getCellIndex(self,cell,time):
        """Return the position of the cell in the state array"""
        for i,c2 in enumerate(self.states[time]):
            if(np.linalg.norm(c2.center-cell.center) < 0.01 and
               abs(c2.surface-cell.surface) < 0.01):
                return i
        return None
    
    def clearLinks(self):
        """Reset all parents/children links"""
        for s in self.states:
            for c in s:
                c.parent = None
                c.children = []
            
    def linkCells(self,iou_threshold=0.2):
        """Track the cells through time and find parent and children for each cell"""
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
                        
                        if(tpl[1] >= 0):
                            cell.parent = self.states[i+k-1][tpl[1]]
                            cell.parent.children.append(cell)
                            cell.color = cell.parent.color
            i += len(list(DATA.values()))
            DATA.clear()

class Cell():
    """Contains the information about one cell at one time point"""
    def __init__(self,space,time,outline,auto_init=True):
        self.time = time
        #space is the mask matrix  with only this cell (0: empty, 1: cell)
        self.space = np.clip(space,0,1)
        self.outline = outline

        self.divisions = None
        self.center = None
        self.surface = None
        self.rect = None
        self.direction = None
        

        if auto_init:
            self.surface = self.getSurface()
            self.rect = self.getRect(outline)
            self.direction = self.getDirection(outline)
            self.center = self.computeCenter()
        self.color = np.random.rand(3,)*0.6+0.4
        self.parent = None
        self.children = []

    def clone(self):
        """Return a copy of the cell without parent and children."""
        time = self.time
        space = self.space
        outline = self.outline
        cloned_cell = Cell(space, time, outline, auto_init=False)
        cloned_cell.center = self.center
        cloned_cell.surface = self.surface
        cloned_cell.rect = self.rect
        cloned_cell.direction = self.direction
        cloned_cell.color = self.color
        cloned_cell.divisions = self.divisions
        return cloned_cell

    def isNeighborTo(self,cell):
        """Verify if a cell is close to another"""
        for i,o1 in enumerate(self.outline):
            for j in range(i+1,len(cell.outline)):
                o2 = cell.outline[j]
                if(np.linalg.norm(np.array(o1)-np.array(o2)) < 5):
                    return True
        return False

    def getSurface(self):
        """Return the surface of one cell.
        The surface is the ratio of the surface (squared pixels) of the cell on the total surface of the img"""
        empty_area = 0
        filled_area = 0
        total_area = np.shape(self.space)[0]*np.shape(self.space)[1]
        for i in range(np.shape(self.space)[0]):
            for j in range(np.shape(self.space)[1]):
                if(self.space[i,j] <= 0):
                    empty_area += 1
                else:
                    filled_area += 1
        return filled_area/total_area

    def getDirection(self, outline):
        """Return an approximation of the privilegied direction of the cell"""
        max_rect_dist = np.max(self.rect)
        dist = []
        for i in range(len(outline)):
            p1 = outline[i]
            local_dist = []
            for j in range(i+1,len(outline)):
                p2 = outline[j]
                d = np.linalg.norm(p1-p2)
                if(d < max_rect_dist*.1):
                    continue
                local_dist.append([j,d])
            if(len(local_dist) > 0):
                local_dist = np.array(local_dist)
                sorted_local_dist = local_dist[np.argsort(local_dist.T[1])][-1]
                dist.append([(i,int(sorted_local_dist[0])),sorted_local_dist[1]])
        raw_indexes = np.array([d[0] for d in dist])
        raw_distances = np.array([d[1] for d in dist])
        args_indices = np.argsort(raw_distances)
        indexes = raw_indexes[args_indices][-1]
        return np.array(outline[indexes[0]]-outline[indexes[1]])
    
    def forcedDivide(self,ancestor):
        """Force a cell to divide"""
        if(self.parent is None):
            print("Warning: Cell cant divide bcs has no parent  -> abord division")
            return
        parent = self
        for _ in range(ancestor):
            if(parent.parent is None):
                print("Warning: Cell cant divide bcs ancestor " + str(ancestor) + " doesnt exist  -> abord division")
                return
            parent = parent.parent
        divs = parent.getApproximateDivisions()
        if(divs is None or len(divs) < 1):
            print("Warning, no divisions -> abord division")
            return
        inters = [div[0] for div in divs]
        div_vectors = [div[1] for div in divs]
        #sorted_indices = np.argsort(inters[:,0])
        #inters = inters[sorted_indices]
        div_vectors = div_vectors

        #list of spaces, one for each new cell child
        #rslt_spaces = self.cutSpaceUsingLines(inters,div_vectors,f_inter=parent.center)
        rslt_spaces = self.cutSpaceUsingLines(inters,div_vectors)
        for space in rslt_spaces:
            if(np.sum(space) == 0.):
                print("Warning, a cell is removed bcs mask is empty")
                continue
            if(len(outlines_list(space)[0]) < 1):
                print("Warning, a cell is removed bcs has no outlines")
                continue
            cell = Cell(space,self.time,outlines_list(space)[0])
            getRUN().clip.addCell(self.time,cell)
            print("Post " + str(self.time-1))
        if(len(rslt_spaces) <= 0):
            print("Warning, no spaces created using lines cut  -> abord division")
            return 
        getRUN().clip.removeCell(self.time,self)
            
    def cutSpaceUsingLines(self,inters,dirs,f_inter=None):
        """return the spaces created using lines"""
        spaces = [copy.deepcopy(self.space)]
        for k in range(len(inters)):
            I = inters[k]
            if(not(f_inter is None)):
                I = f_inter
            D = dirs[k]
            m_spaces = []
            angle_dir = np.arctan2(D[1], D[0])
            if(angle_dir < 0):
                angle_dir += np.pi
            for space in spaces:
                n1_space = np.zeros(np.shape(space))
                n2_space = np.zeros(np.shape(space))
                for i in range(len(space)):
                    for j in range(len(space[i])):
                        P = np.array([i,j])- I
                        angle = np.arctan2(P[1], P[0]) - angle_dir
                        s = space[i,j]
                        if(s <= 0):
                            continue
                        if(angle < 0):
                            n1_space[i,j] = 1
                        else:
                            n2_space[i,j] = 1
                if(np.sum(n1_space) > 0):
                    m_spaces.append(n1_space)
                if(np.sum(n2_space) > 0):
                    m_spaces.append(n2_space)
            spaces = m_spaces
        return spaces

    def getDivisions(self,force=False):
        """Return list of tpl [...,(intersection:vec2,direction:vec2)] """
        if(len(self.children) <= 1):
            return None
        if(not(self.divisions is None) and not(force)):
            return self.divisions
        #[ (Intersection, Direction) , ... ]
        divs = []
        print(self.children)
        for i in range(len(self.children)):
            c1 = self.children[i]
            for j in range(i+1,len(self.children)):
                c2 = self.children[j]
                if(not(c1.isNeighborTo(c2))):
                    continue
                
                #get contact outlines
                border_points = []
                distances = []
                for i,pos1 in enumerate(c1.outline):
                    for j in range(i+1,len(c2.outline)):
                        pos2 = c2.outline[j]
                        distance = np.linalg.norm(pos1-pos2) 
                        if distance <= np.sqrt(min(c1.surface, c2.surface))*0.2:
                            border_points.append([pos1,pos2])
                            distances.append(distance)

                if len(distances) <= 1:
                    continue

                sorted_indexes = np.argsort(np.array(distances))
                border_points = border_points[sorted_indexes]
                distances = distances[sorted_indexes]

                points = []
                for bp in border_points:
                    if not(bp[0] in points):
                        points.append(bp[0])
                    if not(bp[1] in points):
                        points.append(bp[1])

                #Test 1: Intersection is mean of points
                intersection = np.sum(points)/len(points)

                #Using covariance/fit ???
                #mean = np.mean(points)
                #sum = np.zeros(2)
                #for p in points:
                #    sum.append((p - mean) @ (p - mean).T)
                #covariance = 1/len(points)*sum
                #eigenvalues, eigenvectors = np.linalg.eig(covariance)

                #Using derivative
                pts1 = border_points[0]
                pts2 = border_points[1]
                direction = pts1[0]-pts2[0]
                if np.linalg.norm(direction) <= 0.001:
                    direction = pts2[0]-pts2[1]
                    if np.linalg.norm(direction) <= 0.001:
                        direction = pts1[0]-pts2[1]
                direction = direction/np.linalg.norm(direction)

                print("ttttt")

                divs.append((intersection,direction))
        print(divs)
        self.divisions = divs
        return divs

              
    def getApproximateDivisions(self,force=False):
        """Return list of tpl [...,(intersection:vec2,direction:vec2)] """
        if(len(self.children) <= 1):
            return None
        if(not(self.divisions is None) and not(force)):
            return self.divisions
        #[ (Intersection, Direction) , ... ]
        divs = []
        for i in range(len(self.children)):
            c1 = self.children[i]
            for j in range(i+1,len(self.children)):
                c2 = self.children[j]
                if(np.linalg.norm(c1.center-c2.center) < 0.01*np.max(self.rect)):
                    continue
                if(not(c1.isNeighborTo(c2))):
                    continue
                ce_1 = c1.center
                ce_2 = c2.center
                dir_1 = c1.direction
                dir_2 = c2.direction
                n1 = ce_1[1]-ce_2[1]-dir_2[1]/dir_2[0]*(ce_1[0]-ce_2[0])
                n2 = dir_1[0]*dir_2[1]/dir_2[0]-dir_1[1]
                lambda_1 = n1/n2
                lambda_2 = (ce_1[0]-ce_2[0]+lambda_1*dir_1[0])/dir_2[0]
                intersection = ce_1+lambda_1*dir_1
                if lambda_1*lambda_2 > 0:
                    dir_2 = -np.array(dir_2)

                if(np.linalg.norm(dir_1) == 0):
                    direction = dir_2
                elif(np.linalg.norm(dir_2) == 0):
                    direction = dir_1
                else:
                    direction = dir_1/np.linalg.norm(dir_1)+dir_2/np.linalg.norm(dir_2)
                    
                if(np.linalg.norm(direction) == 0):
                    direction = np.array([dir_1[1],-dir_1[0]])
                
                direction = direction/np.linalg.norm(direction)
                #Actually intersection calculation using directions approximations is too far from the 
                #real intersection so we use the mean center instead.
                intersection = (c1.center+c2.center)/2
                divs.append((intersection,direction))
        self.divisions = divs
        return divs

    def getRect(self, outline):
        """Return the minimum boudingbox containing the cell"""
        T = np.array(outline).T
        return (np.max(T[0])-np.min(T[0]),np.max(T[1])-np.min(T[1]))

    def getCellTrajectory(self,past=True):
        """Not used. Follow the cell through time / Return a cell history"""
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
        """Find the parent of a cell using 'Intersection Over Union' method"""
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

        if(np.max(score) <= 0):
            return (cell_index,-1)
        
        #parent = cells[np.argmax(score)]
        #self.parent = parent
        #self.parent.children.append(self)
        #self.color = self.parent.color
        return (cell_index,np.argmax(score))
        
    def computeCenter(self,force=False):
        """Find the center of a cell using his shape"""
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
        """Apply the union operator for this cell and another"""
        if(not(verifyShape(self,cell2))):return
        return np.clip(self.space + cell2.space,0,1)
    def inter(self,cell2):
        """Apply the intersection operator for this cell and another"""
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