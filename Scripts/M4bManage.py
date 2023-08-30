# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_4b_Manage.py
# Gabriel Huot-Vézina (LCNP), 2012
#   Will push into ArcMap TOC, user given layers separated by scale of "From To".
# ---------------------------------------------------------------------------
###NOTE, some functions are only available in 10.1 http://forums.arcgis.com/threads/46060-Setting-the-scale-range-using-Python-for-a-large-number-of-MXDs
###Check if possible to add new group layers...

#Import des librairies standards
import sys, traceback, string, os, shutil
import arcpy as AP

#Import custom libraries
from GeoScaler_functions import *

#Error handling classes
class CustomError(Exception): pass #Mother class
class CurrentProjectError(CustomError):pass #Child class

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    InputFeatures = sys.argv[1].split(";") #All features that needs to have the new fields

    #Variables
    ModelDictionnary = FieldDictionnary("Dictionnary")
    FromField = ResultFieldDictionnary("From") #Get name for SCALE_FROM field
    ToField = ResultFieldDictionnary("To") #Get name for SCALE_TO field
    LayerSource = [] #An empty list to store layer source path
    Breaker = True # A variable to detect if all given feature/layers are in current selected data frame
    CurrentDataFrame = "" #Will contain current data frame object
    LyrFilesFolderName = "LYR_FILES" #A folder to be created to contains .lyr files

    #-------------------------------------------------------------------
    #Access current Arc Map project
    #-------------------------------------------------------------------
    try:
        #Access mxd project
        mxd = AP.mapping.MapDocument("CURRENT")

        AP.AddMessage("\nCurrent ArcMap project: " + str(os.path.basename(mxd.filePath)))

        #Access data frame that contains all user given layers
        df = AP.mapping.ListDataFrames(mxd)[0]

    except:
        raise CurrentProjectError

    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Variables
    LyrFilesFolder = os.path.dirname(mxd.filePath) + "\\" + LyrFilesFolderName

    #Create a new folder (where mxd is stored) to contains soon to be created lyr files
    if not os.path.isdir(LyrFilesFolder):
        os.mkdir(LyrFilesFolder)

    #-------------------------------------------------------------------
    #Build a list of layer sources
    #-------------------------------------------------------------------
    #List layers within TOC
    layerList= AP.mapping.ListLayers(mxd)

    #Iterate through list to catch their source path
    for layers in layerList:
        if layers.name in InputFeatures:
            LayerSource.append(layers.dataSource)

    #-------------------------------------------------------------------
    #Iterate for all features
    #-------------------------------------------------------------------
    for features in LayerSource:

        #-------------------------------------------------------------------
        #Prepare data
        #-------------------------------------------------------------------
        #Get feature name
        FeatureName = os.path.basename(features)

        #Verify existence of From field and To Field
        FieldList_obj = AP.ListFields(features) #Get list of fields within feature
        FieldList = [] #A list to contain all fields within each features
        for objects in FieldList_obj:
            FieldList.append(objects.name)

        if FromField not in FieldList or ToField not in FieldList:
            AP.AddWarning("Given feature (" + FeatureName + ") doesn't include SCALE_FROM or SCALE_TO field. Process will be skipped for this feature.")
        else:
            AP.AddMessage("Processing script for feature: " + str(FeatureName))

            #-------------------------------------------------------------------
            #Create a .lyr file for each input features
            #-------------------------------------------------------------------
            ###This method will make possible the addition of multiple layers
            ###without interferring with the current layer stored in mxd TOC
            ###with the same name.

            #Lyr variables
            LyrFilePath = LyrFilesFolder + "\\" + FeatureName + ".lyr"

            #Output .lyr may already exists
            try:
                #Save to .lyr file
                AP.SaveToLayerFile_management(InputFeatures[LayerSource.index(features)], LyrFilePath, "RELATIVE")
            except:
                pass

            #-------------------------------------------------------------------
            #Extract unique values of each From To values in feature
            #-------------------------------------------------------------------
            #Call custom function
            UniqueValuesDictionnary = ExtractUniqueValuesByList_double(features, FromField, ToField)

            #Iterate through all values from dictionnary
            for fromValues in UniqueValuesDictionnary:
                #Iterate through values from current dictionnary key
                for toValues in UniqueValuesDictionnary[fromValues]:

                    #Setting other lyr values
                    CurrentLyr = AP.mapping.Layer(LyrFilePath)
                    CurrentLyr.visible = True
                    CurrentLyr.name = FeatureName + " => From " + str(fromValues) + " to " + str(toValues) + " scale."
                    CurrentLyr.definitionQuery = '"' + FromField + '" = ' + str(fromValues) + ' AND "' + ToField + '" = ' + str(toValues)

                    #Set up scale --> ONLY IN ARC 10.1
                    if AP.GetInstallInfo("desktop")["Version"] == "10.1": ###Return example: {'SPBuild':u'10.0.4.4000', ...}
                        try:
                            CurrentLyr.minScale = toValues
                            CurrentLyr.maxScale = fromValues
                        except:
                            pass

                    #Add new layer to TOC
                    AP.mapping.AddLayer(df, CurrentLyr)

    #-------------------------------------------------------------------
    #End script
    #-------------------------------------------------------------------
    #Delete folder containing lyr files
    shutil.rmtree(LyrFilesFolder)

    #Save current project
    mxd.save()
    AP.AddWarning("Current mxd project has been saved.\n")

except CurrentProjectError:
     AP.AddError("This script has to be run in Arc Map only.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))