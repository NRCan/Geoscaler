# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPnt_04.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will generalize all point symbols, with a given priority over each other
# Original work: Gabriel H.V. (LCNP), 2009
# ---------------------------------------------------------------------------
#Import standard lib.
import sys, traceback, string, os
import arcpy as AP

#Import custom lib.
import GeoScaler_functions

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1] #Feature to generalize
    InputField = sys.argv[2] #Field that contains symbols class
    LoadSettingFile = sys.argv[3] #A file with all the setting strings
    Setting_strings = sys.argv[4] #A string with field value, near feature distance and a rank seperated by ";"
    SaveSettingFile = sys.argv[5] #An output file to save the settings strings

    #Field variables
    AvailableFields = [] #An empty list to store previous result field name e.g. B01,B02,B03
    AllFieldName = [] #An empty list to store all the field names from the input feature
    NEAR_FID = "NEAR_FID" #Found in the input feature and generated near table
    IN_FID = "IN_FID" #Found in the generated near table
    DupID = "DupID" #Will a contain a copy of each IDs

    #Other variables
    FeatureLayer = "InputFeature"
    FeatureLayer2 = "InputFeature2"
    SettingList = Setting_strings.split(";") #Split the Setting_strings into a list
    ScriptList = ["M2aSymPnt01", "M2aSymPnt02", "M2aSymPnt03"] #A list of script names to retrieve result fields
    Prefix = "B04_" #A prefix for temp output data
    Generalized_symbol_list = []
    Number_iter = 1 #An iterative variable to display in messages

    #-------------------------------------------------------------------
    #Retrieve generalization results field
    #-------------------------------------------------------------------
    ResultField_Prefix = GeoScaler_functions.FieldDictionnary(ScriptName)
    ResultField = GeoScaler_functions.BuildResultingField(ResultField_Prefix)
    GeoScaler_functions.VerifyResultingField(InputFeature, ResultField)

    #-------------------------------------------------------------------
    #Save the setting strings within a text file
    #-------------------------------------------------------------------
    if SaveSettingFile != "#":
        GeoScaler_functions.SaveSettingToFile(SaveSettingFile, SettingList)

    #-------------------------------------------------------------------
    #Prepare the data
    #-------------------------------------------------------------------
    #Describe the feature to find certain fields
    Desc = AP.Describe(InputFeature)
    Fields = Desc.Fields #A list of fields
    Feature_ID_Field = Desc.OIDFieldName #The identification field

    #List all field names
    for all_fields in Fields:
        AllFieldName.append(all_fields.Name)

    #Duplicate the objectid
    if DupID not in AllFieldName:
        AP.AddField_management(InputFeature, DupID, "LONG")
    FieldDelimiters = '[' + Feature_ID_Field + ']'
    AP.CalculateField_management(InputFeature, DupID, FieldDelimiters)

    #Create a lyr file, for selection purposes
    AP.MakeFeatureLayer_management(InputFeature, FeatureLayer)
    AP.MakeFeatureLayer_management(InputFeature, FeatureLayer2)

    #-------------------------------------------------------------------
    #Merge previous generalization results into the current result field
    #-------------------------------------------------------------------
    #List previous generalization fields
    for scripts in ScriptList:
        PreviousResults = GeoScaler_functions.FieldDictionnary(scripts) + ResultField.split("_")[-1]

        #Build a list of available previous fields
        if PreviousResults in AllFieldName:
            AvailableFields.append(PreviousResults)

    #Verify if there is previous fields
    if len(AvailableFields) != 0:
        #Start an update cursor to merge previous generalization results
        UpCursor = AP.UpdateCursor(FeatureLayer)
        for elements in UpCursor:

            ResultList = [] #A list with the results

            #Iterate through result field and retrieve the data
            for data in AvailableFields:
                ResultList.append(elements.getValue(data))

            #Append the results
            if 0 in ResultList:
                elements.setValue(ResultField,0)
            else:
                elements.setValue(ResultField,1)
            UpCursor.updateRow(elements)

        del elements, UpCursor

    else:
        #Calculate every line with 1
        AP.CalculateField_management(FeatureLayer, ResultField, 1)

    #-------------------------------------------------------------------
    #Generalization
    #-------------------------------------------------------------------
    for priorities in sorted(SettingList):
        #Proceed if not at the last item in the list, doesn't need to be generalized
        if priorities != SettingList[-1]:

            #Build a second iteration, to generalize current symbol with all the other one
            Iter = range(len(SettingList) - SettingList.index(priorities) - 1)
            for i in Iter:

                #Retrieve symbol names
                Current_symbol = str(priorities.split(",")[1])
                Next_symbol = str(SettingList[SettingList.index(priorities) + 1 + Iter.index(i)].split(",")[1])

                #Retrieve symbol near feature distance
                Current_NFD = int(priorities.split(",")[2])
                Next_NFD = int(SettingList[SettingList.index(priorities) + 1 + Iter.index(i)].split(",")[2])

                #Retrieve priority number from item list
                Current_priority = int(priorities.split(",")[0])
                Next_priority = int(SettingList[SettingList.index(priorities) + 1 + Iter.index(i)].split(",")[0])

                #Make sure the next priority is not the same
                Item = 2 #Start an iterator
                while Next_priority == Current_priority:
                    #For same values, retrieve next value
                    Next_priority = int(SettingList[SettingList.index(priorities) + Item].split(",")[0])
                    Next_symbol = str(SettingList[SettingList.index(priorities) + Item + Iter.index(i)].split(",")[1])
                    Next_NFD = int(SettingList[SettingList.index(priorities) + Item + Iter.index(i)].split(",")[2])

                    Item = Item + 1

                #Build a symbol tuple to detect if the current analysis has already been done
                Symbol_tuple = "(" + Current_symbol + "," +  Next_symbol + ")"

                #Calculate a new NFD
                NEW_NFD = Current_NFD/2 + Next_NFD/2

                #---Setting parameter for generalization
                if Current_priority < Next_priority:
                    if Symbol_tuple not in Generalized_symbol_list:

                        #Variables
                        NeighbourList = [] #A list with all neighbours in current iteration

                        #Append the list with proper information
                        Generalized_symbol_list.append(Symbol_tuple)
                        AP.AddMessage(str(Number_iter) + ". Generalization of superposed symbols  between " + Current_symbol + " and " + Next_symbol + "...")

                        #Clean selections and count the number of rows
                        AP.SelectLayerByAttribute_management(FeatureLayer2, "CLEAR_SELECTION")
                        CountBefore = AP.GetCount_management(FeatureLayer2)

                        #Build queries
                        SQL_CurrentSymbol = GeoScaler_functions.BuildSQL(InputFeature,InputField,Current_symbol) + " AND " + str(ResultField) + " = 1"
                        SQL_NextSymbol = GeoScaler_functions.BuildSQL(InputFeature,InputField,Next_symbol) + " AND " + str(ResultField) + " = 1"

                        #Select current symbol class and next symbol class
                        AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", SQL_CurrentSymbol)
                        AP.SelectLayerByAttribute_management(FeatureLayer2, "NEW_SELECTION", SQL_NextSymbol)

                        #Apply a selection with calculated NFD and recount number of rows
                        AP.SelectLayerByLocation_management(FeatureLayer2, "INTERSECT", FeatureLayer, NEW_NFD, "SUBSET_SELECTION")
                        CountAfter = AP.GetCount_management(FeatureLayer2)

                        #Continu if the intersection with NFD returned something
                        if CountBefore != CountAfter and str(CountAfter) != "0":

                            #Create a new feature with only the selection, because we need to iterate through that selection
                            #Can't perform it with a cursor
                            ScratchSelection = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)
                            AP.Select_analysis(FeatureLayer2, ScratchSelection)

                            #Get IDs from new feature of neighbours
                            SelectionCursor = AP.SearchCursor(ScratchSelection)
                            for rows in SelectionCursor:
                                NeighbourList.append(rows.getValue(DupID))
                            del rows, SelectionCursor

                            #Update the original feature with 0 coted symbols
                            UpCursor = AP.UpdateCursor(InputFeature)
                            for each_lines in UpCursor:
                                if each_lines.getValue(DupID) in NeighbourList:
                                    each_lines.setValue(str(ResultField), 0)

                                UpCursor.updateRow(each_lines)
                            del each_lines, UpCursor

                            #Del temp data
                            AP.Delete_management(ScratchSelection)

                        #Iterate number displayed in the messages.
                        Number_iter = Number_iter + 1
    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(ResultField)+".")

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))