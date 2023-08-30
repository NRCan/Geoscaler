# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2bPol_03.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will generalized data, ascii files, into vector files or rasters, in
#   addition to that, it is possible to cut the edges of the resulting vector
#   files with a given border.
# ---------------------------------------------------------------------------
#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP

#Import custom libraries
import GeoScaler_functions

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputRaster = sys.argv[1]  #Input ascii file to convert into raster or feature
    OutputFeature = sys.argv[2] #Output feature class to be created from ASCII file
    SmoothTolerance = sys.argv[3] #The smoothing tolerance for output
    InputBorderFeature = sys.argv[4] #A border to clip output feature

    #Other variables
    Prefix = "BED4POL"

    #-------------------------------------------------------------------
    #Convert raster to feature
    #-------------------------------------------------------------------
    #Create a temp feature name and path
    Scratch_convert= AP.CreateScratchName(Prefix, "CONV", "FeatureClass", Script_path)
    #Convert
    AP.RasterToPolygon_conversion(InputRaster, Scratch_convert, "NO_SIMPLIFY")

    #-------------------------------------------------------------------
    #Clip the output feature with a border feature
    #-------------------------------------------------------------------
    if InputBorderFeature != "#":
        #Create a temp feature name and path
        Scratch_clip_alpha = AP.CreateScratchName(Prefix, "CLIP", "FeatureClass", Script_path)
        Scratch_clip = AP.CreateScratchName(Prefix, "CLIP", "FeatureClass", Script_path)

        #Detect geometry of input border feature
        Desc = AP.Describe(InputBorderFeature)
        Geom = Desc.ShapeType

        #For input line feature
        if Geom == "Polyline":
            AP.FeatureToPolygon_management(Scratch_convert, Scratch_clip_alpha, "#", "ATTRIBUTES")
        else:
            Scratch_clip_alpha = Scratch_convert

        #Clip the feature
        AP.Clip_analysis(Scratch_clip_alpha, InputBorderFeature, Scratch_clip)

    else:
        Scratch_clip = Scratch_convert

    #-------------------------------------------------------------------
    #Smooth the feature if user wants it
    #-------------------------------------------------------------------
    if SmoothTolerance != "#":
        #Create a temp feature name and path
        Scratch_smooth = AP.CreateScratchName(Prefix, "SMOO", "FeatureClass", Script_path)
        #Smooth
        AP.SmoothPolygon_cartography(Scratch_clip, Scratch_smooth, "PAEK", SmoothTolerance, "FIXED_ENDPOINT", "FLAG_ERRORS")
    else:
        Scratch_smooth = Scratch_clip

    #-------------------------------------------------------------------
    #Copy the results into the output feature
    #-------------------------------------------------------------------
    AP.CopyFeatures_management(Scratch_smooth, OutputFeature)

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    #For all situations
    AP.Delete_management(Scratch_convert)

    #For a smoothed feature
    if SmoothTolerance != "#":
        AP.Delete_management(Scratch_smooth)

    #For a clipped feature
    if InputBorderFeature != "#":
        AP.Delete_management(Scratch_clip)

        #For a clipped polygon feature
        if Geom == "Polyline":
            AP.Delete_management(Scratch_clip_alpha)
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
