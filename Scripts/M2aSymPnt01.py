# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPnt_01.py
# Gabriel Huot-Vézina (LCNP), 2010
#   Will help generalizing individual symbol classes by eliminating
#   superposition between symbols.
###NOTE: NEEDS ARCINFO LICENCE
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
    InputFeature = sys.argv[1]  #Feature to generalize
    field = sys.argv[3] #Feature field to generalize with
    field_value = sys.argv[4] #Feature field value, generalization will occur only on this class of symbol
    NFD = sys.argv[5] #Near feature NFD (m)

    #-------------------------------------------------------------------
    #Call a custom function to generalize the given input feature
    #-------------------------------------------------------------------
    GeoScaler_functions.M_2aSymPnt_01(InputFeature, field, field_value, NFD, ScriptName)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
