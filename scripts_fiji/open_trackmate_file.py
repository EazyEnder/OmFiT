"""
Fiji script: Open trackmate xml file
"""

#Path to the xml file, if the img linked to the file is None then the img that will be opened is SAME_ROOT/SAME_NAME.tif
FILE_PATH = '/media/irina/5C00325A00323B7A/Zack/data/export/wt5c13/wt5c13_continuity1706.xml'

#If the spots just appears on the first frame, this means that the dimensions are switched (Z <-> T) so change the boolean.
CHANGE_DIMENSIONS = False

#----------------------------------------------------------------

from ij import IJ, ImagePlus, ImageStack
from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
from fiji.plugin.trackmate.io import TmXmlReader
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate.gui.wizard.descriptors import ConfigureViewsDescriptor
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui import Icons
from fiji.plugin.trackmate.gui import GuiUtils;
from fiji.plugin.trackmate import TrackMate
from java.io import File
import sys
from ij.plugin.frame import RoiManager 
from fiji.plugin.trackmate.gui.wizard import TrackMateWizardSequence 

reload(sys)
sys.setdefaultencoding('utf-8')

file = File( FILE_PATH )
logger = Logger.IJ_LOGGER

reader = TmXmlReader( file )
if not reader.isReadingOk():
    sys.exit(reader.getErrorMessage())
    
model = reader.getModel()
sm = SelectionModel(model)
ds = reader.getDisplaySettings()

spots = model.getSpots()

#rm = RoiManager.getInstance()
#if not rm:
#	rm = RoiManager()

imp = reader.readImage()
if imp is None:
	imp = IJ.openImage(FILE_PATH.split(".")[0]+".tif")
if CHANGE_DIMENSIONS:
	imp_dims = imp.getDimensions()
	imp.setDimensions(imp_dims[2], imp_dims[4], imp_dims[3]) 
imp.show()
settings = reader.readSettings( imp )

displayer =  HyperStackDisplayer(model, sm, imp, ds)
displayer.render()

panelIdentifier = reader.getGUIState();

if panelIdentifier is None:
	panelIdentifier = ConfigureViewsDescriptor.KEY;

trackmate = TrackMate(model, settings)
sequence = TrackMateWizardSequence( trackmate, sm, ds);
sequence.setCurrent( panelIdentifier );
frame = sequence.run( "TrackMate on " + settings.imp.getShortTitle() );
frame.setIconImage( Icons.TRACKMATE_ICON.getImage() );
GuiUtils.positionWindow( frame, imp.getWindow() );
frame.setVisible( True );