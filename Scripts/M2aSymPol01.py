# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPol_01.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will perform generalization based on a minimal area.
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
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1]  #Feature to generalize
    FeatureField = sys.argv[3] #Field to select proper symbols
    FeatureFieldValue = sys.argv[4] #Field value to select proper symbols
    MinArea = sys.argv[5] #Minimum tolerable area

    #-------------------------------------------------------------------
    #Manage resulting field
    #-------------------------------------------------------------------
    #Retrieve generalization results field
    champ_result_alpha = GeoScaler_functions.FieldDictionnary(ScriptName)

    #Build a field name with scale in it
    champ_result = GeoScaler_functions.BuildResultingField(champ_result_alpha)

    #Add results field, if needed
    GeoScaler_functions.VerifyResultingField(InputFeature, champ_result)

    #-------------------------------------------------------------------
    #Create an update cursor, and validate
    #-------------------------------------------------------------------
    if FeatureField == "#":
        Cursor = AP.UpdateCursor(InputFeature)
    else:
        Query = GeoScaler_functions.BuildSQL(InputFeature, FeatureField, FeatureFieldValue)
        Cursor = AP.UpdateCursor(InputFeature, Query)

    for lines in Cursor:
        #Get the area
        Area = lines.shape.area

        #Validate with minimum area
        if Area < int(MinArea):
            lines.setValue(str(champ_result),0)
        else:
            lines.setValue(str(champ_result),1)

        #On met à jour la ligne
        Cursor.updateRow(lines)

    del Cursor, lines #To prevent some locks

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(champ_result)+".")

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

