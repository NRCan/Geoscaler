# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPntLine.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will generalize any point symbols around linear symbol of priority higher
#   the point. Proceeds with a buffer and a clip analysis.
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
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputPntFeature = sys.argv[1] #Feature to generalize
    EntireFeatureNFD = sys.argv[2] #An near feature distance in case if the entire feature is passed to the model
    EntireFeature = sys.argv[3] #If user wants to apply model on the complete feature or not
    InputField = sys.argv[4] #Field that contains symbols class
    LoadSettingFile = sys.argv[5] #A file with all the setting strings
    Setting_strings = sys.argv[6] #A string with field value, near feature distance and a rank seperated by ";"
    SaveSettingFile = sys.argv[7] #An output file to save the settings strings
    InputLineFeature = sys.argv[8] #Line feature that will be cut around desire symbol class
    OutputLineFeature = sys.argv[9] #Output line feature from the cuted line feature.

    #Field variables
    AllFieldName = [] #An empty list to store all the field names from the input feature

    #Other variables
    FeatureLayer = "InputFeature"
    SettingList = Setting_strings.split(";") #Split the Setting_strings into a list
    Prefix = "C_" #A prefix for temp output data
    LastGeneModel = "M2aSymPnt04"
    BufferList = [] #A list to contain all the buffer features created

    #-------------------------------------------------------------------
    #Retrieve last generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(LastGeneModel)
    LastResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)

    #Verify the existence of that last field
    Desc = AP.Describe(InputPntFeature)
    Fields = Desc.Fields #A list of fields

    for all_fields in Fields:
        AllFieldName.append(all_fields.Name)

    if LastResultField not in AllFieldName:
        raise LastModelError

    #-------------------------------------------------------------------
    #Save the setting strings within a text file
    #-------------------------------------------------------------------
    if SaveSettingFile != "#":
        GeoScaler_functions.SaveSettingToFile(SaveSettingFile, SettingList)

    #-------------------------------------------------------------------
    #Prepare the data
    #-------------------------------------------------------------------
    #Create a lyr file, for selection purposes
    AP.MakeFeatureLayer_management(InputPntFeature, FeatureLayer)

    #-------------------------------------------------------------------
    #Generalization
    #-------------------------------------------------------------------
    if str(EntireFeature) == "false":
        for symbols in sorted(SettingList):
            #--- Get info from SettingList
            Current_symbol = str(symbols.split(",")[0])
            Current_NFD = int(symbols.split(",")[1])

            #--- Create buffer around point symbol classes.
            #Build SQL Query
            SQL_query = GeoScaler_functions.BuildSQL(InputPntFeature,InputField,Current_symbol) + " AND " + str(LastResultField) + " = 1"

            #Select symbol class
            AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", SQL_query)

            #Create scratch name
            ScratchBuffer = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

            #Half the near feature distance, or else the result will overgeneralized
            Half_NFD = Current_NFD / 2

            #Create buffer
            AP.Buffer_analysis(FeatureLayer, ScratchBuffer, Half_NFD)
            BufferList.append(ScratchBuffer)

            #Merge all the buffer features into one
            ScratchSuperBuffer = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)
            AP.Merge_management(BufferList, ScratchSuperBuffer)

        #Delete the temp buffers from list
        for buffers in BufferList:
            AP.Delete_management(buffers)

    elif str(EntireFeature) == "true":
        #Half the near feature distance, or else the result will overgeneralized
        Half_NFD = int(EntireFeatureNFD) / 2

        #Create a buffer with the entire feature
        ScratchSuperBuffer = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)
        AP.Buffer_analysis(FeatureLayer, ScratchSuperBuffer, Half_NFD)

    #Apply the erase tool to cut the linear symbols
    ScratchCutedLine = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)
    AP.Erase_analysis(InputLineFeature, ScratchSuperBuffer, ScratchCutedLine)

    #Make sure there is not multipart line symbols
    AP.MultipartToSinglepart_management(ScratchCutedLine, OutputLineFeature)

    #Delete the temp features
    AP.Delete_management(ScratchSuperBuffer)
    AP.Delete_management(ScratchCutedLine)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in output line feature: " + str(OutputLineFeature)+ ".")

except LastModelError:
     AP.AddError("Before running this model, last point generalization model B:04 Global generalization must be run first.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

