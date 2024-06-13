SIZE=250

from ij.plugin.frame import RoiManager
from ij import IJ

rm = RoiManager.getRoiManager()
IJ.run("To ROI Manager", "")

for i in range(SIZE):
	rm.select(i)
	rm.setGroup(i+1)
	rm.setPosition(0)

IJ.run("Multi-class mask(s) from Roi(s)", "show_mask(s) save_mask(s) save_in=/media/irina/5C00325A00323B7A/Zack/data/masks/ suffix=_mask save_mask_as=tif rm=[RoiManager[size=8, visible=true]]")
