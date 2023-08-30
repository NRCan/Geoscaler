# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPnt_03.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will generalize point symbols like model M_2aSymPnt_01, also it will manage
#   symbols overlaping user given geological polygons.
# Original work: Gabriel H.V. (LCNP), 2009
###NEEDS ARCINFO LICENCE
# ---------------------------------------------------------------------------
#Import standard lib.
import sys, traceback, string, os
import arcpy as AP

#Import custom lib.
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class ArcInfoError(CustomError):pass #Child class

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1] #Feature to generalize
    BoolField = sys.argv[2] #For entire feature or not
    InputField = sys.argv[3] #Field that contains relative chronology of glacial striae between each others
    InputFieldValue = sys.argv[4]#Field that contains the flow direction of glacial striae
    NFD = sys.argv[5] #Value for known flow direction
    InputPolFeature = sys.argv[6] #Polygon faeture to base the generalization on.
    BoolPolField = sys.argv[7] #For entire polygon feature or not.
    InputPolField = sys.argv[8] #Value for the glacial striae length, in meters
    InputPolFieldValue = sys.argv[9] #Value for minimum tolerable angle between each striae

    #Variables
    PntFeatureLayer = "Pnt"
    PolFeatureLayer = "Pol"

    #-------------------------------------------------------------------
    #Verify the product licence, scripts need ArcInfo
    #-------------------------------------------------------------------
    if GeoScaler_functions.RequestArcInfo() != "":
        raise ArcInfoError

    #-------------------------------------------------------------------
    #Retrieve generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)

    #-------------------------------------------------------------------
    #Call generic model of point generalization
    #-------------------------------------------------------------------
    GeoScaler_functions.M_2aSymPnt_01(InputFeature, InputField, InputFieldValue, NFD, ScriptName)

    #-------------------------------------------------------------------
    #Analyse symbols over given polygons.
    #-------------------------------------------------------------------
    #Make feature layers with inputs
    AP.MakeFeatureLayer_management(InputFeature, PntFeatureLayer)
    AP.MakeFeatureLayer_management(InputPolFeature, PolFeatureLayer)

    #Select given polygons, if user entered one
    if InputPolField != "#":
        SQL_query = GeoScaler_functions.BuildSQL(InputPolFeature,InputPolField,InputPolFieldValue)
        AP.SelectLayerByAttribute_management(PolFeatureLayer, "NEW_SELECTION", SQL_query)

    #Proceed with a select by location analysis
    CountBefore = AP.GetCount_management(PntFeatureLayer)
    AP.SelectLayerByLocation_management(PntFeatureLayer, "INTERSECT", PolFeatureLayer, "#", "NEW_SELECTION")
    CountAfter = AP.GetCount_management(PntFeatureLayer)

    #Verify the integrity of the last selection
    if CountAfter != 0:
        AP.AddMessage("Number of symbol overlaping polygons: " + str(CountAfter))
        AP.CalculateField_management(PntFeatureLayer, ResultField, 0, "VB")

    else: #The selection returns nothing
        AP.AddWarning("No symbols were superposed with the given polygon class: " + InputPolField + " = " + InputPolFieldValue + ".")

    #-------------------------------------------------------------------
    #Delete temp data
    #-------------------------------------------------------------------
    AP.Delete_management(PntFeatureLayer)
    AP.Delete_management(PolFeatureLayer)

except ArcInfoError:
     AP.AddError("No ArcInfo licence available, retry later.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))