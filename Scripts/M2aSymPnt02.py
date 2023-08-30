# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aSymPnt_02.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will generalize glacial striae by giving symbols a priority number based
#   on chronology, flow direction and relative angle between each other.
# Original work: Gabriel H.V. (LCNP), 2009
###NEEDS ARCINFO LICENCE
# ---------------------------------------------------------------------------

#The next function will determine wich symbol needs to be coted 0, by comparing
#priorities, relative chronologies and mean angles
#---
def compare_symbols(ToBeCoted0_list, nearest_id, nearest_group_id, nearest_priority, nearest_chronology, nearest_mean_angle, nearest_angle, \
                    current_id, current_group_id, current_priority, current_chronology, current_mean_angle, current_angle, min_angle):
    #Variables
    Warning = None

    #---Compare priorities of the two features
    if current_priority < nearest_priority:
        ToBeCoted0_list.append(nearest_id)

    elif current_priority > nearest_priority:
        ToBeCoted0_list.append(current_id)

    elif current_priority == nearest_priority:
        #---Compare chronologies of the two features
        if current_chronology > nearest_chronology:
            ToBeCoted0_list.append(nearest_id)

        elif current_chronology < nearest_chronology:
            ToBeCoted0_list.append(current_id)

        elif current_chronology == nearest_chronology:
            #---Compare mean angles of the two features
            if current_mean_angle > nearest_mean_angle:
                ToBeCoted0_list.append(nearest_id)

            elif current_mean_angle < nearest_mean_angle:
                ToBeCoted0_list.append(current_id)

            elif current_mean_angle == nearest_mean_angle:
                #---May be symbols of priority 7 or 8, needs further analysis
                if current_priority >= 7 or nearest_priority >= 7:
                    #---Compare angles
                    if abs(nearest_angle-current_angle)<= int(min_angle):
                        ToBeCoted0_list.append(current_id)
                    else: #Both symboles needs to be conserved
                        pass

                else:
                    ToBeCoted0_list.append(current_id)
                    ToBeCoted0_list.append(nearest_id)
                    Warning = "Current group of symbol: " + str(current_group_id) + "(id) needs to be hand generalized, because " + \
                                  "it is identical to it's nearest neighbour symbol or group id:" + str(nearest_group_id) + "."
    return ToBeCoted0_list, Warning

#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP

#Import custom libraries
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class ImportError(CustomError):pass #Child class

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1] #Feature to generalize
    AzimField = sys.argv[2]# Field that contains azimuthal angle of glacial striae
    ChronoField = sys.argv[3] #Field that contains relative chronology of glacial striae between each others
    FlowField = sys.argv[4]#Field that contains the flow direction of glacial striae
    KnownFlowValue = sys.argv[5] #Value for known flow direction
    UnknownFlowValue = sys.argv[6] #Value for unknown flow direction
    Length = sys.argv[7] #Value for the glacial striae length, in meters
    MinAngle = sys.argv[8] #Value for minimum tolerable angle between each striae
    StepNumber = sys.argv[9] #The number of user desire generalization steps, equal to priorities

    #Variables
    Buffer = 75 #Min. width of buffer to be created, in meters, should be enough small to detect group of symbols.
    NearLocation = "NO_LOCATION"
    NearAngle = "NO_ANGLE"
    NearIDField = "NEAR_FID" #Found in the input feature and generated near table
    NearDistField = "NEAR_DIST"
    NearIN_FID = "IN_FID" #Found in the generated near table
    Prefix = "SP2" #Prefix for temps features or tables
    Sym_pair = {} #Dictionnary that will contains, first only groups of two symbols than all groups
    Sym_group = {} #Dictionnary that will contains only groups of 3 and more symbols
    Near_liste = [] #A list that will contain all of the NEAR_FID info
    Dissolve_stat_type = "FIRST"
    Dissolve_generalized = [] #A list containing generalization info in the dissolved feature
    FC_Dissolve_dict = {} #A copy of dissolved feature attribute table within a python dictionnary

    #Field variables
    PriorityFields = ["PRIORITY", "GROUP_ID", "SUM_CHRONO", "MEAN_ANGLE", "HETEROGENE"]
    DissolvedPriorityFields = ["FIRST_PRIO", "GROUP_ID", "FIRST_SUM_", "FIRST_MEAN", "FIRST_B02_", "FIRST_PNT_"]

    #Field values variables
    HeterogeneityValues = [1, 2, 3] #["STRSC_ONLY", "STRSI_ONLY", "MIXED"]

    #Other variables
    FeatureLayer = "InputFeature"
    #-------------------------------------------------------------------
    #Verify the product licence, scripts need ArcInfo
    #-------------------------------------------------------------------
    if GeoScaler_functions.RequestArcInfo() != "":
        raise ImportError

    #-------------------------------------------------------------------
    #Add final result field, if needed.
    #-------------------------------------------------------------------
    FinalResultField_alpha = GeoScaler_functions.FieldDictionnary(ScriptName)
    FinalResultField = GeoScaler_functions.BuildResultingField(FinalResultField_alpha)
    GeoScaler_functions.VerifyResultingField(InputFeature, FinalResultField)

    #-------------------------------------------------------------------
    #Create a feature layer for only entered symbols
    #-------------------------------------------------------------------
    #Build a correct SQL query
    SQL_query_known = GeoScaler_functions.BuildSQL(InputFeature,FlowField,KnownFlowValue)
    SQL_query_unknown = GeoScaler_functions.BuildSQL(InputFeature,FlowField,UnknownFlowValue)

    AP.MakeFeatureLayer_management(InputFeature, FeatureLayer, SQL_query_known + " OR " + SQL_query_unknown)

    #-------------------------------------------------------------------
    #Manage field to contains priority analysis results
    #-------------------------------------------------------------------
    #Describe the feature
    Desc = AP.Describe(FeatureLayer)
    Fields = Desc.Fields
    Feature_ID_Field = Desc.OIDFieldName #will be use in "Find symbol grouping" step
    CurrentFields = []

    #List all field names
    for each_fields in Fields:
        CurrentFields.append(each_fields.Name)

    #Iterate through priority fields, if they don't exists add them
    for priority_fields in PriorityFields:
        if priority_fields not in CurrentFields:
            AP.AddField_management(FeatureLayer, priority_fields, "LONG")

    #Reset first priority field to 0
    AP.CalculateField_management(FeatureLayer, PriorityFields[0], 0)

    #Reset final field, that will contain generalization results, to 1
    AP.CalculateField_management(FeatureLayer, FinalResultField, 1)

    #Find field delimiters for ID, will be use to tag groups of symbols
    IDFieldDelimiters = AP.AddFieldDelimiters(FeatureLayer, Feature_ID_Field)

    #-------------------------------------------------------------------
    #Find symbol grouping
    #-------------------------------------------------------------------
    AP.AddMessage("\nFinding and assigning id to groups of glacial striae...")

    #Create a temp name for near table
    Scratch_table = AP.CreateScratchName(Prefix, "", "ArcInfoTable", Script_path)

    #Create a Near table
    AP.GenerateNearTable_analysis(FeatureLayer, FeatureLayer, Scratch_table, Buffer, NearLocation, NearAngle, "ALL")

    #Iterate through near table to find grouping of 2 symbols
    Cursor_alpha = AP.SearchCursor(Scratch_table)
    for lines in Cursor_alpha:
        Near_liste.append(lines.getValue(NearIDField))
        Sym_pair[lines.getValue(NearIN_FID)] = [lines.getValue(NearIDField)]

        if lines.getValue(NearIN_FID) in Near_liste:
            if lines.getValue(NearIDField) in Sym_pair:
                del Sym_pair[lines.getValue(NearIN_FID)]

    #Iterate through near table to find grouping of 3 and more symbols
    Cursor_beta = AP.SearchCursor(Scratch_table)
    for lines in Cursor_beta:
        Sym_group[lines.getValue(NearIN_FID)] = [lines.getValue(NearIDField)]
        if lines.getValue(NearIN_FID) not in Sym_pair:
            if lines.getValue(NearIN_FID) in Sym_group:
                Sym_group[lines.getValue(NearIN_FID)].append(lines.getValue(NearIDField))
        else:
            del Sym_group[lines.getValue(NearIN_FID)]

    #Append both dictionnary within the first one and eliminate duplicate values
    for keys in Sym_group:
        if keys not in Sym_pair:
            key_id = Sym_group[keys][0]
            Sym_pair[key_id].append(keys)
            Sym_pair[key_id] = list(set(Sym_pair[key_id]))

    #Iterate through dictionnary to update groups numbers
    for each_symbols in Sym_pair:
        #Query beginning
        Sym_string = IDFieldDelimiters + " = " + str(each_symbols)
        #Build the rest of the query
        for items in Sym_pair[each_symbols]:
            Sym_string = Sym_string + " OR " + IDFieldDelimiters + " = " + str(items)

        #Update group id
        Cursor_gamma = AP.UpdateCursor(FeatureLayer, Sym_string)
        for group in Cursor_gamma:
            AP.AddMessage(PriorityFields[1] + "  " + str(each_symbols))
            group.setValue(PriorityFields[1], each_symbols)
            Cursor_gamma.updateRow(group)
        del Cursor_gamma, group

    del Cursor_alpha, Cursor_beta, lines
    AP.Delete_management(Scratch_table)
    #-------------------------------------------------------------------
    #Calculate sum of rel. chrono. and angles.
    #-------------------------------------------------------------------
    AP.AddMessage("Evaluating relative chronology and angles within groups of glacial striae...")

    Group_dictionnary = Sym_pair

    #Iterate through dictionnary
    for each_groups in Group_dictionnary:

        #Variables
        Breaker_STRSC = False #Will be usefull in detecting known flow striae within a group of symbols
        Breaker_STRSI = False #Will be usefull in detecting unknown flow striae within a group of symbols
        Sum_chrono = 0 #Iterator to sum relative chronology within symbol groups
        Sum_angle = 0 #Iterator to sum angles within symbol groups
        Mean_angle = 0 #For angle mean
        Sum_symbols = 0 #For number of symbols within a group
        Diff_angle = 0 #For difference between symbols within a group

        #Query beginning
        Sym_string = IDFieldDelimiters + " = " + str(each_groups)
        #Build the rest of the query
        for items in Group_dictionnary[each_groups]:
            Sym_string = Sym_string + " OR " + IDFieldDelimiters + " = " + str(items)

        #Iterate to retrieve info.
        Cursor_sum = AP.SearchCursor(FeatureLayer, Sym_string)
        for results in Cursor_sum:
            #Detect priority homogeneity of symbols within each groups
            if results.getValue(FlowField) == KnownFlowValue:
                Breaker_STRSC = True
            elif results.getValue(FlowField) == UnknownFlowValue:
                Breaker_STRSI = True

            #Sum relative chronology within each groups
            try:#If it goes wrong, the value trying to convert into an integer is empty, it means no chronology
                Sum_chrono = Sum_chrono + int(results.getValue(ChronoField))
            except:
                Sum_chrono = Sum_chrono + 0

            #Sum angle within each groups
            try: #If it goes wrong, the value trying to convert into an integer is empty, it means no chronology
                Sum_angle = Sum_angle + int(results.getValue(AzimField))
            except:
                Sum_angle = Sum_angle + 0

            #Sum the number of symbols within each groups
            Sum_symbols = Sum_symbols + 1

            #For each symbols, calculate the angle difference with the last one.
            Diff_angle = abs(Diff_angle - int(results.getValue(AzimField)))

        del results, Cursor_sum

        #Calculate mean angle for each groups
        Mean_angle = Sum_angle / Sum_symbols

        #Update info.
        Cursor_mean = AP.UpdateCursor(FeatureLayer, Sym_string)
        for results in Cursor_mean:
            #Update sum chrono
            results.setValue(PriorityFields[2], Sum_chrono)
            #Update mean angle
            results.setValue(PriorityFields[3], Mean_angle)
            #Update heterogeneity field
            if Breaker_STRSC == True and Breaker_STRSI == True:
                results.setValue(PriorityFields[4], HeterogeneityValues[2])
            elif Breaker_STRSC == False and Breaker_STRSI == True:
                results.setValue(PriorityFields[4], HeterogeneityValues[1])
            elif Breaker_STRSC == True and Breaker_STRSI == False:
                results.setValue(PriorityFields[4], HeterogeneityValues[0])

            Cursor_mean.updateRow(results)
        del Cursor_mean, results

    #-------------------------------------------------------------------
    #Prioritize symbols between each_other
    #-------------------------------------------------------------------
    #---Priority 8 - Isolated unknown flow direction striae
    if int(StepNumber) == 8:
        AP.AddMessage("Assigning priority 8 to Isolated unknown flow direction striae...")

        #Detect symbol group with Near analysis within defined small buffer
        AP.Near_analysis(FeatureLayer, FeatureLayer, Buffer, NearLocation, NearAngle)

        #Build a query to select desire symbols --> "CODE" = 'STRSI' AND "NEAR_FID" = -1
        SQL_query = GeoScaler_functions.BuildSQL(FeatureLayer,FlowField,UnknownFlowValue) + " AND " + \
                    GeoScaler_functions.BuildSQL(FeatureLayer,NearIDField,-1)

        #Create update cursor
        CursorP8 = AP.UpdateCursor(FeatureLayer, SQL_query)

        for lines in CursorP8:
            #Set the priority to 8
            lines.setValue(PriorityFields[0],8)
            #Give a group number
            lines.setValue(PriorityFields[1], str(lines.getValue(Feature_ID_Field)))
            CursorP8.updateRow(lines)

        del CursorP8, lines #To prevent some locks

    #---Priority 7 - Isolated known flow direction striae
    if int(StepNumber) > 7:
        AP.AddMessage("Assigning priority 7 to Isolated known flow direction striae...")

        #Build a query to select desire symbols --> "CODE" = 'STRSI' AND "NEAR_FID" = -1
        SQL_query = GeoScaler_functions.BuildSQL(FeatureLayer,FlowField,KnownFlowValue) + " AND " + \
                    GeoScaler_functions.BuildSQL(FeatureLayer,NearIDField,-1)

        #Create update cursor
        CursorP7 = AP.UpdateCursor(FeatureLayer, SQL_query)

        for lines in CursorP7:
            #Set the priority to 7
            lines.setValue(PriorityFields[0],7)
            #Give a group number
            lines.setValue(PriorityFields[1], str(lines.getValue(Feature_ID_Field)))
            CursorP7.updateRow(lines)

        del CursorP7, lines #To prevent some locks

    #---Priority 1 to 6 - Groups of symbols
    AP.AddMessage("Assigning priority 6 to 1, symbol groups...")
    for each_groups in Group_dictionnary:
        #Query beginning
        Sym_string = IDFieldDelimiters + " = " + str(each_groups)
        #Build the rest of the query
        for items in Group_dictionnary[each_groups]:
            Sym_string = Sym_string + " OR " + IDFieldDelimiters + " = " + str(items)

        #Update info.
        Cursor_groups = AP.UpdateCursor(FeatureLayer, Sym_string)
        for lines in Cursor_groups:

            #Detect heterogeneity of symbol group
            if lines.getValue(PriorityFields[4]) == 2:
                #---Priority 5 and 6 - Group of unknown flow direction striae (6 - without relative chrono.; 5 - with relative chrono.)
                if int(StepNumber) > 4:
                    if int(lines.getValue(PriorityFields[2])) == 0:
                        lines.setValue(PriorityFields[0], 6)
                    elif int(lines.getValue(PriorityFields[2])) != 0:
                        lines.setValue(PriorityFields[0], 5)

            if lines.getValue(PriorityFields[4]) == 3:
                #---Priority 4 and 3 - Group of unknown and known flow direction striae (4 - without relative chrono.; 3 - with relative chrono.)
                if int(StepNumber) > 2:
                    if int(lines.getValue(PriorityFields[2])) == 0:
                        lines.setValue(PriorityFields[0], 4)
                    elif int(lines.getValue(PriorityFields[2])) != 0:
                        lines.setValue(PriorityFields[0], 3)

            if lines.getValue(PriorityFields[4]) == 1:
                #---Priority 2 and 1 - Group of known flow direction striae (2 - without relative chrono.; 1 - with relative chrono.)
                if int(StepNumber) > 2:
                    if int(lines.getValue(PriorityFields[2])) == 0:
                        lines.setValue(PriorityFields[0], 2)
                    elif int(lines.getValue(PriorityFields[2])) != 0:
                        lines.setValue(PriorityFields[0], 1)

            Cursor_groups.updateRow(lines)
        del Cursor_groups, lines

    #-------------------------------------------------------------------
    #Generalization of symbols and symbol groups
    #-------------------------------------------------------------------
    AP.AddMessage("Dissolving symbol groups before generalization...")

    #Create a scratchname
    Scratch_diss = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

    #Dissolving groups of symbols into unique entities
    AP.Dissolve_management(FeatureLayer,Scratch_diss, PriorityFields[1], [[PriorityFields[0],Dissolve_stat_type], \
                                                                          [PriorityFields[2],Dissolve_stat_type], \
                                                                          [PriorityFields[3],Dissolve_stat_type], \
                                                                          [FinalResultField, Dissolve_stat_type], \
                                                                          [AzimField, Dissolve_stat_type]], "MULTI_PART")

    #Describe the feature
    Desc_diss = AP.Describe(Scratch_diss)
    FID_Field_diss = Desc_diss.OIDFieldName

    #Iterate through dissolved layer and rebuild attribute table within a custom dictionnary
    Cursor_dict = AP.SearchCursor(Scratch_diss)
    for lines in Cursor_dict:
        Attr_list = []
        #Build list
        Attr_list.append(lines.getValue(DissolvedPriorityFields[1])) #GROUP ID
        Attr_list.append(lines.getValue(DissolvedPriorityFields[0])) #PRIORITY
        Attr_list.append(lines.getValue(DissolvedPriorityFields[2])) #SUM CHRONO
        Attr_list.append(lines.getValue(DissolvedPriorityFields[3])) #MEAN ANGLE
        Attr_list.append(lines.getValue(DissolvedPriorityFields[4])) #ANGLE

        #Build dictionnary
        FC_Dissolve_dict[lines.getValue(FID_Field_diss)] = Attr_list
    del lines, Cursor_dict

    #SQL variables
    NeighboursM = True #Variable to detect multiple superposed symbols
    NeighboursS = True #Variable to detect simple superposed symbols
    Scratch_diss_lyr = "Scratch_diss"
    AP.MakeFeatureLayer_management(Scratch_diss, Scratch_diss_lyr)
    SQL_query_update = GeoScaler_functions.BuildSQL(Scratch_diss_lyr, DissolvedPriorityFields[4],1)

    #---Multiple superposed symbols generalization
    AP.AddMessage("Generalizing multiple superposed symbols...")
    while NeighboursM==True:

        NeighboursM=False #Re-initialization of the variable

        #Apply a new near analysis on the dissolved feature
        AP.SelectLayerByAttribute_management(Scratch_diss_lyr, "NEW_SELECTION", str(DissolvedPriorityFields[4]) + " = 1")
        AP.Near_analysis(Scratch_diss_lyr, Scratch_diss_lyr, Length, NearLocation, NearAngle)
        AP.SelectLayerByAttribute_management(Scratch_diss_lyr, "CLEAR_SELECTION")

        #Create update cursor
        SQL_query_search = SQL_query_update + " AND " + GeoScaler_functions.BuildComplexSQL(Scratch_diss_lyr,NearIDField,-1, "<>")
        Cursor_gene = AP.SearchCursor(Scratch_diss_lyr, SQL_query_search)

        #Create an empty list to stock superposed symbols
        UniqueList = [] #To find duplicate
        ToBeCoted0 = [] #To store duplicate

        for lines in Cursor_gene:
            if lines.getValue(NearIDField) not in UniqueList:
                UniqueList.append(lines.getValue(NearIDField))
            else:
                #Retrieve info about the nearest feature around the multiple superposed symbol
                nearest_id = lines.getValue(NearIDField)
                nearest_group_id = FC_Dissolve_dict[nearest_id][0]
                nearest_priority = FC_Dissolve_dict[nearest_id][1]
                nearest_chronology = FC_Dissolve_dict[nearest_id][2]
                nearest_mean_angle = FC_Dissolve_dict[nearest_id][3]
                nearest_angle = FC_Dissolve_dict[nearest_id][4]
                current_id = lines.getValue(FID_Field_diss)
                current_group_id = lines.getValue(DissolvedPriorityFields[1])
                current_priority = lines.getValue(DissolvedPriorityFields[0])
                current_chronology = lines.getValue(DissolvedPriorityFields[2])
                current_mean_angle = lines.getValue(DissolvedPriorityFields[3])
                current_angle = lines.getValue(DissolvedPriorityFields[4])

                #Call the custom function to compare symbols, see top of script
                Func_result = compare_symbols(ToBeCoted0, nearest_id, nearest_group_id, nearest_priority, nearest_chronology, \
                                              nearest_mean_angle, nearest_angle, current_id, current_group_id, current_priority, current_chronology, \
                                              current_mean_angle, current_angle, MinAngle)
                ToBeCoted0 = Func_result[0]

                #Add warning if necessary
                if Func_result[1] != None:
                    AP.AddWarning(Func_result[1])

        del lines, Cursor_gene

        #Update the feature
        Cursor_gene_beta = AP.UpdateCursor(Scratch_diss_lyr, SQL_query_update)

        #Update only if near features were detected
        if len(ToBeCoted0)!=0 :
            AP.AddMessage("Number of symbol coded as 0 in the current iteration: " + str(len(ToBeCoted0)))

            for lines in Cursor_gene_beta:
                fid_in_list = (lines.getValue(FID_Field_diss) in ToBeCoted0)
                #When the current feature has been detected as a superposed symbol
                if fid_in_list == True:
                    lines.setValue(str(DissolvedPriorityFields[4]),0)
                #When id are not the same, cote 1 instead
                else:
                    lines.setValue(str(DissolvedPriorityFields[4]),1)
                Cursor_gene_beta.updateRow(lines)

            #Restart the while loop
            NeighboursM=True

            del lines, Cursor_gene_beta

    #---Double superposition generalization
    AP.AddMessage("Generalizing simple superposed symbols...")
    while NeighboursS==True:

        NeighboursS=False #Initialisation de la variable témoins

        #Apply a new near analysis on the dissolved feature
        AP.SelectLayerByAttribute_management(Scratch_diss_lyr, "NEW_SELECTION", str(DissolvedPriorityFields[4]) + " = 1")
        AP.Near_analysis(Scratch_diss_lyr, Scratch_diss_lyr, Length, NearLocation, NearAngle)
        AP.SelectLayerByAttribute_management(Scratch_diss_lyr, "CLEAR_SELECTION")

        #Create a search cursor
        SQL_query_search = SQL_query_update + " AND " + GeoScaler_functions.BuildComplexSQL(Scratch_diss_lyr,NearDistField,0, ">")
        Cursor_gene_gamma = AP.SearchCursor(Scratch_diss_lyr, SQL_query_search)

        #Create an empty list to stock superposed symbols
        UniqueList = [] #To find duplicate
        ToBeCoted0_dst = [] #To store duplicate distances
        ToBeCoted0_IDs = [] #To store duplicate ids

        for lines in Cursor_gene_gamma:
            if lines.getValue(NearDistField) not in UniqueList:
                UniqueList.append(lines.getValue(NearDistField))
            else:
                #Retrieve info about the nearest feature around the multiple superposed symbol
                nearest_id = lines.getValue(NearIDField)
                nearest_group_id = FC_Dissolve_dict[nearest_id][0]
                nearest_priority = FC_Dissolve_dict[nearest_id][1]
                nearest_chronology = FC_Dissolve_dict[nearest_id][2]
                nearest_mean_angle = FC_Dissolve_dict[nearest_id][3]
                nearest_angle = FC_Dissolve_dict[nearest_id][4]
                current_id = lines.getValue(FID_Field_diss)
                current_group_id = lines.getValue(DissolvedPriorityFields[1])
                current_priority = lines.getValue(DissolvedPriorityFields[0])
                current_chronology = lines.getValue(DissolvedPriorityFields[2])
                current_mean_angle = lines.getValue(DissolvedPriorityFields[3])
                current_angle = lines.getValue(DissolvedPriorityFields[4])

                #Call the custom function to compare symbols, see top of script
                Func_result = compare_symbols(ToBeCoted0, nearest_id, nearest_group_id, nearest_priority, nearest_chronology, \
                                              nearest_mean_angle, nearest_angle, current_id, current_group_id, current_priority, current_chronology, \
                                              current_mean_angle, current_angle, MinAngle)
                ToBeCoted0_IDs = Func_result[0]

                #Add warning if necessary
                if Func_result[1] != None:
                    AP.AddWarning(Func_result[1])

        #Prevent error in script, the cursor will return nothing if no symbol in detected by the query in the cursor
        if len(ToBeCoted0_IDs)!=0 :
            del lines, Cursor_gene_gamma

        #Update the feature
        Cursor_gene_delta = AP.UpdateCursor(Scratch_diss_lyr, SQL_query_update)

        #Mise à jour de la couche sans les doublons seulement s'il y en a.
        if len(ToBeCoted0_IDs)!=0 :
            AP.AddMessage("Number of symbol coded as 0 in the current iteration: " + str(len(ToBeCoted0_IDs)))
            for lines in Cursor_gene_delta:
                fid_in_list_simple = (lines.getValue(FID_Field_diss) in ToBeCoted0_IDs)

                #When id are the same, cote 0
                if fid_in_list_simple == True:
                    lines.setValue(str(DissolvedPriorityFields[4]),0)
                #When id are not the same, cote 1 instead
                else:
                    lines.setValue(str(DissolvedPriorityFields[4]),1)

                Cursor_gene_delta.updateRow(lines)

            NeighboursS=True
            del lines, Cursor_gene_delta

    #---Retrieve all info about generalized features and apply it to the original features.
    AP.AddMessage("Terminating generalization process...")

    Cursor_gene_epsilon = AP.SearchCursor(Scratch_diss_lyr)
    for lines in Cursor_gene_epsilon:
        #Retrieve group id for 0 coted features only
        if lines.getValue(DissolvedPriorityFields[4]) == 0:
            Dissolve_generalized.append(lines.getValue(DissolvedPriorityFields[1]))
    del lines, Cursor_gene_epsilon

    #Update the original feature
    Cursor_gene_zeta = AP.UpdateCursor(FeatureLayer)
    for lines in Cursor_gene_zeta:
        #For group ids stock in the last appended list
        if lines.getValue(PriorityFields[1]) in Dissolve_generalized:
            lines.setValue(FinalResultField, 0)
        Cursor_gene_zeta.updateRow(lines)
    del lines, Cursor_gene_zeta

    #---Delete the dissolved feature
    AP.Delete_management(Scratch_diss)

    #-------------------------------------------------------------------
    #Delete unwanted fields, only keeps the field with the results
    #-------------------------------------------------------------------
    PriorityFields.remove("GROUP_ID")
    PriorityFields.append(NearIDField)
    PriorityFields.append(NearDistField)
    AP.DeleteField_management(FeatureLayer, PriorityFields)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(FinalResultField)+".")

except ImportError:
     AP.AddError("No ArcInfo licence available, retry later.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))