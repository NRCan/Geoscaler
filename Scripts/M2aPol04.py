# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aPol_04.py
# Gabriel Huot-Vézina (LCNP), 2010
#   Analysis before and after polygon generalization features, and will, from
#   a given attribute value search for missing polygons, thus converting them
#   to point symbols. The results will be store in either an existing feature
#   or a new one and will be created.
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
    GeoBefore = sys.argv[1]  #Input polygon feature layer before generalization
    GeoBeforeField = sys.argv[2] #Input polygon feature layer before generalization, field name
    GeoBeforeFieldValue = sys.argv[3] #Input polygon feature layer before generalization, field value
    GeoAfter = sys.argv[4] #Input polygon feature layer after generalization
    GeoAfterField = sys.argv[5] #Input polygon feature layer after generalization, field name
    GeoAfterFieldValue = sys.argv[6] #Input polygon feature layer after generalization, field value
    NewSymFeature = sys.argv[7] #Input new symbol feature name and path.
    SymFeature = sys.argv[8] #Input existing symbol feature.
    SymFeatureField = sys.argv[9] #Input existing symbol feature field name.
    SymFeatureFieldValue = sys.argv[10] #Input existing symbol feature field value.

    #Variables
    FeatureDict = {1:[GeoBefore,GeoBeforeField,GeoBeforeFieldValue], \
                   2:[GeoAfter, GeoAfterField, GeoAfterFieldValue]}
    TempFeatureList = [] #An empty list, will contain output feature for step 1.
    TempLayerList = [] #An empty list,will contain output layers for step 2.
    FieldListSc = [] #An empty list, will contain scratch_output field name
    IDField = "TEMP_ID"
    NumTypeList = ["SmallInteger", "Integer", "Single", "Double"]
    Prefix = "GS"

    #-------------------------------------------------------------------
    #1.Select desire polygons, within feature. (e.g. rock polygons)
    #-------------------------------------------------------------------
    for feat_key in sorted(FeatureDict):
        #Retrieve features parameters within the dictionnary
        FeatName = FeatureDict[feat_key][0]
        FeatField = FeatureDict[feat_key][1]
        FeatValue = FeatureDict[feat_key][2]

        #Create an SQL query
        SQL_Query = GeoScaler_functions.BuildSQL(FeatName, FeatField, FeatValue)

        #Create a temp name for output selection
        Scratch_Geol = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

        #Select proper polygons
        AP.Select_analysis(FeatName, Scratch_Geol, SQL_Query)

        #Keep the outputs within a list
        TempFeatureList.append(Scratch_Geol)

    #-------------------------------------------------------------------
    #2.Select by location polygons with same centroids
    #-------------------------------------------------------------------
    #Make feature layers out of the two temp feature
    for scratch_feat in TempFeatureList:

        #Retrieve the name of the GS features
        GSLayer = string.split(os.path.basename(scratch_feat),".")[0]

        #Create a layer name
        GSLayerName = '"' + GSLayer + '"'

        #Select proper polygons
        AP.MakeFeatureLayer_management(scratch_feat, GSLayerName)

        #Keep the outputs within a list
        TempLayerList.append(GSLayerName)

    #Select same polygons
    AP.SelectLayerByLocation_management(TempLayerList[0], "INTERSECT",TempLayerList[1], "#", "NEW_SELECTION")

    #-------------------------------------------------------------------
    #3.Invert selection, to select polygons that disapeared during
    #   generalization.
    #-------------------------------------------------------------------
    AP.SelectLayerByAttribute_management(TempLayerList[0], "SWITCH_SELECTION")

    #-------------------------------------------------------------------
    #4a.Convert the selection to a point feature:
    #   If the user wants the results within an existing feature
    #-------------------------------------------------------------------
    if SymFeature != "#" and NewSymFeature == "#":
        #Create a temp name for output selection
        Scratch_output = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

        #Copy the selected features within the temp one
        AP.FeatureToPoint_management(TempLayerList[0], Scratch_output, "INSIDE")
        #AP.CopyFeatures_management(TempLayerList[0], Scratch_output)

        #Retrieve original field parameters
        FieldList = AP.ListFields(SymFeature)
        for fields in FieldList:
            if fields.name == SymFeatureField:
                FieldType = fields.type
                FieldPre = fields.precision
                FieldScale = fields.scale
                FieldLen = fields.length
                FieldAlias = fields.aliasName
                FieldNull = fields.isNullable
                FieldReq = fields.required
                FieldDom = fields.domain

        #Retrieve Scratch fields to compare
        FieldListScratch = AP.ListFields(Scratch_output)
        for scratchFields in FieldListScratch:
            FieldListSc.append(scratchFields.name)

        #Create a new field with the same name as the one entered by the user
        if SymFeatureField not in FieldListSc: #If the fields is not the same as input
            AP.AddField_management(Scratch_output, SymFeatureField, FieldType, FieldPre, FieldScale, \
                                   FieldLen, FieldAlias, FieldNull, FieldReq, FieldDom)

        if SymFeatureFieldValue !=  GeoBeforeFieldValue: #If the value is not the same as input
            #Add correct delimiters around field name
            SQL_field = AP.AddFieldDelimiters(SymFeature, SymFeatureField) #[Field] for shapes and gdb, "Field" for mdb

            #Add correct delimiters around field value
            if str(FieldType) == "String":
                SQL_value = "'" + str(SymFeatureFieldValue) + "'"
            elif str(FieldType) in NumTypeList:
                SQL_value = str(SymFeatureFieldValue)
            else:
                raise TypeError

            #Calculate values for the new field, as the old one
            AP.CalculateField_management(Scratch_output, SymFeatureField, SQL_value)

            #Delete the old field
            AP.DeleteField_management(Scratch_output, GeoBeforeField)

        #Merge the resulting features
        AP.Append_management([Scratch_output], SymFeature, "NO_TEST")

    #-------------------------------------------------------------------
    #4b.Convert the selection to a point feature:
    #   If the user wants the results in a newfeature
    #--------------------------------------------------------------------
    elif SymFeature == "#" and NewSymFeature != "#":
        #With the last layer selection, the tool will only convert selected features
        AP.FeatureToPoint_management(TempLayerList[0], NewSymFeature, "INSIDE")

    #-------------------------------------------------------------------
    #If the user didn't entered anything....
    #--------------------------------------------------------------------
    else:
        raise AttributeError

    #------------------------------------------------------------------------------
    #Deleting useless temp data
    #------------------------------------------------------------------------------
    for Scratch_features in TempFeatureList:
        AP.Delete_management(Scratch_features)
    if SymFeature != "#" and NewSymFeature == "#":
        AP.Delete_management(Scratch_output)

except TypeError:
    AP.AddError("Selected output field value is not numeric or text.")
except AttributeError:
    AP.AddError("Missing output feature, enter either an existing or a new output for the resulting point feature.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))
