import sys

from ij import IJ
from ij import WindowManager

from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.omnipose import OmniposeDetectorFactory
from fiji.plugin.trackmate.omnipose.OmniposeSettings import PretrainedModelOmnipose
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.features.track import TrackIndexAnalyzer

import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.visualization.trackscheme.TrackScheme as TrackScheme
from fiji.plugin.trackmate.gui.wizard import WizardController

reload(sys)
sys.setdefaultencoding('utf-8')

imp = WindowManager.getCurrentImage()
imp.show()

model = Model()

model.setLogger(Logger.IJ_LOGGER)



#------------------------

settings = Settings(imp)

settings.detectorFactory = OmniposeDetectorFactory()
settings.detectorSettings = {
    'OMNIPOSE_MODEL_FILEPATH' : "",
    'OMNIPOSE_PYTHON_FILEPATH' : "/home/irina/miniconda3/envs/omnipose_fiji/bin/python",
    'OMNIPOSE_MODEL': PretrainedModelOmnipose.BACT_PHASE,
    'TARGET_CHANNEL' : 1,
    'USE_GPU' : False,
    'CELL_DIAMETER' : 30.,
    'OPTIONAL_CHANNEL_2' : -1, 
    'SIMPLIFY_CONTOURS' : False,
} 

filter1 = FeatureFilter('AREA', 66, True)
settings.addSpotFilter(filter1)


settings.trackerFactory = SparseLAPTrackerFactory()
settings.trackerSettings = settings.trackerFactory.getDefaultSettings() 
settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
settings.trackerSettings['ALLOW_TRACK_MERGING'] = False

settings.addAllAnalyzers()

filter2 = FeatureFilter('TRACK_DISPLACEMENT', 0, True)
settings.addTrackFilter(filter2)



trackmate = TrackMate(model, settings)


ok = trackmate.checkInput()
if not ok:
    sys.exit(str(trackmate.getErrorMessage()))

ok = trackmate.process()
if not ok:
    sys.exit(str(trackmate.getErrorMessage()))


selectionModel = SelectionModel( model )

ds = DisplaySettingsIO.readUserDefault()
ds.setTrackColorBy( TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX )
ds.setSpotColorBy( TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX )

displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
displayer.render()
displayer.refresh()

trackScheme = TrackScheme(model, selectionModel, ds)
trackScheme.render()

model.getLogger().log( str( model ) )
