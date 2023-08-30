# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_4a_Regroupe.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will manage all generalization fields, for symbols, into 2 new single field
# ---------------------------------------------------------------------------

#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP

#Import custom libraries
from GeoScaler_functions import *

#Error handling classes
class CustomError(Exception): pass #Mother class
class ResultError(CustomError):pass #child class

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    DeleteField = sys.argv[1] #If user wants to delete all old fields or not.
    InputFeatures = sys.argv[2].split(";") #All features that needs to have the new fields

    #Variables
    ModelDictionnary = FieldDictionnary("Dictionnary")
    FromField = ResultFieldDictionnary("From") #Get name for SCALE_FROM field
    ToField = ResultFieldDictionnary("To") #Get name for SCALE_TO field
    FieldType = "LONG" #Short doesn't take number with more than 6 caracters...
    PrefixList = [] #An empty list to contain all the prefix and hierarchy numbers from model dictionnary
    CurrentScaleList = [] #An empty list to contain previous scale contained in field name
    UnwantedFields = [] #An empty list to contain all previous generalization resulting fields, in case users wants to delete them
    InitialScale = int(RetrieveInfoFromXML(["Initial_Scale"])[0])/1000 # Retrieve initial scale from XML environment file.
    DefaultFromField = InitialScale #Default "From scale", if not more then 1 scale has been found and FromField and ToField, didn't contains anything at first
    UnknownValue = False #Will detect if a value other than 0 or 1 is within a field

    #-------------------------------------------------------------------
    #Build hierarchy based on result field
    #-------------------------------------------------------------------
    for elements in ModelDictionnary:
        PrefixList.append(ModelDictionnary[elements]) #Last element contains hierarchy

    #-------------------------------------------------------------------
    #Iterate for all features
    #-------------------------------------------------------------------
    for features in InputFeatures:

        #-------------------------------------------------------------------
        #Prepare data
        #-------------------------------------------------------------------
        #Get feature name
        FeatureName = os.path.basename(features)

        #Get feature geometry
        Geom = AP.Describe(features).ShapeType.lower()
        AP.AddMessage("Processing script for feature: " + str(FeatureName))

        #-------------------------------------------------------------------
        #Adding fields
        #-------------------------------------------------------------------
        #Verify existence of new field, if not add them
        FieldList_obj = AP.ListFields(features) #Get list of fields within feature
        FieldList = [] #A list to contain all fields within each features
        for objects in FieldList_obj:
            FieldList.append(objects.name)

        if FromField not in FieldList:
            #Create field
            AP.AddField_management(features,FromField,FieldType)

        if ToField not in FieldList:
            #Create field
            AP.AddField_management(features,ToField,FieldType)

        #-------------------------------------------------------------------
        #Get last field containing results
        #-------------------------------------------------------------------
        #Variables
        LastFieldPriority = 0
        LastField = []
        LastField_0 = [] #An empty list, in case all the priority fields are listed as 0

        #Iterate through old and known field
        for fields_1 in PrefixList:
            #Iterate through current feature fields
            for fields_2 in FieldList:
                #Find concordence
                if fields_1[0] in fields_2:
                    #Validate geometry -- could be discordance for polygons that were transformed into points
                    if Geom in fields_1[2]:
                        #Build a list of unwanted fields if necessary
                        UnwantedFields.append(fields_2)

                        #Validate priority
                        if fields_1[1] != 0 and fields_1[1] > LastFieldPriority:
                            #Get name
                            LastField.append(fields_2)

                            #Add to priority list
                            LastFieldPriority = fields_1[1]

                        elif fields_1[1] != 0 and fields_1[1] == LastFieldPriority:
                            #Get name
                            LastField.append(fields_2)
                            #Add to priority list
                            LastFieldPriority = fields_1[1]

                        #Manage case of user that didn't want trough normal process of generalization (ex: he stopped at B01 instead of finishing at B04).
                        elif fields_1[1] == 0 and LastFieldPriority == 0:
                            #Remove any previous values if necessary
                            #First occurence
                            if LastField_0 == []:
                                #Add to priority list
                                LastField_0.append(fields_2)
                                LastFieldPriority = fields_1[1]

                            if int(fields_1[0][2])> int(LastField_0[0][2]):
                                #Remove all values and add the new one
                                LastField_0 = []
                                LastField_0.append(fields_2)
                                LastFieldPriority = fields_1[1]

        #If user really didn't went through normal process, convert lists
        if LastFieldPriority == 0:
            #If something was found
            if len(LastField_0) != 0:
                LastField = LastField_0
            else:
                raise ResultError

        #-------------------------------------------------------------------
        #If multiple scale results are presents (e.g. A01_250k, A01_500k)
        #Build a dictionnary of hierarchy based on scale (From...To)
        #-------------------------------------------------------------------
        FromToScaleDict = {} #A dictionnary to contain ordered scales

        if len(LastField) > 1:
            for fields in LastField:
                #Build dictionnary
                FieldName = fields.split("_")[0]
                if FieldName not in FromToScaleDict:
                    #Add an empty to dictionnary key
                    FromToScaleDict[FieldName] = []

                #Append scale to dictionnary key
                Scale = fields.split("_")[-1].split("k")[0]
                FromToScaleDict[FieldName].append(int(Scale))

                #Sort the new list
                FromToScaleDict[FieldName].sort()

                #Build real From To dict. (i.e. eliminate possible in between scales from dictionnary)
                if len(FromToScaleDict[FieldName]) > 2:
                    FromToScaleDict[FieldName] = [FromToScaleDict[FieldName][0], FromToScaleDict[FieldName][-1]]
        else:
            Scale = LastField[0].split("_")[-1].split("k")[0]
            FromToScaleDict[LastField[0].split("_")[0]] = [DefaultFromField]
            FromToScaleDict[LastField[0].split("_")[0]].append(int(Scale))

        #-------------------------------------------------------------------
        #Add scale info line by line
        #-------------------------------------------------------------------
        Cursor = AP.UpdateCursor(features)
        for lines in Cursor:
            #Iterate through dictionnary
            for elements in FromToScaleDict:
                #Rebuild field names
                RebuildFromField = elements + "_" + str(FromToScaleDict[elements][0]) + "k"
                RebuildToField = elements + "_" + str(FromToScaleDict[elements][-1]) + "k"

                #Get results
                try:
                    FromResult = lines.getValue(RebuildFromField)
                except:
                    FromResult = 1 #If initial scale generalized field doesn't exists, put 1 as value

                ToResult = lines.getValue(RebuildToField)

                #Apply tranformation rules to FromTo fields
                if FromResult not in [0,1] or ToResult not in [0,1]: #For null values if it happens
                    UnknownValue = True
                    FromResult_ = FromResult
                    ToResult_ = ToResult
                    FromField_ = RebuildFromField
                    ToField_ = RebuildToField
                else:
                    #For situations with only one field of results
                    if len(FromToScaleDict[elements]) == 1:

                        if FromResult == 0 and ToResult == 0:
                            SetFrom = DefaultFromField * 1000 #Multiply by 1000 because scale within field name is in k unit
                            SetTo = DefaultFromField * 1000
                        elif FromResult == 1 and ToResult == 0:
                            SetFrom = DefaultFromField * 1000
                            SetTo = DefaultFromField * 1000
                        elif FromResult == 1 and ToResult == 1:
                            SetFrom = DefaultFromField * 1000
                            SetTo = int(FromToScaleDict[elements][-1]) * 1000
                        elif FromResult == 0 and ToResult == 1:
                            SetFrom = int(FromToScaleDict[elements][-1]) * 1000
                            SetTo = int(FromToScaleDict[elements][-1]) * 1000

                    #For situations with only more than one field of results
                    elif len(FromToScaleDict[elements]) > 1:

                        if FromResult == 0 and ToResult == 0:
                            SetFrom = DefaultFromField * 1000 #Multiply by 1000 because scale within field name is in k unit
                            SetTo = DefaultFromField * 1000
                        elif FromResult == 1 and ToResult == 0:
                            SetFrom = int(FromToScaleDict[elements][0]) * 1000
                            SetTo = int(FromToScaleDict[elements][0]) * 1000
                        elif FromResult == 1 and ToResult == 1:
                            SetFrom = int(FromToScaleDict[elements][0]) * 1000
                            SetTo = int(FromToScaleDict[elements][-1]) * 1000
                        elif FromResult == 0 and ToResult == 1:
                            SetFrom = int(FromToScaleDict[elements][-1]) * 1000
                            SetTo = int(FromToScaleDict[elements][-1]) * 1000

                    #Set transformation
                    lines.setValue(FromField, SetFrom)
                    lines.setValue(ToField, SetTo)
                    Cursor.updateRow(lines)

        del Cursor, lines

        #Label a late warning to user (prevents from seeing it for each process rows)
        if UnknownValue == True:
            AP.AddWarning("Wrong values in one of these fields: " + str(FromResult_) + " in " + FromField_ + ", or " + str(ToResult_) + " in " + ToField_)

        #-------------------------------------------------------------------
        #If users wants to delete old fields
        #-------------------------------------------------------------------
        if str(DeleteField) == "true":
            AP.AddMessage("Deleting old result fields.")
            for fields in UnwantedFields:
                AP.DeleteField_management(features, fields)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in fields: " + str(FromField)+" and " + str(ToField))

except ResultError:
     AP.AddError("Entered feature (" + FeatureName + ") doesn't include any GeoScaler generalization fields.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))