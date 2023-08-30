# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymLine_05.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help smooth polylines, with a selection or not.
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
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputFeature = sys.argv[1]  #Feature to generalize
    EntireFeature = sys.argv[2] #If user wants to smooth with a symbol class or not
    Field = sys.argv[3] #Feature field to generalize with
    FieldValue = sys.argv[4] #Feature field value for the main symbol
    SmoothTolerance = int(sys.argv[5]) #Field that contains symbol ids from both symbol class, optional
    OutputFeature = sys.argv[6] #Minimum tolerable length (m)

    #Other variables
    FeatureLayer = "FeatureLayer" #To perform selection within input feature
    Prefix = "D05" #For temp data

    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Create feature layer
    AP.MakeFeatureLayer_management(InputFeature, FeatureLayer)

    #If a symbol class is required by user
    if EntireFeature == "false":
        #Build SQL query
        SQL = GeoScaler_functions.BuildSQL(InputFeature,Field,FieldValue)
        #Select symbol class
        AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", SQL)

    #-------------------------------------------------------------------
    #Smooth feature layer
    #-------------------------------------------------------------------
    #Create a temp feature name
    Scratch_feature = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

    #Smooth
    if EntireFeature == "false": #For symbol class
        AP.SmoothLine_cartography(FeatureLayer, Scratch_feature, "PAEK", SmoothTolerance, "True", "NO_CHECK")
    else: #For entire feature
        AP.SmoothLine_cartography(FeatureLayer, OutputFeature, "PAEK", SmoothTolerance, "True", "NO_CHECK")

    #-------------------------------------------------------------------
    #Append result to entire feature
    #-------------------------------------------------------------------
    if EntireFeature == "false":
        #Invert selection from feature layer
        AP.SelectLayerByAttribute_management(FeatureLayer, "SWITCH_SELECTION")

        #Create a temp name for feature copy
        Scratch_copy = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

        #Copy feature into a temp one
        AP.CopyFeatures_management(FeatureLayer, OutputFeature)

        #Append last smoothed feature with the output copy
        AP.Append_management([Scratch_feature], OutputFeature, "NO_TEST")

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in output feature: " + str(OutputFeature)+".")

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
