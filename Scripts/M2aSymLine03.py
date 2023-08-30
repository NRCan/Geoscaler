# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymLine_03.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help generalizing individual line symbol classes by eliminating
#   short lines and then symbol very close to each other with a virtual buffer
#   zone method.
# Original work: Gabriel H.V. (LCNP), 2008
###NEEDS ARCINFO AND SPATIAL ANALYST
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
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputFeature = sys.argv[1]  #Feature to generalize
    EntireFeature = sys.argv[2] #Model will be apply if the entire or a class is entered
    Field = sys.argv[3] #Feature field to generalize with
    FieldValue = sys.argv[4] #Feature field value, generalization will occur only on this class of symbol
    MTL = sys.argv[5] #Minimum tolerable length (m)
    ProximityDist = sys.argv[6] #Minimum tolerable proximity (m)

    #Other variables
    FeatureLayer = "FeatureLayer" #To perform selection within input feature
    FieldNames = [] #Will contain all the fields names from input feature
    CurrentSym = 0 #The current symbol ID in proximity analysis
    CurrentLength = 0 #The current symbol length in proximity analysis
    LengthDict = {} #A dictionnary to store symbols length
    NeighbourDict = {} #A dictionnary to store all the neighbours to analyse
    NeighbourDict_beta = {} #Another dictionnary to store neighbour, but a temp one
    ResultDict = {} #A dictionnary to store all symbols that will be coted 0
    Prefix = "D03" #For temp data
    NearLocation = "NO_LOCATION" #Parameter used in near analysis
    NearAngle = "NO_ANGLE" #Parameter used in near analysis
    NearIDField = "NEAR_FID" #Found in the input feature and generated near table
    NearDistField = "NEAR_DIST" #Found in the input feature and generated near table
    NearIN_FID = "IN_FID" #Found in the generated near table
    Near_liste = [] #A list that will contain all of the NEAR_FID info

    #-------------------------------------------------------------------
    #Retrieve and assign generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
##    GeoScaler_functions.VerifyResultingField(InputFeature, ResultField)

    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Describe the input feature
    Desc = AP.Describe(InputFeature)
    OID = Desc.OIDFieldName

    #Iterate through dictionnary and retrieve length of symbols
    if Field != "#":
        #Create an SQL Query to fit into the cursor
        SQL = GeoScaler_functions.BuildSQL(InputFeature, Field, FieldValue) + " AND "+ ResultField + " = 1"

    #-------------------------------------------------------------------
    #Generalization by lenght
    #-------------------------------------------------------------------
    #Call custom function
    GeoScaler_functions.M_2aSymLine_01(InputFeature, Field, FieldValue, MTL, ScriptName)

    #-------------------------------------------------------------------
    #Build length dictionnary {OIDi:Xi, OIDj:Xj, ...:...}
    #-------------------------------------------------------------------
    Cursor = AP.SearchCursor(InputFeature)
    for rows in Cursor:
        LengthDict[rows.getValue(OID)] = rows.Shape.length
    del rows, Cursor

    #-------------------------------------------------------------------
    #Build neighbour dictionnary {ID:[Near feature i, Near feature j, ...], ...:...}
    #-------------------------------------------------------------------
    #Create a temp name for near table
    Scratch_table = AP.CreateScratchName(Prefix, "", "ArcInfoTable", Script_path)

    #Create a feature layer to make selection within it
    AP.MakeFeatureLayer_management(InputFeature, FeatureLayer)

    #Select proper symbol if needed
    if Field != "#":
        AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", SQL)

    #Create a Near table
    AP.GenerateNearTable_analysis(FeatureLayer, FeatureLayer, Scratch_table, ProximityDist, NearLocation, NearAngle, "ALL")

    #Iterate through near table to find grouping of 2 symbols
    Cursor_alpha = AP.SearchCursor(Scratch_table)
    for lines in Cursor_alpha:
        Near_liste.append(lines.getValue(NearIDField))
        NeighbourDict[lines.getValue(NearIN_FID)] = [lines.getValue(NearIDField)]

        if lines.getValue(NearIN_FID) in Near_liste:
            if lines.getValue(NearIDField) in NeighbourDict:
                del NeighbourDict[lines.getValue(NearIN_FID)]

    #Iterate through near table to find grouping of 3 and more symbols
    Cursor_beta = AP.SearchCursor(Scratch_table)
    for lines in Cursor_beta:
        NeighbourDict_beta[lines.getValue(NearIN_FID)] = [lines.getValue(NearIDField)]
        if lines.getValue(NearIN_FID) not in NeighbourDict:
            if lines.getValue(NearIN_FID) in NeighbourDict_beta:
                NeighbourDict_beta[lines.getValue(NearIN_FID)].append(lines.getValue(NearIDField))
        else:
            del NeighbourDict_beta[lines.getValue(NearIN_FID)]

    #Append both dictionnary within the first one and eliminate duplicate values
    for keys in NeighbourDict_beta:
        if keys not in NeighbourDict:
            key_id = NeighbourDict_beta[keys][0]
            NeighbourDict[key_id].append(keys)
            NeighbourDict[key_id] = list(set(NeighbourDict[key_id]))

    #-------------------------------------------------------------------
    #Build result dictionnary
    #-------------------------------------------------------------------
    #Iterate through neighbour dictionnary
    for keys in NeighbourDict:
        #Retrieve current symbol length
        CurrentLen = LengthDict[keys]
        for values in NeighbourDict[keys]:
            #Retrieve neighbour symbol length
            NeighbourLen = LengthDict[values]
            if NeighbourLen <= CurrentLen:
                #Cote neighbour as 0
                ResultDict[values] = 0
            else:
                #Cote neighbour as good and the current symbol as 0
                ResultDict[values] = 1
                ResultDict[keys] = 0

    #-------------------------------------------------------------------
    #Cote 0 the detected symbols
    #-------------------------------------------------------------------
    Cursor_gamma = AP.UpdateCursor(InputFeature)
    for rows_gamma in Cursor_gamma:
        #Detect if the current row is in the dictionnary
        if rows_gamma.getValue(OID) in ResultDict:
            #Make sure the symbol needs to be coted 0
            if ResultDict[rows_gamma.getValue(OID)] == 0:
                rows_gamma.setValue(ResultField, 0)
                Cursor_gamma.updateRow(rows_gamma)
    del rows_gamma, Cursor_gamma

    #-------------------------------------------------------------------
    #Delete temp features
    #-------------------------------------------------------------------
    AP.Delete_management(Scratch_table)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
