# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPol_02.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Analysis before and after polygon generalization features, and will, from
#   a given attribute value search for missing polygons, thus converting them
#   to point symbols. The results will be store in either an existing feature
#   or a new one and will be created.
###HARDCODE for custom toolbox
###NO POINT GENERALIZATION WILL OCCUR.
# ---------------------------------------------------------------------------

#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP

#Import custom libraries
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class TypeError(CustomError):pass #Child class
class AttributeError(CustomError):pass #Child class

try:

    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    AP.AddMessage(ScriptName)
    InputFeature = sys.argv[1]  #Feature to generalize
    EntireFeatureBool = sys.argv[2] #To know if the model needs to be run on entire feature or not
    FeatureField = sys.argv[3] #Field to select proper symbols
    FeatureFieldValue = sys.argv[4] #Field value to select proper symbols
    MinArea = sys.argv[5] #Minimum tolerable area
    NewSymFeature = sys.argv[6] #Input new symbol feature name and path.
    SymFeature = sys.argv[7] #Input existing symbol feature.
    SymFeatureField = sys.argv[8] #Input existing symbol feature field name.
    SymFeatureFieldValue = sys.argv[9] #Input existing symbol feature field value.

    #Variables
    ToolboxPath = Script_path + "\\Scripts\GeoScaler Tools.tbx"
    Prefix = "GS"
##    ScriptName = "M_2aSymPol_02"
    PointToLineOpt = "INSIDE"
    Breaker = False
    NumTypeList = ["SmallInteger", "Integer", "Single", "Double"]

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
    #Constructing Queries
    #-------------------------------------------------------------------
    if FeatureField == "#": #For all polygons
        #Create an SQL query
        SQL_Query = GeoScaler_functions.BuildSQL(InputFeature, champ_result, 0)

    else: #For wanted values only
        #Create an SQL query for wanted symbols only
        SQL_Query_alpha = GeoScaler_functions.BuildSQL(InputFeature, FeatureField, FeatureFieldValue)

        #Create an SQL query for wanted symbols only
        SQL_Query_beta = GeoScaler_functions.BuildSQL(InputFeature, champ_result, 0)

        #Create an AND SQL query
        SQL_Query = SQL_Query_alpha + " AND " + SQL_Query_beta
    #-------------------------------------------------------------------
    #1.Call function M_2aSymPol_01, to generalize polygons first
    #-------------------------------------------------------------------
    GeoScaler_functions.M_2aSymPol_01(InputFeature, FeatureField, FeatureFieldValue, MinArea, champ_result, SQL_Query)

    #-------------------------------------------------------------------
    #2. Select generalized polygons only (coted 0)
    #-------------------------------------------------------------------
    #Create a temp name for output selection
    Scratch_Geol = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

    #Select proper polygons
    AP.Select_analysis(InputFeature, Scratch_Geol, SQL_Query)

    #-------------------------------------------------------------------
    #3. Convert them into point symbols
    #-------------------------------------------------------------------
    #New symbol feature
    if SymFeature == "#":
        AP.FeatureToPoint_management(Scratch_Geol, NewSymFeature, PointToLineOpt)

    #Existing symbol feature
    elif SymFeature != "#":
        #Conversion
        Scratch_Geol_beta = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)
        AP.FeatureToPoint_management(Scratch_Geol, Scratch_Geol_beta, PointToLineOpt)

        #Add field with results in existing feature, for the append mapping to occur
        GeoScaler_functions.VerifyResultingField(SymFeature, champ_result)

        #Verify if wanted field already exists within the new point symbol feature
        DescPNT = AP.Describe(Scratch_Geol_beta)
        FieldsPNT = DescPNT.Fields
        for each_PNT_fields in FieldsPNT:
            if each_PNT_fields.Name == SymFeatureField:
                Breaker = True

        #Retrieve existing field config.
        Desc = AP.Describe(SymFeature)
        Fields = Desc.Fields
        for each_fields in Fields:
            if each_fields.Name == SymFeatureField:
                FieldType = each_fields.type
                FieldPre = each_fields.precision
                FieldScale = each_fields.scale
                FieldLen = each_fields.length
                FieldAlias = each_fields.aliasName
                FieldNull = each_fields.isNullable
                FieldReq = each_fields.required
                FieldDom = each_fields.domain

        #If the field doesn't exist, add it
        if Breaker == False:
            AP.AddField_management(Scratch_Geol_beta, SymFeatureField, FieldType, FieldPre, FieldScale, \
                                   FieldLen, FieldAlias, FieldNull, FieldReq, FieldDom)
        if FieldType == "String":
            AP.CalculateField_management(Scratch_Geol_beta,SymFeatureField, '"' + SymFeatureFieldValue + '"', "VB")
        elif str(FieldType) in NumTypeList:
            AP.CalculateField_management(Scratch_Geol_beta,SymFeatureField, SymFeatureFieldValue, "VB")
        else:
            raise TypeError
        #Append the new points within the desire existing symbol feature
        AP.Append_management([Scratch_Geol_beta], SymFeature, "NO_TEST", "", "")

    else:
        raise AttributeError

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    AP.Delete_management(Scratch_Geol)

    if SymFeature != "#" and NewSymFeature == "#":
        AP.Delete_management(Scratch_Geol_beta)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(champ_result)+".")

except TypeError:
    AP.AddError("Selected output field value is not numeric or text.")
except AttributeError:
    AP.AddError("Missing output feature, enter either an existing or a new output for the resulting point feature.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
