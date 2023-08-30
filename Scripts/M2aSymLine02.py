# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymLine_02.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help generalizing individual line symbol classes by eliminating
#   short lines and it will manage symbols overlaping user given geological
#   polygons.
# Original work: Gabriel H.V. (LCNP), 2009
# ---------------------------------------------------------------------------

#Import standard libs.
import sys, traceback, string, os
import arcpy as AP

#Import custom libs.
import GeoScaler_functions

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1]  #Feature to generalize
    EntireFeature = sys.argv[2] #Model will be apply if the entire or a class is entered
    Field = sys.argv[3] #Feature field to generalize with
    FieldValue = sys.argv[4] #Feature field value, generalization will occur only on this class of symbol
    MTL = sys.argv[5] #Minimum tolerable length (m)
    InputPolFeature = sys.argv[6] #Polygon faeture to base the generalization on.
    EntirePolFeature = sys.argv[7] #For entire polygon feature or not.
    InputPolField = sys.argv[8] #Value for the glacial striae length, in meters
    InputPolFieldValue = sys.argv[9] #Value for minimum tolerable angle between each striae

    #-------------------------------------------------------------------
    #Retrieve and assign generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
##    GeoScaler_functions.VerifyResultingField(InputFeature, ResultField)

    #-------------------------------------------------------------------
    #Generalization
    #-------------------------------------------------------------------
    #Call custom function
    GeoScaler_functions.M_2aSymLine_01(InputFeature, Field, FieldValue, MTL, ScriptName)

    #-------------------------------------------------------------------
    #Analyse symbols over given polygons.
    #-------------------------------------------------------------------
    #Call custom function
    GeoScaler_functions.SymbolsOverPolygons(InputFeature, Field, FieldValue, InputPolFeature, InputPolField, InputPolFieldValue, ResultField)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
