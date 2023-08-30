# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aPol_03.py
# Gabriel Huot-Vézina (LCNP), 2010
#   Will manage generalization data, like converting the grid into a vector
#   feature, or clipping the grid with a given border (frame).
# ---------------------------------------------------------------------------
###NOTE: A bug was found when output temp data are made within the script_path directory
###      By using this directory a shapefile is made automatically and returns
###      "Invalid void topology" error when it has to be clipped with a feature.
###      The temp outputs are now features to prevent bug.

#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP
import arcpy.sa as AP_SA #For spatial analyst tools

#Import custom libraries
import GeoScaler_functions

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputResultGrid = sys.argv[1]  #Generalization results obtain in Cellular automata model
    OutputFeature = sys.argv[2] #Path to output feature, resulting from conversion
    InputBorderFeature = sys.argv[3] #Path to input frame to clip OutputFeature

    #Other variables
    Prefix = "GS"
    TempGDB = Script_path + "\\" +Prefix + ".gdb"

    #-------------------------------------------------------------------
    #If a user doesn't want to clip the feature with a given border
    #-------------------------------------------------------------------
    AP.AddMessage("1. Beginning grid, from previous generalization, conversion into a feature...")

    if InputBorderFeature == "#":
        AP.RasterToPolygon_conversion(InputResultGrid, OutputFeature, "SIMPLIFY", "VALUE")

    #------------------------------------------------------------------------------
    #If a user wants to clip the feature
    #------------------------------------------------------------------------------
    else:

        #Create a temp file geodatabase
        AP.CreateFileGDB_management(Script_path, Prefix, "CURRENT")

        #Create the generalized geological feature
        Scratch_geol = AP.CreateScratchName(Prefix, "", "FeatureClass", TempGDB)
        AP.RasterToPolygon_conversion(InputResultGrid, Scratch_geol, "SIMPLIFY")

        AP.AddMessage("2. Beginning clip of output feature with given border...")

        #Detect the geometry of the input feature (polygon vs polyline)
        Border_desc = AP.Describe(InputBorderFeature)
        Border_geom = Border_desc.ShapeType #Even though the feature is not a shapefile.

        #If the input border is not a polygon
        if Border_geom != "Polygon":

            #Convert the line border into a polygon feature
            Scratch_border = AP.CreateScratchName(Prefix, "", "FeatureClass", TempGDB)
            AP.FeatureToPolygon_management(InputBorderFeature, Scratch_border, "#", "ATTRIBUTES")

            #Clip geological feature
            AP.Clip_analysis(Scratch_geol, Scratch_border,OutputFeature)

        else:
            #Clip geological feature
            AP.Clip_analysis(Scratch_geol, InputBorderFeature,OutputFeature)

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    if InputBorderFeature != "#":
        AP.Delete_management(Scratch_geol)
        if Border_geom != "Polygon":
            AP.Delete_management(Scratch_border)

    if os.path.isdir(TempGDB):
        AP.Delete_management(TempGDB)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
