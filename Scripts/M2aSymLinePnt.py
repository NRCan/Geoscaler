# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymLinePnt.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help generalizing point symbols classes around more prioritary linear
#   symbol classes.
# Original work: Gabriel H.V. (LCNP), 2009
# ---------------------------------------------------------------------------
#Import standard lib.
import sys, traceback, string, os
import arcpy as AP

#Import custom lib.
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class LastModelError(CustomError):pass #Child class

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputLineFeature = sys.argv[1] #Feature to generalize around it
    FieldResult = sys.argv[2] #The last field that contains generalization results, should be D06_
    MTP = sys.argv[3] #The minimal proximity distance usually used line generalization models
    InputPntFeature = sys.argv[4] #Point feature that will be coted 0 if too near from line features
    EntireFeature = sys.argv[5] #If user wants to apply model on the complete feature or not
    InputField = sys.argv[6] #Field that contains symbols class
    LoadSettingFile = sys.argv[7] #A file with all the setting strings
    Setting_strings = sys.argv[8] #A string with field value, near feature distance and a rank seperated by ";"
    SaveSettingFile = sys.argv[9] #An output file to save the settings strings

    #Other variables
    FeatureLayerLine = "FeatureLayerLine"
    FeatureLayerPnt = "FeatureLayerPnt"
    SettingList = Setting_strings.split(";") #Split the Setting_strings into a list
    Prefix = "E_" #A prefix for temp output data

    #-------------------------------------------------------------------
    #Retrieve and assign generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
    GeoScaler_functions.VerifyResultingField(InputPntFeature, ResultField)

    #-------------------------------------------------------------------
    #Save the setting strings within a text file
    #-------------------------------------------------------------------
    if SaveSettingFile != "#":
        GeoScaler_functions.SaveSettingToFile(SaveSettingFile, SettingList)

    #-------------------------------------------------------------------
    #Prepare the data
    #-------------------------------------------------------------------
    #Create a layer file, for selection purposes
    AP.MakeFeatureLayer_management(InputPntFeature, FeatureLayerPnt)
    AP.MakeFeatureLayer_management(InputLineFeature, FeatureLayerLine)

    #For line symbols, select only the symbol coted as 1
    SQL = GeoScaler_functions.BuildSQL(InputLineFeature,FieldResult,1)
    AP.SelectLayerByAttribute_management(FeatureLayerLine, "NEW_SELECTION", SQL)

    #-------------------------------------------------------------------
    #Generalization
    #-------------------------------------------------------------------
    #For symbol class only
    if str(EntireFeature) == "false":
        #Cote the symbols as 1 to start
        AP.CalculateField_management(FeatureLayerPnt, ResultField, 1)

        #For each symbol class
        for symbols in sorted(SettingList):
            #--- Get info from SettingList
            Current_symbol = str(symbols.split(",")[0])
            Current_MTP = int(symbols.split(",")[1])

            #Build SQL Query to select class
            SQL_query = GeoScaler_functions.BuildSQL(InputPntFeature,InputField,Current_symbol)

            #Select symbol class
            AP.SelectLayerByAttribute_management(FeatureLayerPnt, "NEW_SELECTION", SQL_query)

            #Get total number of symbols
            NumberBefore = int(AP.GetCount_management(FeatureLayerPnt)[0])

            #Select all point symbol around all the lines
            AP.SelectLayerByLocation_management(FeatureLayerPnt, "INTERSECT", FeatureLayerLine, int(Current_MTP), "SUBSET_SELECTION")

            #Get the number of symbol selected
            NumberAfter = int(AP.GetCount_management(FeatureLayerPnt)[0])
##            AP.AddWarning(str(NumberBefore) + " ... " + str(NumberAfter))
            #Cote all the selected as 0, if there is
            if NumberAfter > 0 and NumberBefore != NumberAfter:
                AP.CalculateField_management(FeatureLayerPnt, ResultField, 0)
            else:
                AP.AddWarning("There was no punctual symbols from class '" + Current_symbol + "' around line symbols.")

    #For entire point feature
    elif str(EntireFeature) == "true":
        #Cote the symbols as 1 to start
        AP.CalculateField_management(FeatureLayerPnt, ResultField, 1)

        #Get total number of symbols
        NumberBefore = int(AP.GetCount_management(FeatureLayerPnt)[0])

        #Select all point symbol around all the lines
        AP.SelectLayerByLocation_management(FeatureLayerPnt, "INTERSECT", FeatureLayerLine, int(MTP), "NEW_SELECTION")

        #Get the number of symbol selected
        NumberAfter = int(AP.GetCount_management(FeatureLayerPnt)[0])

        #Cote all the selected as 0, if there is
        if NumberAfter > 0 and NumberBefore != NumberAfter:
            AP.CalculateField_management(FeatureLayerPnt, ResultField, 0)
        else:
            AP.AddWarning("There was no punctual symbols around line symbols.")

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(ResultField)+".")

except LastModelError:
     AP.AddError("Before running this model, last point generalization model B:04 Global generalization must be run first.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
