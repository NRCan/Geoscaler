# -*- coding: cp1252 -*-
#-------------------------------------------------------------------------------
# Name:        M_2aPol_02
# Purpose:     Will generalize any raster with a majority filter.
#
# Author:      Gabriel Huot-Vézina (ghuotvez)
#
# Created:     03-10-2011
# Copyright:   (c) ghuotvez 2011
# Licence:     Laboratoire de Cartographie Numérique et Photogrammétrie,
#              Geological Survey Canada, Natural Resources Canada, Québec, Qc.
#-------------------------------------------------------------------------------
###NEEDS A SPATIAL ANALYST LICENCE

#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP
import arcpy.sa as APSA #For spatial analyst tools

#Import custom libraries
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class EnvironmentError(CustomError):pass #Child class

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputRaster = sys.argv[1] #The input raster to generalize
    Radius = int(sys.argv[2])#Moore's neighbourhood radius
    FinalIteration = int(sys.argv[3]) #Total iteration
    OutputRaster = sys.argv[4]#The generalization result output
    MinSize = sys.argv[5] #The minimal polygon size to the output
    OutputInterval = sys.argv[6] #The number of output if needed, at every X iteration, for testing purposes

    #Other variables
    NoDataValue = 0 #Temp value for no data values within output raster
    FieldCount = "Count" #The field name within region group raster that contains number of pixel per regions
    FieldValue = "Value" #The field namw within region group raster that contain ids
    IterLoop = 1 #The starting number for the while loop
    IterList = [] #An empty to contain the number at wich a real output will be available, instead of a temp one.
    DeleteList = []# A list to contain all temp output to delete after the process
    OutputName = string.split(os.path.basename(OutputRaster),".")[0][0:5] #Carater 0 to 4, the minimum is set within toolvalidator
    ToAnalyse = () #A tuple with the first value, the last iterated raster and second value the generalized output
    FilterType = "MAJORITY" #The type of filter to use within generalization
    Prefix = "Pol2" #A prefix for temp outputs
    SmallPolList = [] #A list of regions within raster that should be nibbled, because too small in area
    RemapRegion = [] #A list that contains the mapping of region raster
    RegionLinkField = "LINK" #Link field within region raster

    #-------------------------------------------------------------------
    #Verify Spatial Analyst licence
    #-------------------------------------------------------------------
    try:
        GeoScaler_functions.RequestLicence("Spatial")
    except:
        raise EnvironmentError

    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Manage null parameters
    if OutputInterval != "#":
        OutputInterval = int(OutputInterval)
    if MinSize != "#":
        MinSize = int(MinSize)

    #Set the moore's neighborhood radius (e.g. 1 radius = a window of 3X3 cells)
    MooreRadius = Radius * 2 + 1

    #Setting the output folder for output by intervals and temp data
    Workspace = os.path.dirname(OutputRaster)

    #Setting NoData value to another value, will help manage NoData later
    Scratch_null = AP.CreateScratchName(Prefix, "NULL", "RasterDataset", Script_path)
    ###Needs to be specified at least 2 element in RemapValue or else, NoData can't be mapped...
    Reclass = APSA.Reclassify(InputRaster, "VALUE", APSA.RemapValue([[0,0],["NoData", NoDataValue]]), "DATA")
    Reclass.save(Scratch_null)
    DeleteList.append(Scratch_null)

    #Managing output intervals
    if OutputInterval != "#":
        #Build a temp list
        TempList = range(FinalIteration)
        for numbers in TempList:
            ###Add 1 to numbers because TempList starts with a 0
            ###Select second item in tuple result from divmod
            ###For 10 iteration the list should look like [2,4,6,8] if user as selected an output at every 2 iterations
            if divmod(numbers + 1, OutputInterval)[1] == 0 and numbers + 1 != FinalIteration:
                IterList.append(numbers + 1)

    #-------------------------------------------------------------------
    #Generalization
    #-------------------------------------------------------------------
    while IterLoop <= FinalIteration:
        AP.AddMessage("Iteration: " + str(IterLoop) + ".")
        #-------------------------------------------------------------------
        #Prepare data
        #-------------------------------------------------------------------
        #Manage output paths
        OutputName_alpha = OutputName + "_" + str(IterLoop)
##        OutputPath_beta = Workspace + "\\" + OutputName_beta
##        OutputPath = Workspace + "\\" + OutputName_beta
        OutputPath = AP.CreateScratchName(OutputName_alpha, "", "RasterDataset", Workspace)

        #Manage data to analyse
        if IterLoop == 1:
            #Start with the scratch raster
            ToAnalyse = (Scratch_null, OutputPath)
        else:
            #Start with the last element of the list
            ToAnalyse = (ToAnalyse[1], OutputPath)

        #-------------------------------------------------------------------
        #Apply a majotiry filter
        #-------------------------------------------------------------------
        FocalMajority = APSA.FocalStatistics(ToAnalyse[0], \
                                             APSA.NbrRectangle(MooreRadius,MooreRadius,"CELL"), \
                                             FilterType, "DATA")
        FocalMajority.save(ToAnalyse[1])
        DeleteList.append(ToAnalyse[1])
        #-------------------------------------------------------------------
        #Eliminate small polygons
        #-------------------------------------------------------------------
        #For final iteration or output iterations
        if IterLoop in IterList or IterLoop == FinalIteration:
            #Manage outputs names
            if IterLoop < 10:
                OutputName_beta = OutputName + "_00" + str(IterLoop)
            elif IterLoop >= 10 and IterLoop < 100:
                OutputName_beta = OutputName + "_0" + str(IterLoop)
            elif IterLoop >= 100 and IterLoop < 1000:
                OutputName_beta = OutputName + "_" + str(IterLoop)

            #Manage output paths
            if IterLoop != FinalIteration:
                OutputPath = Workspace + "\\" + OutputName_beta
                #If something already exists
                if os.path.isfile(OutputPath) == True:
                    OutputPath = AP.CreateScratchName(OutputName_beta, "", "RasterDataset", Workspace)
##                DeleteList.append(OutputPath)
            else:
                OutputPath = OutputRaster

            #Reclassify generated NoData with temp NoData value (e.g. NoData to 9999 or 0)
            Scratch_null_beta = AP.CreateScratchName(Prefix, "NULL", "RasterDataset", Script_path)
            ###Needs to be specified at least 2 element in RemapValue or else, NoData can't be mapped...
            Reclass = APSA.Reclassify(ToAnalyse[1], "VALUE", APSA.RemapValue([[0,0],["NoData", NoDataValue]]), "DATA")
            Reclass.save(Scratch_null_beta)
            DeleteList.append(Scratch_null_beta)

            #Replace the previous 0s or 9999s from temp NoData value to real NoData, will serve as a mask to Nibble function
            Scratch_mask = AP.CreateScratchName(Prefix, "MASK", "RasterDataset", Script_path)
            SQL = '"' + FieldValue + '" <> ' + str(NoDataValue)
            ConMask = APSA.Con(ToAnalyse[1], ToAnalyse[1], "#", SQL)
            ConMask.save(Scratch_mask)
            DeleteList.append(Scratch_mask)

            #-------------------------------------------------------------------
            #Manage small polygons within raster, if necessary
            #-------------------------------------------------------------------
            #User doesn't want to remove small polygons
            if str(MinSize) == "#":

                #Nibble the results (replace NoData by it's neighbours)
                NibleOut = APSA.Nibble(Scratch_null_beta,Scratch_mask)
                NibleOut.save(OutputPath)

            #User wants to remove small polygons
            else:

                #Step 1: Assign a unique ID for each regions (polygons) in raster
                Scratch_step1 = AP.CreateScratchName(Prefix, "S1", "RasterDataset", Script_path)
                Region = APSA.RegionGroup(Scratch_mask, "FOUR","WITHIN","ADD_LINK")
                Region.save(Scratch_step1)
                DeleteList.append(Scratch_step1)

                #Step 2: Select small polygons
                Scratch_step2 = AP.CreateScratchName(Prefix, "S2", "RasterDataset", Script_path)
                ExtractS2 = APSA.ExtractByAttributes(Scratch_step1, '"' + FieldCount + '" >= ' + str(MinSize))
                ExtractS2.save(Scratch_step2)
                DeleteList.append(Scratch_step2)

##                #Step 2: Find small polygons
##                Scratch_step2 = AP.CreateScratchName(Prefix, "S2", "RasterDataset", Script_path)
##                SQL_S2 = '"' + FieldValue + '" >= ' + str(MinSize)
##                ConStep2 = APSA.Con(Scratch_step1, Scratch_step1, "#", SQL_S2)
##                ConStep2.save(Scratch_step2)
##                DeleteList.append(Scratch_step2)
##
##                #Step 3: Nibble the results (replace the values by it's neighbours)
##                NibleOut = APSA.Nibble(Scratch_step2,Scratch_mask)
##                NibleOut.save(OutputPath)

                #Simply nibble the results
                NibleOut = APSA.Nibble(Scratch_null_beta,Scratch_step2)
                NibleOut.save(OutputPath)

        #-------------------------------------------------------------------
        #Post managemnet
        #-------------------------------------------------------------------
        #Manage outputs
        if IterLoop in IterList:
            AP.AddWarning("Intermediate result available at: " + OutputPath)
        elif IterLoop == FinalIteration:
            AP.AddWarning("Final result available at: " + OutputPath)
        else:
            DeleteList.append(ToAnalyse[1])

        #Iterate IterLoop number
        IterLoop = IterLoop + 1

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    for files in DeleteList:
        try:
            AP.Delete_management(files)
        except:
            pass

except EnvironmentError:
    AP.AddError("No " + str(LicenceName) + " licence available, retry later.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
