"""
Fiji script: An interface that allows the user to dynamically merge/divide cells or even remove a slice & preserving the json structure
"""

from javax.swing import JFrame, JButton, JOptionPane, JPanel
from ij import IJ, WindowManager as WM
import math

from ij.plugin.frame import RoiManager 
from ij.gui import Roi,PolygonRoi

LOG = False
  
def divide(event):  

  imp = WM.getCurrentImage()
  if not(imp):
  	print "Open an image first."
  	if LOG:
  		IJ.log("Open an image first.")
  	return
  	
  rm = RoiManager.getInstance()
  if not(rm):
  	print "Open ROI Manager first."
  	if LOG:
  		IJ.log("Open ROI Manager first.")
  	return
  
  selection = rm.getSelectedRoisAsArray()
  if not(len(selection) == 1):
  	print "You need to select only 1 ROIs"
  	if LOG:
  		IJ.log("You need to select only 1 ROIs")
  	return
  	
  line = imp.getRoi()
  if not(line):
  	print "You need to draw a line first"
  	if LOG:
  		IJ.log("You need to draw a line first")
  	return
  if not(line.isLine):
  	print "Selection isn't a line"
  	if LOG:
  		IJ.log("Selection isn't a line")
  	return
  
  D = (line.x2 - line.x1, line.y2 - line.y1)
  
  cell = selection[0]
  X = cell.getXCoordinates()
  Y = cell.getYCoordinates()
  
  ROI1_X = []
  ROI1_Y = []
  ROI2_X = []
  ROI2_Y = []
  angle_dir = math.atan2(D[1],D[0])
  for i in range(len(X)):
  	x = X[i]+cell.getBoundingRect().x
  	y = Y[i]+cell.getBoundingRect().y
  	P = (x-line.x1,y-line.y1)
  	angle = math.atan2(P[1], P[0]) - angle_dir
  	print angle
  	if angle < 0:
  		ROI1_X.append(x)
  		ROI1_Y.append(y)
  	else:
  		ROI2_X.append(x)
  		ROI2_Y.append(y)
  	
  ROI1 = PolygonRoi(ROI1_X,ROI1_Y,len(ROI1_X),Roi.POLYGON)
  ROI2 = PolygonRoi(ROI2_X,ROI2_Y,len(ROI2_X),Roi.POLYGON)
  
  slice_number = cell.getPosition()
  ROI1.setPosition(slice_number)
  ROI2.setPosition(slice_number)
  
  rm.runCommand('Delete')
  rm.addRoi(ROI1)
  rm.addRoi(ROI2)
  IJ.log("ROI divided")
  
def merge(event):
	imp = WM.getCurrentImage()
	if not(imp):
		print "Open an image first."
		if LOG:
			IJ.log("Open an image first.")
		return
		
	rm = RoiManager.getInstance()
	if not(rm):
		print "Open ROI Manager first."
		if LOG:
			IJ.log("Open ROI Manager first.")
		return
	
	selection = rm.getSelectedRoisAsArray()
	if len(selection) < 2:
		print "You need to select only 2 ROIs at least"
		if LOG:
			IJ.log("You need to select only 2 ROIs")
		return
	
	rm.runCommand('Combine')
	rm.runCommand('Add')
	rm.runCommand('Delete')
	IJ.log("ROIs merged")
	
def openTrackMate(event):
	imp = WM.getCurrentImage()
	if not(imp):
		print "Open an image first."
		if LOG:
			IJ.log("Open an image first.")
		return
		
	rm = RoiManager.getInstance()
	if not(rm):
		print "Open ROI Manager first."
		if LOG:
			IJ.log("Open ROI Manager first.")
		return
		
	
		
  

#/--------------Interface------------------/
frame = JFrame("Repair GUI", visible=True)  
divide_button = JButton("Divide", actionPerformed=divide)
merge_button = JButton("Merge", actionPerformed=merge)  
remove_frame_button = JButton("Remove frame", actionPerformed=divide)  
open_trackmate_button = JButton("Open TrackMate", actionPerformed=openTrackMate)
#Add a button to add a custom selection to ROI

panel = JPanel()
panel.add(divide_button)
panel.add(merge_button) 
#panel.add(remove_frame_button) 
panel.add(open_trackmate_button)
frame.add(panel)
frame.pack() 