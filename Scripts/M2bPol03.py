# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2bPol_03.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will transform ascii files into rasters, in
#   addition to that, it is possible to delete faults, remove small regions
#   and preserved codes when removing small regions.
# ---------------------------------------------------------------------------
#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP
import arcpy.sa as APSA

#Import custom libraries
import GeoScaler_functions

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputRaster = sys.argv[1]  #Input ascii file to convert into raster or feature
    OutputRaster = sys.argv[2] #An output raster
    RemoveFaults = sys.argv[3] #List of code of fault cells to be remove from output
    RemovePolygons = sys.argv[4] #The number of cells to be removed from raster, as too smal polygons
    PreservedCodes = sys.argv[5] #List of code of polygons to be preserved, eg. dykes

    #Other variables
    Prefix = "BED3POL" #For temp data names
    NoDataValue = 0 #Temp value for no data values within output raster
    PixelType = "32_BIT_SIGNED"
    FieldCount = "Count" #The field name within region group raster that contains number of pixel per regions
    FieldValue = "Value" #The field namw within region group raster that contain ids
    SmallPolList = [] #A list of regions within raster that should be nibbled, because too small in area
    RemapRegion = [] #A list that contains the mapping of region raster
    RegionLinkField = "LINK" #Link field within region raster
    DeleteList = []# A list to contain all temp output to delete after the process
    Script_path = "in_memory"
    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Manage multiple values for faults codes and/or preserved codes
    if ";" in RemoveFaults:
        FaultList = RemoveFaults.split(";")
    elif "#" not in RemoveFaults:
        FaultList = [RemoveFaults]
    else:
        FaultList = RemoveFaults

    if ";" in PreservedCodes:
        PreservedList = PreservedCodes.split(";")
    elif "#" not in PreservedCodes:
        PreservedList = [PreservedCodes]
    else:
        PreservedList = PreservedCodes

    #-------------------------------------------------------------------
    #Manage NULL values within raster
    #-------------------------------------------------------------------
    AP.AddMessage("\nManaging null values within raster.")
    Scratch_null = AP.CreateScratchName(Prefix, "NULL", "RasterDataset", Script_path)
    ###IsNull() function will result in a raster with 0 and 1 where there was NoData
    ###The result can be used with Con() function, 1 values are considered as true
    ###and 0 values are considered as false.
    Con = APSA.Con(APSA.IsNull(InputRaster), NoDataValue, InputRaster)
    Con.save(Scratch_null)
    DeleteList.append(Scratch_null)

    #-------------------------------------------------------------------
    #Manage Faults and/or Preserved code values within raster by creating masks
    #-------------------------------------------------------------------
    AP.AddMessage("Managing faults and/or preserved codes.")

    #Create a scratch name for the mask
    Scratch_mask_alpha = AP.CreateScratchName(Prefix, "MaskA", "RasterDataset", Script_path)
    Scratch_mask_beta = AP.CreateScratchName(Prefix, "MaskB", "RasterDataset", Script_path)

    #Without faults and preserved codes---------------
    if FaultList == "#" and PreservedList == "#":
        #Same as the last dataset
        Scratch_mask_beta = InputRaster

    elif FaultList != "#" and PreservedList == "#":
        #Cote faults as 0s
        GeoScaler_functions.MultipleCon_diff(FaultList, InputRaster, Scratch_mask_beta, FieldValue)
        DeleteList.append(Scratch_mask_beta)

    elif FaultList == "#" and PreservedList != "#":
        #Cote Preserved codes as 0s
        GeoScaler_functions.MultipleCon_diff(PreservedList, InputRaster, Scratch_mask_beta, FieldValue)
        DeleteList.append(Scratch_mask_beta)

    elif FaultList != "#" and PreservedList != "#":
        #Cote faults as 0s
        GeoScaler_functions.MultipleCon_diff(FaultList, InputRaster, Scratch_mask_alpha, FieldValue)
        DeleteList.append(Scratch_mask_alpha)

        #Cote Preserved codes as 0s
        GeoScaler_functions.MultipleCon_diff(PreservedList, Scratch_mask_alpha, Scratch_mask_beta, FieldValue)
        DeleteList.append(Scratch_mask_beta)

    #-------------------------------------------------------------------
    #Manage small polygons within raster, if necessary
    #-------------------------------------------------------------------
    AP.AddMessage("Managing small polygons removing.")

    #User doesn't want to remove small polygons
    if RemovePolygons == "#":
        if PreservedList == "#":
            #Nibble the results (replace NoData by it's neighbours)
            NibleOut = APSA.Nibble(Scratch_null,Scratch_mask_beta)
            NibleOut.save(OutputRaster)

        else:
            #Step 1: Nibble the results (replace NoData by it's neighbours)
            Scratch_S1 = AP.CreateScratchName(Prefix, "S1", "RasterDataset", Script_path)
            NibleOut = APSA.Nibble(Scratch_null,Scratch_mask_beta)
            NibleOut.save(Scratch_S1)
            DeleteList.append(Scratch_S1)

            #Step 2: Make a mask where only preserved codes (dykes) are set to NoData
            Scratch_S2 = AP.CreateScratchName(Prefix, "S2", "RasterDataset", Script_path)
            GeoScaler_functions.MultipleCon_diff(PreservedList, Scratch_null, Scratch_S2, FieldValue)
            DeleteList.append(Scratch_S2)

            #Step 3: Make a mask where everything else than preserved codes (dykes) are set to NoData
            Scratch_S3 = AP.CreateScratchName(Prefix, "S3", "RasterDataset", Script_path)
            for values in PreservedList:
                if PreservedList.index(values) == 0:
                    SQL = '"' + FieldValue + '" = ' + str(values)
                else:
                    SQL = SQL + " OR " + '"' + FieldValue + '" = ' + str(values)
            ConS3 = APSA.Con(Scratch_null, Scratch_null, "#", SQL)
            ConS3.save(Scratch_S3)
            DeleteList.append(Scratch_S3)

            #Step 4:Set in our step 1 result, NoData values from step 2, that is only preserved codes
            Scratch_S4 = AP.CreateScratchName(Prefix, "S4", "RasterDataset", Script_path)
            Extract = APSA.ExtractByMask(Scratch_S1,Scratch_S2)
            Extract.save(Scratch_S4)
            DeleteList.append(Scratch_S4)

            #Step 5: Replace the NoData values in step3 raster with original Preserved Codes (dykes)
            ConS1 = APSA.Con(APSA.IsNull(Scratch_S4), Scratch_S3, Scratch_S4)
            ConS1.save(OutputRaster)

    #User wants to remove small polygons
    else:
        #Step 1: Assign a unique ID for each regions (polygons) in raster
        Scratch_step1 = AP.CreateScratchName(Prefix, "S1", "RasterDataset", Script_path)
        Region = APSA.RegionGroup(Scratch_mask_beta, "FOUR","WITHIN","ADD_LINK")
        Region.save(Scratch_step1)
        DeleteList.append(Scratch_step1)

        #Step 2: Select small polygons
        Scratch_step2 = AP.CreateScratchName(Prefix, "S2", "RasterDataset", Script_path)
        ExtractS2 = APSA.ExtractByAttributes(Scratch_step1, '"' + FieldCount + '" >= ' + str(RemovePolygons))
        ExtractS2.save(Scratch_step2)
        DeleteList.append(Scratch_step2)

        #For preserved codes or not -----------
        if PreservedList == "#":
            #Simply nibble the results
            NibleOut = APSA.Nibble(Scratch_null,Scratch_step2)
            NibleOut.save(OutputRaster)

        else:
            #Step 3: Nibble the result
            Scratch_step3 = AP.CreateScratchName(Prefix, "S3", "RasterDataset", Script_path)
            NibleOut = APSA.Nibble(Scratch_null,Scratch_step2)
            NibleOut.save(Scratch_step3)
            DeleteList.append(Scratch_step3)

            #Step 4: Make a mask where only preserved codes are set to NoData
            Scratch_S4 = AP.CreateScratchName(Prefix, "S4", "RasterDataset", Script_path)
            GeoScaler_functions.MultipleCon_diff(PreservedList, Scratch_null, Scratch_S4, FieldValue)
            DeleteList.append(Scratch_S4)

            #Step 5: Make a mask where everything else than preserved codes (dykes) are set to NoData
            Scratch_S5 = AP.CreateScratchName(Prefix, "S5", "RasterDataset", Script_path)
            for values in PreservedList:
                if PreservedList.index(values) == 0:
                    SQL = '"' + FieldValue + '" = ' + str(values)
                else:
                    SQL = SQL + " OR " + '"' + FieldValue + '" = ' + str(values)
            ConS3 = APSA.Con(Scratch_null, Scratch_null, "#", SQL)
            ConS3.save(Scratch_S5)
            DeleteList.append(Scratch_S5)

            #Step 6:Set in our step 1 result, NoData values from step 2, that is only preserved codes
            Scratch_S6 = AP.CreateScratchName(Prefix, "S6", "RasterDataset", Script_path)
            Extract = APSA.ExtractByMask(Scratch_step3,Scratch_S4)
            Extract.save(Scratch_S6)
            DeleteList.append(Scratch_S6)


            #Step 7: Replace the NoData values in step5 raster with original Preserved Codes (dykes)
            ConS7 = APSA.Con(APSA.IsNull(Scratch_S6), Scratch_S5, Scratch_S6)
            ConS7.save(OutputRaster)

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    for files in DeleteList:
        AP.Delete_management(files)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
