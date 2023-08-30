# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPost_01.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help recover point/lines symbols around other point/lines symbols
# Original work: Gabriel H.V. (LCNP), 2009
# ---------------------------------------------------------------------------
#Import standard lib.
import sys, traceback, string, os
import arcpy as AP

#Import custom lib.
import GeoScaler_functions

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputMainFeature = sys.argv[1] #Feature to generalize around it
    EntireFeature = sys.argv[2] #If user wants to apply model on the complete main feature or not
    FieldMain = sys.argv[3] #Field from main feature
    FieldValueMain = sys.argv[4] #Field value from main feature
    FieldResult = sys.argv[5] #The last field that contains generalization results, should be B04_
    InputRecoveryFeature = sys.argv[6] #The feature from wich symbols will be recover
    EntireRecoFeature = sys.argv[7] #If user wants to apply model on entire recovery feature or not
    FieldReco = sys.argv[8] #Field for symbol class of recovery feature
    FieldRecoValue = sys.argv[9] #Field value for symbol class of recovery feature
    FieldResultReco = sys.argv[10] #The field that contains the last generalization results
    RecoveryRadius = int(sys.argv[11]) #The radius to search for recovery feature around main feature

    #Other variables
    FeatureLayerMain = "FeatureLayerMain"
    FeatureLayerReco = "FeatureLayerReco"

    #-------------------------------------------------------------------
    #Retrieve and assign generalization results field to recovery feature
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
    GeoScaler_functions.VerifyResultingField(InputRecoveryFeature, ResultField)

    #-------------------------------------------------------------------
    #Prepare the data
    #-------------------------------------------------------------------
    #Create a layer file, for selection purposes
    AP.MakeFeatureLayer_management(InputMainFeature, FeatureLayerMain)
    AP.MakeFeatureLayer_management(InputRecoveryFeature, FeatureLayerReco)

    #For main symbols, select only the symbol coted as 1
    SQL = GeoScaler_functions.BuildSQL(InputMainFeature,FieldResult,1)
    AP.SelectLayerByAttribute_management(FeatureLayerMain, "NEW_SELECTION", SQL)

    #Copy the result from ResultFieldReco, onto the new resulting field
    ## The function AddFieldDelimiters doesn't seem to work in Arc10.0 SP4
    ## DelimiterRes = AP.AddFieldDelimiters(InputRecoveryFeature, FieldResultReco) #[Field] for shapes and gdb, "Field" for mdb
    ## Returns "x" instead of [x] for a gdb...

    if ".mdb" in InputRecoveryFeature:
        DelimiterRes = '"' + FieldResultReco + '"'
    elif ".shp" in InputRecoveryFeature or ".gdb" in InputRecoveryFeature:
        DelimiterRes = "[" + FieldResultReco + "]"
    else:
        DelimiterRes = FieldResultReco

    AP.CalculateField_management(FeatureLayerReco, ResultField, DelimiterRes)

    #-------------------------------------------------------------------
    #Reverse generalization
    #-------------------------------------------------------------------
    #For main symbol class only
    if str(EntireFeature) == "false":
        #Select symbol class from main feature
        SQL_main = GeoScaler_functions.BuildSQL(InputMainFeature, FieldMain, FieldValueMain)
        AP.SelectLayerByAttribute_management(FeatureLayerMain, "SUBSET_SELECTION", SQL_main)

    #For recovery symbol class only:#
    if EntireRecoFeature == "false":
        #Select symbol class from reco. feature
        SQL_reco = GeoScaler_functions.BuildSQL(InputRecoveryFeature, FieldReco, FieldRecoValue)
        AP.SelectLayerByAttribute_management(FeatureLayerReco, "NEW_SELECTION", SQL_reco)

        #Select with a virtual buffer reco. symbols around main symbols
        AP.SelectLayerByLocation_management(FeatureLayerReco, "INTERSECT", FeatureLayerMain, RecoveryRadius, "SUBSET_SELECTION")

    else:
        #Select with a virtual buffer reco. symbols around main symbols
        AP.SelectLayerByLocation_management(FeatureLayerReco, "INTERSECT", FeatureLayerMain, RecoveryRadius, "NEW_SELECTION")

    #Cote as 1 the select symbols
    AP.CalculateField_management(FeatureLayerReco, ResultField, 1)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    FeatureName = string.split(os.path.basename(InputRecoveryFeature), ".")[0]
    AP.AddMessage("Results are available in field: " + str(ResultField)+", in feature " + FeatureName + ".")

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
