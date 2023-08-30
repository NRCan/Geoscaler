# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2bPol_01.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will prepare input data, for later polygon generalization with cellular
#   automata.
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
    InputFeature = sys.argv[1]  #Input polygon feature layer
    Field = sys.argv[2] #Input polygon feature layer field (only num)
##    InputRaster = sys.argv[3] #If a user wants to convert a raster file instead of feature
    InputFaultFeature = sys.argv[3] #A fault feature
    EntireFeature = sys.argv[4] #A boolean value to know if the entire fault feature has to be analyse
    FieldFaults = sys.argv[5] #The field containing faults attribute
    FieldValueFaults = sys.argv[6] #The value of faults to analyse
    Cellsize = sys.argv[7] #Cellsize for the output grid
    OutputRaster = sys.argv[8] #Path and name for the output grid file.

    #Other variables
    RasterField = "VALUE" #Usually the default when converting feature layer to raster
    Prefix = "BED1POL"
    FeatureLayer = "FeatureLayer" #Will be use for selection purposes within input fault feature
    TempFaultField = "FAULTS" #Will be use if user want entire fault feature
    RasterList = [] #A list to contain the input rasters
    PixelType = "32_BIT_SIGNED"

    #-------------------------------------------------------------------
    #If a user wants to convert a faults
    #-------------------------------------------------------------------
    if InputFaultFeature != "#":
        #Create a layer file, for selection purposes
        AP.MakeFeatureLayer_management(InputFaultFeature, FeatureLayer)

        #If user has given a field and value:
        if EntireFeature == "false":
            #Select the fault class from input feature
            SQL = GeoScaler_functions.BuildSQL(InputFaultFeature,FieldFaults,FieldValueFaults)
            AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", SQL)
        else:
            #Adding a new temp field into the fault feature
            AP.AddField_management(FeatureLayer, TempFaultField, "SHORT")

            #Calculate within new field, value 9999
            AP.CalculateField_management(FeatureLayer, TempFaultField, 9999)

            #Rename the new field variable as the one entered by user
            FieldFaults = TempFaultField

            AP.AddWarning("Faults have been attributed code 9999 within input feature.")

        #Convert the faults into a temp raster
        Scratch_faults = AP.CreateScratchName(Prefix, "", "RasterDataset", Script_path)
        AP.PolylineToRaster_conversion(FeatureLayer, FieldFaults, Scratch_faults, "MAXIMUM_LENGTH", "#", Cellsize)

    #-------------------------------------------------------------------
    #If a user wants to convert a polygon feature
    #-------------------------------------------------------------------
    Scratch_geol = AP.CreateScratchName(Prefix, "", "RasterDataset", Script_path)
    AP.PolygonToRaster_conversion(InputFeature, Field, Scratch_geol, "MAXIMUM_AREA", "#", Cellsize)

    #-------------------------------------------------------------------
    #Create a new merged raster, from faults and/or polygons
    #-------------------------------------------------------------------
    #Raster name and paths
    OutputPath = os.path.dirname(OutputRaster)
    OutputName = os.path.basename(OutputRaster)
##    AP.AddWarning(OutputName + "," + OutputPath)

    if InputFaultFeature != "#":
        AP.MosaicToNewRaster_management([Scratch_geol, Scratch_faults],OutputPath, OutputName, "#", PixelType, Cellsize, "1", "LAST", "FIRST")
    else:
        AP.MosaicToNewRaster_management([Scratch_geol], OutputPath, OutputName, "#", PixelType, Cellsize, "1", "LAST", "FIRST")

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    if InputFaultFeature != "#":
        AP.Delete_management(Scratch_faults)
        AP.Delete_management(Scratch_geol)
    if InputFaultFeature == "#":
        AP.Delete_management(Scratch_geol)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
