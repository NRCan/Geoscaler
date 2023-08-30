# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymLine_06.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will append all line generalization fields into one single field.
# Original work: Gabriel H.V. (LCNP), 2008
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
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1]  #Feature to append results
    FieldList = sys.argv[2].split(";") #User's given list of field that contains results

    #Other variables
    ResultDict = {} #Will contains each IDs and the generalization results {OIDi:0, OIDj:1, ...}

    #-------------------------------------------------------------------
    #Retrieve and assign generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
    GeoScaler_functions.VerifyResultingField(InputFeature, ResultField)

    #-------------------------------------------------------------------
    #Append results
    #-------------------------------------------------------------------
    #Describe the input feature
    Desc = AP.Describe(InputFeature)
    OID = Desc.OIDFieldName

    #Iterate through feature to read results
    Cursor = AP.SearchCursor(InputFeature)
    for rows in Cursor:
        #Start the dictionnary with a positive value
        ResultDict[rows.getValue(OID)] = 1
        #Iterate through each given fields from user
        for fields in FieldList:
            #Validate negative results
            if rows.getValue(fields) == 0:
                #Append the result to dictionnary
                ResultDict[rows.getValue(OID)] = 0
    del rows, Cursor

    #Update the input feature with retrieve information
    Cursor_beta = AP.UpdateCursor(InputFeature)
    for rows_beta in Cursor_beta:
        #Get the info
        rows_beta.setValue(ResultField, ResultDict[rows_beta.getValue(OID)])
        #Update the line
        Cursor_beta.updateRow(rows_beta)
    del rows_beta, Cursor_beta

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(ResultField)+".")

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
