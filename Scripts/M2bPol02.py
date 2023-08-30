# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2bPol_02.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will generalize bedrock polygons with certain contraints from user, like
#   faults and dykes.
###NEEDS A SPATIAL ANALYST LICENCE
# ---------------------------------------------------------------------------
#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP
import arcpy.sa as APSA

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
    InputRaster = sys.argv[1]  #Input ascii file to convert into raster or feature
    Radius = int(sys.argv[2])#Moore's neighbourhood radius
    PreserveFaults = sys.argv[3] #List of code of fault cells to be preserved from output
    FaultsNeighbour = sys.argv[4] #The number of cells around faults to preserve
    PreservedCodes = sys.argv[5] #List of code of polygons to be preserved, eg. dykes
    FinalIteration = int(sys.argv[6]) #Total iteration
    OutputInterval = sys.argv[7] #The number of output if needed, at every X iteration, for testing purposes
    OutputRaster = sys.argv[8] #An output raster

    #Other variables
    NoDataValue = 0 #Temp value for no data values within output raster
    FieldValue = "Value" #The field namw within region group raster that contain ids
    DeleteList = []# A list to contain all temp output to delete after the process
    IterLoop = 1 #The starting number for the while loop
    IterList = [] #An empty to contain the number at wich a real output will be available, instead of a temp one.
    OutputName = string.split(os.path.basename(OutputRaster),".")[0][0:5] #Carater 0 to 4, the minimum is set within toolvalidator
    ToAnalyse = () #A tuple with the first value, the last iterated raster and second value the generalized output
    FilterType = "MAJORITY" #The type of filter to use within generalization
    AllPreservedData = [] #A list to contain all preserved data, (e.g. dykes, faults, and faults neighbours)
    Scratch = "C:\\Temp"

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
    #Setting the scratch workspace
    AP.env.scratchWorkspace = Scratch

    #Manage multiple values for faults codes and/or preserved codes
    if ";" in PreserveFaults:
        FaultList = PreserveFaults.split(";")
    elif "#" not in PreserveFaults:
        FaultList = [PreserveFaults]
    else:
        FaultList = PreserveFaults
        FaultList = PreserveFaults

    if ";" in PreservedCodes:
        PreservedList = PreservedCodes.split(";")
    elif "#" not in PreservedCodes:
        PreservedList = [PreservedCodes]
    else:
        PreservedList = PreservedCodes

    #Set the moore's neighborhood radius (e.g. 1 radius = a window of 3X3 cells)
    MooreRadius = Radius * 2 + 1

    #Setting the output folder for output by intervals
    Workspace = os.path.dirname(OutputRaster)

    #Managing output intervals
    if OutputInterval != "#":
        OutputInterval = int(OutputInterval)

        #Build a temp list
        TempList = range(FinalIteration)
        for numbers in TempList:
            ###Add 1 to numbers because TempList starts with a 0
            ###Select second item in tuple result from divmod
            ###For 10 iteration the list should look like [2,4,6,8] if user as selected an output at every 2 iterations
            if divmod(numbers + 1, OutputInterval)[1] == 0 and numbers + 1 != FinalIteration:
                IterList.append(numbers + 1)

    #STEP 1 ---: Setting NoData value to another value, will help manage NoData later
    Scratch_S1 = AP.CreateScratchName("S1_", "", "RasterDataset", Scratch)
    ###IsNull() function will result in a raster with 0 and 1 where there was NoData
    ###The result can be used with Con() function, 1 values are considered as true
    ###and 0 values are considered as false.
    Con = APSA.Con(APSA.IsNull(InputRaster), NoDataValue, InputRaster)
    Con.save(Scratch_S1)

    #STEP 2 ---: Create a mask out of the replaced NoData values
    Scratch_S2 = AP.CreateScratchName("S2_", "", "RasterDataset", Scratch)
    SQL_ConMNull = '"' + FieldValue + '" <> ' + str(NoDataValue)
    ConMNull = APSA.Con(Scratch_S1, Scratch_S1, "#", SQL_ConMNull)
    ConMNull.save(Scratch_S2)

    #-------------------------------------------------------------------
    #Manage cells around faults (optional)
    #-------------------------------------------------------------------
    AP.AddMessage("Managing neighbouring cells around faults.")

    if int(FaultsNeighbour) != 0 and FaultList != "#":
        #Expand faults by a fix number of cells
        Scratch_S3 = AP.CreateScratchName("S3_", "", "RasterDataset", Scratch)
        Expand = APSA.Expand(Scratch_S1, FaultsNeighbour, FaultList)
        Expand.save(Scratch_S3)
    else:
        Scratch_S3 = Scratch_S1

    #-------------------------------------------------------------------
    #Manage Faults and/or Preserved code values within raster by creating masks
    #-------------------------------------------------------------------
    AP.AddMessage("Managing faults and/or preserved codes.")

    #Create scratch names
    Scratch_S4 = AP.CreateScratchName("S4_", "", "RasterDataset", Scratch)
    Scratch_S5 = AP.CreateScratchName("S5_", "", "RasterDataset", Scratch)

    #Without faults and preserved codes---------------
    if FaultList == "#" and PreservedList == "#":
        #Same as the last dataset
        Scratch_S5 = Scratch_S3
        AllPreservedData = "#"

    elif FaultList != "#" and PreservedList == "#":
        #Cote faults as 0s
        GeoScaler_functions.MultipleCon_diff(FaultList, Scratch_S3, Scratch_S5, FieldValue)

        #Build a list of all preserved data (e.g. dykes, faults)
        AllPreservedData = FaultList

    elif FaultList == "#" and PreservedList != "#":
        #Cote Preserved codes as 0s
        GeoScaler_functions.MultipleCon_diff(PreservedList, Scratch_S3, Scratch_S5, FieldValue)

        #Build a list of all preserved data (e.g. dykes, faults)
        AllPreservedData = PreservedList

    elif FaultList != "#" and PreservedList != "#":
        #Cote faults as 0s
        GeoScaler_functions.MultipleCon_diff(FaultList, Scratch_S3, Scratch_S4, FieldValue)

        #Cote Preserved codes as 0s
        GeoScaler_functions.MultipleCon_diff(PreservedList, Scratch_S4, Scratch_S5, FieldValue)

        #Build a list of all preserved data (e.g. dykes, faults)
        AllPreservedData = PreservedList + FaultList

    #-------------------------------------------------------------------
    #Generalize
    #-------------------------------------------------------------------
    AP.AddMessage("Generalization...")

    while IterLoop <= FinalIteration:
        #-------------------------------------------------------------------
        #Prepare data
        #-------------------------------------------------------------------
        #Manage outputs names
        if IterLoop < 10:
            OutputName_beta = OutputName + "_00" + str(IterLoop)
        elif IterLoop >= 10 and IterLoop < 100:
            OutputName_beta = OutputName + "_0" + str(IterLoop)
        elif IterLoop >= 100 and IterLoop < 1000:
            OutputName_beta = OutputName + "_" + str(IterLoop)

        #Manage output paths
        if IterLoop in IterList or IterLoop == FinalIteration:
            if IterLoop != FinalIteration:
                OutputPath = AP.CreateScratchName(OutputName_beta, "", "RasterDataset", Workspace)
            else:
                OutputPath = OutputRaster
        else:
            OutputPath = AP.CreateScratchName(OutputName_beta, "", "RasterDataset", Scratch)

        #Manage data to analyse
        if IterLoop == 1:
            #Start with the scratch raster
            ToAnalyse = (Scratch_S5, OutputPath)
        else:
            #Start with the last element of the list
            ToAnalyse = (ToAnalyse[1], OutputPath)

        #-------------------------------------------------------------------
        #Apply a majotiry filter
        #-------------------------------------------------------------------
        Scratch_S6 = AP.CreateScratchName("S6_", "", "RasterDataset", Scratch)
        FocalMajority = APSA.FocalStatistics(ToAnalyse[0], \
                                             APSA.NbrRectangle(MooreRadius,MooreRadius,"CELL"), \
                                             FilterType, "DATA")
        FocalMajority.save(Scratch_S6)

        #-------------------------------------------------------------------
        #Manage preserved codes
        #-------------------------------------------------------------------
        #STEP 7 ---:Setting NoData value to another value, will help manage NoData later
        Scratch_S7 = AP.CreateScratchName("S7_", "", "RasterDataset", Scratch)
        ###IsNull() function will result in a raster with 0 and 1 where there was NoData
        ###The result can be used with Con() function, 1 values are considered as true
        ###and 0 values are considered as false.
        Con = APSA.Con(APSA.IsNull(Scratch_S6), NoDataValue, Scratch_S6)
        Con.save(Scratch_S7)

        #STEP 8 ---:Create a mask out of the replaced NoData values
        Scratch_S8 = AP.CreateScratchName("S8_", "", "RasterDataset", Scratch)
        ConMNullB = APSA.Con(Scratch_S7, Scratch_S7, "#", SQL_ConMNull)
        ConMNullB.save(Scratch_S8)

        if AllPreservedData == "#":
            #FINAL STEP ---: Nibble the results (replace NoData by it's neighbours)
            NibleOut = APSA.Nibble(Scratch_S7,Scratch_S8)
            NibleOut.save(ToAnalyse[1])

        else:
            #STEP 9 ---: Nibble the results (replace NoData by it's neighbours)
            Scratch_S9 = AP.CreateScratchName("S9_", "", "RasterDataset", Scratch)
            NibleOut = APSA.Nibble(Scratch_S7,Scratch_S8)
            NibleOut.save(Scratch_S9)

            #STEP 10 ---: Make a mask where preserved data (code, faults, buffer) are set to NoData
            Scratch_S10 = AP.CreateScratchName("S10_", "", "RasterDataset", Scratch)
            GeoScaler_functions.MultipleCon_diff(AllPreservedData, Scratch_S5, Scratch_S10, FieldValue)

            #STEP 11 ---: Set in our step 1 result, NoData values from step 2, that is only all preserved data (code, faults, buffer)
            Scratch_S11 = AP.CreateScratchName("S11_", "", "RasterDataset", Scratch)
            Extract = APSA.ExtractByMask(Scratch_S9,Scratch_S10)
            Extract.save(Scratch_S11)

            #FINAL STEP ---: Replace the NoData values in step3 raster with all original preserved data (code, faults, buffer)
##            AP.AddMessage("FINAL STEP ")
            ConS1 = APSA.Con(APSA.IsNull(Scratch_S11), Scratch_S2, Scratch_S11)
            ConS1.save(ToAnalyse[1])

        #-------------------------------------------------------------------
        #Post management
        #-------------------------------------------------------------------
        AP.AddMessage("Iteration number: " + str(IterLoop))

        #Manage outputs
        if IterLoop in IterList:
            AP.AddWarning("Intermediate result available at: " + ToAnalyse[1])
        elif IterLoop == FinalIteration:
            AP.AddWarning("Final result available at: " + ToAnalyse[1])

        #Iterate IterLoop number
        IterLoop = IterLoop + 1

    #------------------------------------------------------------------------------
	#Deleting useless temp data
	#------------------------------------------------------------------------------
	for files in DeleteList:
		AP.Delete_management(files)

except EnvironmentError:
    AP.AddError("No " + str(LicenceName) + " licence available, retry later.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
