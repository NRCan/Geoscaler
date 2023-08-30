# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymLine_04.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help generalizing related symbol (e.g. buried esker with a surounding
#   limit) by eliminating the symbols by length.
# Original work: Gabriel H.V. (LCNP), 2008
###NEEDS ARCINFO AND SPATIAL ANALYST
# ---------------------------------------------------------------------------

#Import standard libs.
import sys, traceback, string, os
import arcpy as AP

#Import custom libs.
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class EnvironmentError(CustomError):pass #Child class

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    InputFeature = sys.argv[1]  #Feature to generalize
    Field = sys.argv[2] #Feature field to generalize with
    FieldValue = sys.argv[3] #Feature field value for the main symbol
    FieldValue2 = sys.argv[4] #Feature field value for symbol related to the main symbol
    UniqueIDField = sys.argv[5] #Field that contains symbol ids from both symbol class, optional
    MTL = int(sys.argv[6]) #Minimum tolerable length (m)
    ProximityDist = sys.argv[7] #Minimum tolerable proximity (m)
    DetectUnrelated = sys.argv[8] #To use if user wants to perform a relation validation

    #Process variables
    if ProximityDist != "#":
        ProximityDist = int(sys.argv[7])

    #Field variables
    AnalysisFields = ["GROUP_ID", "GROUP_FLAG"]

    #Other variables
    FeatureLayerS1 = "FeatureLayerS1" #To perform selection within input feature
    FeatureLayerS2 = "FeatureLayerS2" #To perform selection within input feature
    FieldNames = [] #Will contain all the fields names from input feature
    NeighbourDict = {} #A dictionnary to store all the neighbours to analyse
    NeighbourDict_beta = {} #Another dictionnary to store neighbour, but a temp one
    ResultDict = {} #A dictionnary to store all symbols that will be coted 0
    Prefix = "D04" #For temp data
    NearLocation = "NO_LOCATION" #Parameter used in near analysis
    NearAngle = "NO_ANGLE" #Parameter used in near analysis
    NEAR_FID = "NEAR_FID" #Found in the input feature and generated near table
    NEAR_DIST = "NEAR_DIST" #Found in the input feature and generated near table
    IN_FID = "IN_FID" #Found in the generated near table
    Near_liste = [] #A list that will contain all of the NEAR_FID info
    Sym_pair = {} #A dictionnary to contain group of symbols
    FlagWord = "ERROR" #The word written in the field that will contain flags from unrelated symbols

    #-------------------------------------------------------------------
    #Verify the product licence, scripts need ArcInfo
    #-------------------------------------------------------------------
    if GeoScaler_functions.RequestArcInfo() != "":
        raise EnvironmentError

    #-------------------------------------------------------------------
    #Retrieve and assign generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
    GeoScaler_functions.VerifyResultingField(InputFeature, ResultField)

    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Describe the input feature
    Desc = AP.Describe(InputFeature)
    OID = Desc.OIDFieldName
    Fields = Desc.Fields

    #List all field names
    for field_rows in Fields:
        FieldNames.append(field_rows.Name)

    #Iterate through priority fields, if they don't exists add them
    for fields in AnalysisFields:
        if fields not in FieldNames:
            if fields == AnalysisFields[1]:
                AP.AddField_management(InputFeature, fields, "TEXT", "#", "#", "5")
            else:
                AP.AddField_management(InputFeature, fields, "LONG")
            AP.AddMessage("*****A new field (" + fields+") is now available in attribute table...")

    #Create a field delimiter (shape vs mdb vs gdb)
    FieldDelimiters = AP.AddFieldDelimiters(InputFeature, OID)

    #Create feature layer
    AP.MakeFeatureLayer_management(InputFeature, FeatureLayerS1)
    AP.MakeFeatureLayer_management(InputFeature, FeatureLayerS2)

    #Build SQL Queries
    SQL_S1 = GeoScaler_functions.BuildSQL(InputFeature,Field,FieldValue)
    SQL_S2 = GeoScaler_functions.BuildSQL(InputFeature,Field,FieldValue2)
    SQL_S1S2 = GeoScaler_functions.BuildSQL(InputFeature,Field,FieldValue) + " OR " + GeoScaler_functions.BuildSQL(InputFeature,Field,FieldValue2)

    #-------------------------------------------------------------------
    #Find symbol grouping
    #-------------------------------------------------------------------
    if UniqueIDField == "#":
        AP.AddMessage("*****Finding and assigning id to related symbols...")

        #-------------------------------------------------------------------
        #Build neighbour dictionnary {ID:[Near feature i, Near feature j, ...], ...:...}
        #-------------------------------------------------------------------
        #Create a temp name for near table
        Scratch_table = AP.CreateScratchName(Prefix, "", "ArcInfoTable", Script_path)

        #Select in each feature layers, given class of symbols
        AP.SelectLayerByAttribute_management(FeatureLayerS1, "NEW_SELECTION", SQL_S1)
        AP.SelectLayerByAttribute_management(FeatureLayerS2, "NEW_SELECTION", SQL_S2)

        #Restart ID to 0 for all rows
        AP.CalculateField_management(FeatureLayerS1, AnalysisFields[0], 0)
        AP.CalculateField_management(FeatureLayerS2, AnalysisFields[0], 0)

        #Create a Near table
        AP.GenerateNearTable_analysis(FeatureLayerS1, FeatureLayerS2, Scratch_table, ProximityDist, NearLocation, NearAngle, "ALL")

        #Buld a dictionnary of neighbours
        Cursor_alpha = AP.SearchCursor(Scratch_table)
        for lines in Cursor_alpha:
            if lines.getValue(IN_FID) not in NeighbourDict:
                NeighbourDict[lines.getValue(IN_FID)] = [lines.getValue(NEAR_FID)]
            else:
                NeighbourDict[lines.getValue(IN_FID)].append(lines.getValue(NEAR_FID))
        del Cursor_alpha, lines

        #Iterate through dictionnary to update groups numbers
        for neighbours in NeighbourDict:
            #Query beginning
            Sym_string = FieldDelimiters + " = " + str(neighbours)
            #Build the rest of the query
            for items in NeighbourDict[neighbours]:
                Sym_string = Sym_string + " OR " + FieldDelimiters + " = " + str(items)

            #Update group id
            Cursor_beta = AP.UpdateCursor(InputFeature, Sym_string)
            for group in Cursor_beta:
                group.setValue(AnalysisFields[0], neighbours)
                Cursor_beta.updateRow(group)
            del Cursor_beta, group

        #Delete temp table
        AP.Delete_management(Scratch_table)

    #-------------------------------------------------------------------
    #Find mismatch related symbols
    #-------------------------------------------------------------------
    if DetectUnrelated == "true":
        #For groups found within script
        if UniqueIDField == "#":
            AP.AddMessage("*****Detecting unrelated symbols...")
            #Iterate through feature to detect mistmatch
            Cursor_gamma = AP.UpdateCursor(InputFeature, SQL_S1S2)
            for rows_gamma in Cursor_gamma:
                #If a value is nothing, than the string transf. result should returm false
                if rows_gamma.getValue(AnalysisFields[0]) != 0:
                    rows_gamma.setValue(AnalysisFields[1], "")
                    Cursor_gamma.updateRow(rows_gamma)
                else:
                    rows_gamma.setValue(AnalysisFields[1], FlagWord)
                    Cursor_gamma.updateRow(rows_gamma)
            del rows_gamma, Cursor_gamma

    #-------------------------------------------------------------------
    #Generalization by length
    #-------------------------------------------------------------------
    #Iterate through input feature and read length
    Cursor_delta = AP.SearchCursor(InputFeature, SQL_S1S2)
    for rows_delta in Cursor_delta:
        if int(rows_delta.Shape.length) <= MTL:
            #Model custom ID
            if UniqueIDField == "#":
                ResultDict[rows_delta.getValue(AnalysisFields[0])] = 0
            #User provided ID
            else:
                ResultDict[rows_delta.getValue(UniqueIDField)] = 0
    del rows_delta, Cursor_delta

    #Update the feature with proper information
    Cursor_epsilon = AP.UpdateCursor(InputFeature, SQL_S1S2)
    for rows_epsilon in Cursor_epsilon:
        #Model custom ID
        if UniqueIDField == "#":
            if rows_epsilon.getValue(AnalysisFields[0]) in ResultDict:
                rows_epsilon.setValue(ResultField, 0)
            else:
                rows_epsilon.setValue(ResultField, 1)
        #User provided ID
        else:
            if rows_epsilon.getValue(UniqueIDField) in ResultDict:
                rows_epsilon.setValue(ResultField, 0)
            else:
                rows_epsilon.setValue(ResultField, 1)
        Cursor_epsilon.updateRow(rows_epsilon)
    del rows_epsilon, Cursor_epsilon

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(ResultField)+".")

except EnvironmentError:
     AP.AddError("No ArcInfo licence available, retry later.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
