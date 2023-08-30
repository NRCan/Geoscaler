# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2bSym.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will help generalizing bedrock based symbols such as plane and lineation.
# Original work: Gabriel H.V. (LCNP), 2008
# ---------------------------------------------------------------------------

#Import standard libs.
import sys, traceback, string, os
import arcpy as AP

#Import custom libs.
import GeoScaler_functions

def DissFieldName(DataType, FieldName):
    #Conditions in this function will help find the true field name
    #The field names will vary if it's from a shapefile or feature within a database.
    #Shapefiles have maximum length field names, instead features field names are not bound
    #to a maximum.
    if DataType == "ShapeFile":
        Prefix = "FIRST_"
        return Prefix + FieldName[:4] #Four caracter maximum after FIRST_
    else:
        Prefix = "FIRST_"
        return Prefix + FieldName

def ComplexGeneralization(InputFeatureLayer, SQL, NFD, ResultField, AzimuthField, AzimTolerance, \
                          DPField, DPTolerance, NEAR_DIST, NEAR_FID, IDField): #DP stands for Dip or plunge angles
    #Import standard libs.
    import sys, traceback, string, os
    import arcpy as AP

    try:
        #-------------------------------------------------------------------
        #Multiple superposition generalization
        #-------------------------------------------------------------------
        #Variables
        Neighbours = True
        OldDictionnary = {} #Will help end the generalization, or else it will loop infinitly
        Iterator = 1
        #Convert into integers, or else problem arises
        DPTolerance = int(DPTolerance)
        AzimTolerance = int(AzimTolerance)

        #Loop until there is no more neighbours
        while Neighbours==True:
            #Init
            Neighbours=False

            #Variables
            FirstNeighbour = {} #To list the first neighbours found
            MultipleNeighbours = {} #Dictionnary to contain symbols to be coted 0 #Example: {ID=1:[[P1,P2, Px],[A1,A2, Ax], ...], ...}

            #Perform a near analysis
            AP.SelectLayerByAttribute_management(InputFeatureLayer, "NEW_SELECTION",  SQL)
            AP.Near_analysis(InputFeatureLayer, InputFeatureLayer, str(NFD), "NO_LOCATION", "NO_ANGLE")

            #Create cursor with proper query to select neighbours (symbol with a diff. value of -1 id.)
            Cursor_M = AP.SearchCursor(InputFeatureLayer, str(ResultField) + " = 1 AND NEAR_FID <> - 1")
            for ligne_M in Cursor_M:

                #Filter duplicate values
                if ligne_M.getValue(NEAR_FID) not in FirstNeighbour:
                    #Keep the original ID from first neighbours as dict. key and angles as values
                    FirstNeighbour[ligne_M.getValue(NEAR_FID)]=[[ligne_M.getValue(DPField)],\
                                                                [ligne_M.getValue(AzimuthField)]]
                else:
                    #Condition to first multiple neighbours, needs different command line to add info.
                    if ligne_M.getValue(NEAR_FID) in MultipleNeighbours:
                        #Append info
                        MultipleNeighbours[ligne_M.getValue(NEAR_FID)][0].append(ligne_M.getValue(DPField))
                        MultipleNeighbours[ligne_M.getValue(NEAR_FID)][1].append(ligne_M.getValue(AzimuthField))

                    else:
                        #Init. info addition
                        MultipleNeighbours[ligne_M.getValue(NEAR_FID)] = [[ligne_M.getValue(DPField)],\
                                                                          [ligne_M.getValue(AzimuthField)]]

                        #Add the first neighbours to dictionnary, or else later angle analysis will be biased
                        MultipleNeighbours[ligne_M.getValue(NEAR_FID)][0].append(FirstNeighbour[ligne_M.getValue(NEAR_FID)][0][0])
                        MultipleNeighbours[ligne_M.getValue(NEAR_FID)][1].append(FirstNeighbour[ligne_M.getValue(NEAR_FID)][1][0])

            #In case multiple neighbours are detected and the dictionnary is not similar to the previous iteration
            if len(MultipleNeighbours)!=0 and OldDictionnary != MultipleNeighbours:

                #Update cursor to cote symbols
                Cursor_M2 = AP.UpdateCursor(InputFeatureLayer, SQL)
                for ligne_M2 in Cursor_M2:

                    #If current iterated symbols is in the dictionnary
                    fid_in_liste = (ligne_M2.getValue(IDField) in MultipleNeighbours)
                    if fid_in_liste == True:

                        #For users that wants both condition--------------------------------------------
                        if DPTolerance != 0 and AzimTolerance !=0:

                            #Variables
                            Diff_dp = 0
                            Diff_azim = 0

                            #Analyse the plunge angle
                            for dpAngles in MultipleNeighbours[ligne_M2.getValue(IDField)][0]:
                                #Calculate the difference between the angles
                                Diff_dp = abs(Diff_dp-dpAngles)

                            #Analyse the azimuthal angle
                            for azimAngles in MultipleNeighbours[ligne_M2.getValue(IDField)][1]:
                                #Calculate the difference between the angles
                                Diff_azim = abs(Diff_azim-azimAngles)

                            #Conditions to cote 0 or 1, based on user plunge and azimuthal tolerance
                            if int(abs(ligne_M2.getValue(DPField) - Diff_dp)) <= int(DPTolerance):
                                if int(abs(ligne_M2.getValue(AzimuthField) - Diff_azim)) <= int(AzimTolerance):
                                    ligne_M2.setValue(str(ResultField),0)
                                else:
                                    ligne_M2.setValue(str(ResultField),0)
                            else:
                                if int(abs(ligne_M2.getValue(AzimuthField) - Diff_azim)) <= int(AzimTolerance):
                                    ligne_M2.setValue(str(ResultField),0)
                                else:
                                    ligne_M2.setValue(str(ResultField),1)

                            if Diff_dp == 0:
                                ligne_M2.setValue(str(ResultField),0)

                            if Iterator == len(MultipleNeighbours[ligne_M2.getValue(IDField)][0]):
                                ligne_M2.setValue(str(ResultField),1)

                        #For users that wants Dip plunge tolerance only --------------------------------------------
                        elif DPTolerance != 0 and AzimTolerance ==0:

                            #Variables
                            Diff_dp = 0

                            #Analyse the plunge angle
                            for dpAngles in MultipleNeighbours[ligne_M2.getValue(IDField)][0]:
                                #Calculate the difference between the angles
                                Diff_dp = abs(Diff_dp-dpAngles)

                            #Conditions to cote 0 or 1, based on user plunge and azimuthal tolerance
                            if int(abs(ligne_M2.getValue(DPField) - Diff_dp)) <= int(DPTolerance):
                                ligne_M2.setValue(str(ResultField),0)
                            else:
                                ligne_M2.setValue(str(ResultField),1)

                            if Iterator == len(MultipleNeighbours[ligne_M2.getValue(IDField)][0]):
                                ligne_M2.setValue(str(ResultField),1)

                            if Diff_dp == 0:
                                ligne_M2.setValue(str(ResultField),0)

                        #For users that wants azimuthal tolerance only --------------------------------------------
                        elif DPTolerance == 0 and AzimTolerance !=0:
                            #Variables
                            Diff_azim = 0

                            #Analyse the azimuthal angle
                            for azimAngles in MultipleNeighbours[ligne_M2.getValue(IDField)][1]:
                                #Calculate the difference between the angles
                                Diff_azim = abs(Diff_azim-azimAngles)

                            #Conditions to cote 0 or 1, based on user plunge and azimuthal tolerance
                            if int(abs(ligne_M2.getValue(AzimuthField) - Diff_azim)) <= int(AzimTolerance):
                                ligne_M2.setValue(str(ResultField),0)
                            else:
                                ligne_M2.setValue(str(ResultField),1)

                            if Iterator == len(MultipleNeighbours[ligne_M2.getValue(IDField)][0]):
                                ligne_M2.setValue(str(ResultField),1)

                        #For users that wants no conditions --------------------------------------------
                        elif DPTolerance == 0 and AzimTolerance ==0:
                            ligne_M2.setValue(str(ResultField),0)

                    #If the object is not in the list
                    else:

                        ligne_M2.setValue(str(ResultField),1)

                    #Update
                    Cursor_M2.updateRow(ligne_M2)

                #Re-init the old dictionnary to detect infinit loops
                OldDictionnary = MultipleNeighbours

                Iterator = Iterator + 1

                #Re-init while loop
                Neighbours=True

        #-------------------------------------------------------------------
        #Simple superposition generalization
        #-------------------------------------------------------------------
        #Re-init variables
        Neighbours = True
        OldDictionnary = {} #Will help end the generalization, or else it will loop infinitly
        Iterator = 1

        #Loop until there is no more neighbours
        while Neighbours==True:
            #Init
            Neighbours=False

            #Variables
            DoubleNeighbours = {} #Dictionnary to contain symbols to be coted 0 #Example: {ID=1:[[P1,P2, Px],[A1,A2, Ax], ...], ...}

            #Perform a near analysis
            AP.SelectLayerByAttribute_management(InputFeatureLayer, "NEW_SELECTION",  SQL)
            AP.Near_analysis(InputFeatureLayer, InputFeatureLayer, str(NFD), "NO_LOCATION", "NO_ANGLE")

            #Create cursor with proper query to select neighbours (symbol with a diff. value of 0m.)
            Cursor_D = AP.SearchCursor(InputFeatureLayer, str(ResultField) + " = 1 AND NEAR_DIST > 0")
            for ligne_D in Cursor_D:

                #Filter duplicate values
                if ligne_D.getValue(NEAR_DIST) not in DoubleNeighbours:
                    #Keep the original distance as dict. key and angles as values
                    DoubleNeighbours[ligne_D.getValue(NEAR_DIST)] = [[ligne_D.getValue(PlungeField)],\
                                                                     [ligne_D.getValue(AzimuthField)]]
                else:
                    #Append info
                    DoubleNeighbours[ligne_D.getValue(NEAR_DIST)][0].append(ligne_D.getValue(PlungeField))
                    DoubleNeighbours[ligne_D.getValue(NEAR_DIST)][1].append(ligne_D.getValue(AzimuthField))

            #In case simple neighbours are detected and the dictionnary is not similar to the previous iteration
            if len(DoubleNeighbours)!=0 and OldDictionnary != DoubleNeighbours:
                #Update cursor to cote symbols
                Cursor_D2 = AP.UpdateCursor(InputFeatureLayer, SQL)
                for ligne_D2 in Cursor_D2:

                    #If current iterated symbols is in the dictionnary
                    dist_in_list = (ligne_D2.getValue(NEAR_DIST) in DoubleNeighbours)
                    if dist_in_list == True:
                        #For users that wants both condition--------------------------------------------
                        if DPTolerance != 0 and AzimTolerance !=0:
                            #Variables
                            Diff_dp = 0
                            Diff_azim = 0

                            #Analyse the dip angle
                            for dpAngles in DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0]:
                                #Calculate the difference between the angles
                                Diff_dp = abs(Diff_dp-dpAngles)

                            #Analyse the azimuthal angle
                            for azimAngles in DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][1]:
                                #Calculate the difference between the angles
                                Diff_azim = abs(Diff_azim-azimAngles)

                            #Conditions to cote 0 or 1, based on user dip and azimuthal tolerance
                            if int(Diff_dp) <= int(DPTolerance):# and ligne_D2.getValue(DPField)!= DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0][-1]:
                                ligne_D2.setValue(str(ResultField),0)

                            elif int(Diff_dp) > int(DPTolerance):# and ligne_D2.getValue(DPField)!= DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0][-1]:

                                if int(Diff_azim) <= int(AzimTolerance):
                                    ligne_D2.setValue(str(ResultField),0)
                                else:
                                    ligne_D2.setValue(str(ResultField),1)

    ##                        #Conditions to cote 0 or 1, based on user dip and azimuthal tolerance
    ##                        if int(abs(ligne_D2.getValue(DPField) - Diff_dp)) <= int(DPTolerance):# and ligne_D2.getValue(DPField)!= DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0][-1]:
    ##
    ##                            ligne_D2.setValue(str(ResultField),0)
    ##
    ##                        elif int(abs(ligne_D2.getValue(DPField) - Diff_dp)) > int(DPTolerance):# and ligne_D2.getValue(DPField)!= DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0][-1]:
    ##
    ##                            if int(abs(ligne_D2.getValue(AzimuthField) - Diff_azim)) <= int(AzimTolerance):
    ##                                ligne_D2.setValue(str(ResultField),0)
    ##                            else:
    ##                                ligne_D2.setValue(str(ResultField),1)

                            if Diff_dp == 0:
                                ligne_D2.setValue(str(ResultField),0)

                            if Iterator == len(DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0]):
                                ligne_D2.setValue(str(ResultField),1)



                        #For users that wants Dip plunge tolerance only --------------------------------------------
                        elif DPTolerance != 0 and AzimTolerance ==0:

                            Diff_dp = 0

                            #Analyse the dip angle
                            for dpAngles in DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0]:
                                #Calculate the difference between the angles
                                Diff_dp = abs(Diff_dp-dpAngles)

                            #Conditions to cote 0 or 1, based on user dip and azimuthal tolerance
                            if int(Diff_dp) <= int(DPTolerance):# and ligne_D2.getValue(DPField)!= DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][0][-1]:
                                ligne_D2.setValue(str(ResultField),0)

                            else:
                                ligne_D2.setValue(str(ResultField),1)

                            if Diff_dp == 0:
                                ligne_D2.setValue(str(ResultField),0)

                        #For users that wants azimuthal tolerance only --------------------------------------------
                        elif DPTolerance == 0 and AzimTolerance != 0:
                            #Variables
                            Diff_azim = 0

                            #Analyse the azimuthal angle
                            for azimAngles in DoubleNeighbours[ligne_D2.getValue(NEAR_DIST)][1]:
                                #Calculate the difference between the angles
                                Diff_azim = abs(Diff_azim-azimAngles)

                            if int(Diff_azim) <= int(AzimTolerance):
                                ligne_D2.setValue(str(ResultField),0)
                            else:
                                ligne_D2.setValue(str(ResultField),1)
                        #For users that wants no conditions --------------------------------------------
                        elif DPTolerance == 0 and AzimTolerance ==0:
                            ligne_D2.setValue(str(ResultField),0)

                    #If the object is not in the list
                    else:
                        ligne_D2.setValue(str(ResultField),1)

                    #Update
                    Cursor_D2.updateRow(ligne_D2)

                #Re-init the old dictionnary to detect infinit loops
                OldDictionnary = DoubleNeighbours

                Iterator = Iterator + 1

                #Re-init while loop
                Neighbours=True
    except:
        AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

#Error handling classes
class CustomError(Exception): pass #Mother class
class EnvironmentError(CustomError):pass #Child class

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
    ScriptName = os.path.basename(sys.argv[0]).split("#")[-1].split("_")[0] #The name of the current script. ex: GeoscalerTools10.tbx#M2aSymPol01_GeoScalerTools.py
    InputFeature = sys.argv[1]  #Feature to generalize
    SymbolField = sys.argv[2] #The field that contains the symbol classes
    PlanarValue = sys.argv[3] #The field value for planar symbols
    LinearValue = sys.argv[4] #The field value for linear symbols
    DipField = sys.argv[5] #The field containing all the dip angles for planar symbols
    PlungeField = sys.argv[6] #The field containing all the plunge angles for linear symbols
    AzimuthField = sys.argv[7] #The field containing all the azimuthal anngles for the symbols
    NFD = sys.argv[8] #The near feature distance between symbols
    AzimTolerance = sys.argv[9] #The azimuthal tolerance between symbols
    DipTolerance = sys.argv[10] #The dip tolerance between planar symbols, e.g. 10 degrees
    PlungeTolerance = sys.argv[11] #The plunge toleranc between linear symbols, e.g. 10 degrees.
    FlagErrorBool = sys.argv[12] #If the user wants or not to flag azimuthal errors
    AllStepsBool = sys.argv[13] #If the user wants to perform script on all steps
    SpecificSteps = sys.argv[14] #If the user wants to perform script on specified steps only
    #AP.AddWarning(AllStepsBool + " " + FlagErrorBool +  "  " + SpecificSteps)
    #Field variables
    AnalysisFields = ["DUP_ID", "GROUP_ID", "GROUP_FLAG"]

    #Other variables
    StepsName = ["Groups", "Linear", "Planar"]
    Buffer = 15 #Min. width of buffer in meters, used to detect group of symbols.
    Prefix = "BEDSYM" #Prefix for temps features or tables
    NearLocation = "NO_LOCATION"
    NearAngle = "NO_ANGLE"
    NEAR_FID = "NEAR_FID" #Found in the input feature and generated near table
    NEAR_DIST = "NEAR_DIST"
    IN_FID = "IN_FID" #Found in the generated near table
    PlanarLayer = "PlanarLayer"
    LinearLayer = "LinearLayer"
    Sym_pair = {} #Dictionnary that will contains, first only groups of two symbols than all groups
    Sym_group = {} #Dictionnary that will contains only groups of 3 and more symbols
    Near_liste = [] #A list that will contain all of the NEAR_FID info
    FlagDict = {} #A dictionnary that will contains all the groups numbers with value equal to azimuths , dip and plunge angles from the symbols within group
    FlagList = [] #A list of all the real group of symbols that are problems
    AzimDict= {} #A dictionnary to contains the azimuth angle of each symbol within groups
    DipPlungeDict = {} #A dictionnary to contains the dip and plunge angles from symbols within groups
    FlagWord = "ERROR" #The word written in the field that will contain flags from incoherent azimuth angles
    Dissolve_stat_type = "FIRST" #Type of dissolve applied to fields
    NearList = [] #A list of near features to cote 0
    NearLayer = "NearLayer"
    InputFeatureLayer = "InputFeatureLayer"
    LinearLayer_beta = "LinearLayer_beta"

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
    #Manage field to contains analysis fields
    #-------------------------------------------------------------------
    #Describe the feature
    Desc = AP.Describe(InputFeature)
    Fields = Desc.Fields
    Feature_ID_Field = Desc.OIDFieldName #The identification field
    FieldNames = []

    #List all field names
    for field_rows in Fields:
        FieldNames.append(field_rows.Name)

    #Iterate through priority fields, if they don't exists add them
    for fields in AnalysisFields:
        if fields not in FieldNames:
            if fields == AnalysisFields[2]:
                AP.AddField_management(InputFeature, fields, "TEXT", "#", "#", "5")
            else:
                AP.AddField_management(InputFeature, fields, "LONG")

    #-------------------------------------------------------------------
    #Prepare data
    #-------------------------------------------------------------------
    #Adding a duplicate id to the feature
    FieldDelimiters = AP.AddFieldDelimiters(InputFeature, Feature_ID_Field)
    AP.CalculateField_management(InputFeature, AnalysisFields[0], "[" + Feature_ID_Field + "]")

    #Restart group numbers to 0
    AP.CalculateField_management(InputFeature, AnalysisFields[1], 0)

    #Create feature layer
    AP.MakeFeatureLayer_management(InputFeature, PlanarLayer)
    AP.MakeFeatureLayer_management(InputFeature, LinearLayer)
    AP.MakeFeatureLayer_management(InputFeature, InputFeatureLayer)

    #Query to select planar and linear symbols
    SQL_Planar = GeoScaler_functions.BuildSQL(InputFeature,SymbolField,PlanarValue)
    SQL_Linear = GeoScaler_functions.BuildSQL(InputFeature,SymbolField,LinearValue)

    #Select the classes within the features
    AP.SelectLayerByAttribute_management(PlanarLayer, "NEW_SELECTION", SQL_Planar)
    AP.SelectLayerByAttribute_management(LinearLayer, "NEW_SELECTION", SQL_Linear)

    #Calculate resulting field to 1 for planar and linear symbols
    #If the user wants to use all step option
    if AllStepsBool == "true":
        AP.CalculateField_management(PlanarLayer, ResultField, 1)
        AP.CalculateField_management(LinearLayer, ResultField, 1)

    #-------------------------------------------------------------------
    #Find symbol grouping
    #-------------------------------------------------------------------
    AP.AddMessage("*****Finding and assigning id to groups of planar and linear symbols...")

    #Perform a select layer by location with an intersection to detect groups
    AP.SelectLayerByLocation_management(PlanarLayer, "INTERSECT", LinearLayer, Buffer, "SUBSET_SELECTION")
    #AP.SelectLayerByLocation_management(LinearLayer, "INTERSECT", PlanarLayer, Buffer, "SUBSET_SELECTION")

    #Create a temp name for near table
    Scratch_table = AP.CreateScratchName(Prefix, "T", "ArcInfoTable", Script_path)

    #Create a Near table
    AP.GenerateNearTable_analysis(PlanarLayer, LinearLayer, Scratch_table, Buffer, NearLocation, NearAngle, "ALL")

    if str(AP.GetCount_management(Scratch_table)) != "0":
        #Iterate through near table to find grouping of 2 symbols
        Cursor_alpha = AP.SearchCursor(Scratch_table)

        for lines in Cursor_alpha:
            Near_liste.append(lines.getValue(NEAR_FID))
            Sym_pair[lines.getValue(IN_FID)] = [lines.getValue(NEAR_FID)]

            if lines.getValue(IN_FID) in Near_liste:
                if lines.getValue(NEAR_FID) in Sym_pair:
                    del Sym_pair[lines.getValue(IN_FID)]
        del lines, Cursor_alpha

        #Iterate through feature and update the group number
        for each_symbols in Sym_pair:
            #Query beginning
            Sym_string = FieldDelimiters + " = " + str(each_symbols)
            #Build the rest of the query
            for items in Sym_pair[each_symbols]:
                Sym_string = Sym_string + " OR " + FieldDelimiters + " = " + str(items)

            #Update group id
            Cursor_beta = AP.UpdateCursor(InputFeature, Sym_string)
            for group in Cursor_beta:
                group.setValue(AnalysisFields[1], each_symbols)
                Cursor_beta.updateRow(group)
            del group, Cursor_beta
    else:
        AP.AddWarning("   No groups of planar and linear symbols were detected...")

    AP.Delete_management(Scratch_table)

    #-------------------------------------------------------------------
    # Flag incoherent lineation and planar symbol groups
    # *Azimuthal angle too high or incoherent plunge angles
    #-------------------------------------------------------------------
    if FlagErrorBool == "true":
        AP.AddMessage("*****Flagging incoherent lineation and planar groups ...")

        #Iterate trhough feature and fill in a dictionnary of information from table
        Cursor_flag = AP.SearchCursor(InputFeature)
        for row_flag in Cursor_flag:
            #For groups only
            if row_flag.getValue(AnalysisFields[1]) != 0:
                if row_flag.getValue(AnalysisFields[1]) not in FlagDict:
                    #Add the group number as a key within dictionnary
                    FlagDict[row_flag.getValue(AnalysisFields[1])]= {}
                #Get the azimuth angles
                if row_flag.getValue(SymbolField) == PlanarValue:
                    FlagDict[row_flag.getValue(AnalysisFields[1])]["AzimPlane"] = row_flag.getValue(AzimuthField)
                elif row_flag.getValue(SymbolField) == LinearValue:
                    FlagDict[row_flag.getValue(AnalysisFields[1])]["AzimLineation"] = row_flag.getValue(AzimuthField)

        #Iterate through flag dictionnary to analyse the angles from groups
        for values in FlagDict:
            #Variables
            AzimPlane = FlagDict[values]["AzimPlane"]
            AzimLineation = FlagDict[values]["AzimLineation"]

            if AzimPlane > 180:
                #The group is correct
                if AzimLineation >= AzimPlane and AzimLineation < 360:
                    pass
                #The group is correct
                elif AzimLineation >= 0 and AzimLineation <= (-180 + AzimPlane):
                    pass
                #The group have a problem
                else:
                    FlagList.append(values)
            elif AzimPlane <= 180:
                #The group is correct
                if AzimLineation >= AzimPlane and AzimLineation < (AzimPlane + 180):
                    pass
                #The group have a problem
                else:
                    FlagList.append(values)

        #Update the feature if problem were detected
        if len(FlagList) != 0:
            FlagCursor = AP.UpdateCursor(InputFeature)
            for flag_rows in FlagCursor:
                if flag_rows.getValue(AnalysisFields[1]) in FlagList:
                    flag_rows.setValue(AnalysisFields[2], FlagWord)
                FlagCursor.updateRow(flag_rows)
            del flag_rows, FlagCursor

    #-------------------------------------------------------------------
    # Detect superposed groups symbols between each others
    # Between each other, they are the same priority, the following code
    # will use near analysis to generalize
    #-------------------------------------------------------------------
    if AllStepsBool == "true" or StepsName[0] in SpecificSteps:
        AP.AddMessage("*****Detecting overlaps between group of planar and linear symbols ...")

        #Create a new point feature out of the groups symbols, the output will be a unique point by groups
        Scratch_group = AP.CreateScratchName(Prefix, "", "FeatureClass", Script_path)

        #Dissolving groups of symbols into unique entities
        FieldsToDissolve = [[DipField, Dissolve_stat_type], [PlungeField,Dissolve_stat_type], \
                            [AzimuthField,Dissolve_stat_type], [AnalysisFields[1], Dissolve_stat_type], \
                            [ResultField, Dissolve_stat_type]]

        AP.Dissolve_management(InputFeature,Scratch_group, AnalysisFields[1], FieldsToDissolve, "MULTI_PART")

        #Describe the new dissolved feature
        Desc = AP.Describe(Scratch_group)
        Temp_ID_Field = Desc.OIDFieldName #The identification field
        DataType = Desc.DataType

        #Delete the group 0
        AP.MakeFeatureLayer_management(Scratch_group, NearLayer)
        SQL_Group0 = GeoScaler_functions.BuildSQL(Scratch_group,AnalysisFields[1],0)
        AP.SelectLayerByAttribute_management(NearLayer, "NEW_SELECTION", SQL_Group0)
        AP.DeleteRows_management(NearLayer)
        #-------------------------------------------------------------------
        #Multiple superposition generalization

        #Calculate all values as 1, to start.
        RF = DissFieldName(DataType, ResultField)
        GID = DissFieldName(DataType, AnalysisFields[1])
        AP.CalculateField_management(NearLayer, RF, 1)

        #Loop until there is no more neighbours
        Neighbours = True
        while Neighbours==True:
            Neighbours=False

            #Select only 1 coted symbols, so there are the only one passed to the near analysis
            AP.SelectLayerByAttribute_management(NearLayer, "NEW_SELECTION", str(RF) + " = 1")

            #Perform a near analysis
            AP.Near_analysis(NearLayer, NearLayer, str(NFD), "NO_LOCATION", "NO_ANGLE")

            #Create cursor with proper query to select neighbours (symbol with a diff. value of -1 id.)
            Cursor_M = AP.SearchCursor(NearLayer, str(RF) + " = 1 AND NEAR_FID <> - 1")

            #Variables
            uniqueList = []
            liste_mult_elim = [] #List that will contain all symbols to be coted 0

            for ligne_M in Cursor_M:
                #Find duplicate values within list
                if ligne_M.getValue(NEAR_FID) not in uniqueList:
                    uniqueList.append(ligne_M.getValue(NEAR_FID))
                else:
                    liste_mult_elim.append(ligne_M.getValue(NEAR_FID))

            #If there is multiple neighbours
            if len(liste_mult_elim)!=0 :

                #-------------------------------------------------------------------
                #Cursor to update the input feature with generalized informations
                Cursor_M2 = AP.UpdateCursor(NearLayer, str(RF) + " = 1")
                for ligne_M2 in Cursor_M2:
                    fid_in_liste = ligne_M2.getValue(Temp_ID_Field) in liste_mult_elim

                    #If the object is in the list
                    if fid_in_liste == True:
                        ligne_M2.setValue(str(RF),0)

                    #If the object is not in the list
                    else:
                        ligne_M2.setValue(str(RF),1)

                    #Update
                    Cursor_M2.updateRow(ligne_M2)
                Neighbours=True

        #-------------------------------------------------------------------
        #Double superposition generalization
        Neighbours_D = True
        while Neighbours_D==True:

            Neighbours_D=False

            #Select only 1 coted symbols, so there are the only one passed to the near analysis
            AP.SelectLayerByAttribute_management(NearLayer, "NEW_SELECTION", str(RF) + " = 1")

            #Perform a near analysis
            AP.Near_analysis(NearLayer, NearLayer, str(NFD), "NO_LOCATION", "NO_ANGLE")

            #Create cursor with proper query to select neighbours (symbol with a diff. value of 0m.)
            Cursor_D = AP.SearchCursor(NearLayer, str(RF) + " = 1 AND NEAR_DIST > 0")

            #Variables
            uniqueList_D = []
            liste_doublons_elim = [] #List that will contain all symbols to be coted 0
            liste_ID_doublons_elim = [] #List that will contain all symbols ids to be coted 0

            for ligne_D in Cursor_D:
                #Find duplicate values within list
                if ligne_D.getValue(NEAR_DIST) not in uniqueList_D:
                    uniqueList_D.append(ligne_D.getValue(NEAR_DIST))
                else:
                    liste_doublons_elim.append(ligne_D.getValue(NEAR_DIST))
                    liste_ID_doublons_elim.append(ligne_D.getValue(NEAR_FID))

            #-------------------------------------------------------------------
            #Cursor to update the input feature with generalized informations
            Cursor_D2 = AP.UpdateCursor(NearLayer,str(RF) + " = 1")

            #If there is a neighbour
            if len(liste_ID_doublons_elim)!=0 :
                for ligne_D2 in Cursor_D2:
                    fid_in_liste = (ligne_D2.getValue(Temp_ID_Field) in liste_ID_doublons_elim)

                    #If the object is in the list
                    if fid_in_liste == True:
                        ligne_D2.setValue(str(RF),0)

                    #If the object is not in the list
                    else:
                        ligne_D2.setValue(str(RF),1)
                    #Update
                    Cursor_D2.updateRow(ligne_D2)
                Neighbours_D=True

        #List all the groups to cote 0 from Scratch_group feature
        GroupCursor = AP.SearchCursor(Scratch_group)
        for groups in GroupCursor:
            if groups.getValue(RF) == 0:
                NearList.append(groups.getValue(GID))
        #del groups, GroupCursor

        #Update the input feature with proper information from generalization
        UpGroupCur = AP.UpdateCursor(InputFeature)
        for upgroup in UpGroupCur:
            if upgroup.getValue(AnalysisFields[1]) in NearList and upgroup.getValue(AnalysisFields[1]) != 0 :
                upgroup.setValue(ResultField, 0)
            UpGroupCur.updateRow(upgroup)
        #del upgroup, UpGroupCur

    #-------------------------------------------------------------------
    # Detect superposed groups of symbols with single symbols
    #-------------------------------------------------------------------
    if AllStepsBool == "true" or StepsName[0] in SpecificSteps:
        AP.AddMessage("*****Detecting overlaps between groups symbols and not grouped symbols...")

        #Select all planar and linear symbols that are not within groups
        AP.SelectLayerByAttribute_management(InputFeatureLayer, "NEW_SELECTION", SQL_Planar)
        AP.SelectLayerByAttribute_management(InputFeatureLayer, "ADD_TO_SELECTION", SQL_Linear)
        SQL_NoGroups = GeoScaler_functions.BuildSQL(InputFeature,AnalysisFields[1],0)
        AP.SelectLayerByAttribute_management(InputFeatureLayer, "SUBSET_SELECTION", SQL_NoGroups)

        #Select with a buffer all symbols around groups
        AP.SelectLayerByAttribute_management(NearLayer, "CLEAR_SELECTION")
        AP.SelectLayerByLocation_management(InputFeatureLayer, "INTERSECT", NearLayer, NFD, "SUBSET_SELECTION")

        #Calculate to 0 within resulting field, the last selection
        AP.CalculateField_management(InputFeatureLayer, ResultField, 0)

        #Delete temp feature
        AP.Delete_management(Scratch_group)

    #-------------------------------------------------------------------
    # Detect superposed linear symbols with linear symbols
    #-------------------------------------------------------------------
    if AllStepsBool == "true" or StepsName[1] in SpecificSteps:

        AP.AddMessage("*****Detecting overlaps between linear symbols with linear symbols ...")

        #Prepare data
        SQL_Multiple = GeoScaler_functions.BuildSQL(InputFeature,ResultField,1) + " AND " + \
                       GeoScaler_functions.BuildSQL(InputFeature,SymbolField,LinearValue) + " AND " + \
                       GeoScaler_functions.BuildSQL(InputFeature,AnalysisFields[1],0)

        #Call the above custom function to generalize
        ComplexGeneralization(InputFeatureLayer, SQL_Multiple, NFD, ResultField, AzimuthField, AzimTolerance, \
                              PlungeField, PlungeTolerance, NEAR_DIST, NEAR_FID, Feature_ID_Field)

    #-------------------------------------------------------------------
    # Detect superposed linear symbols with planar symbols
    #-------------------------------------------------------------------
    if AllStepsBool == "true" or StepsName[1] in SpecificSteps:

        AP.AddMessage("*****Detecting overlaps between linear symbols with planar symbols ...")

        #Select the classes within the features
        AP.SelectLayerByAttribute_management(PlanarLayer, "NEW_SELECTION", SQL_Planar)
        AP.SelectLayerByAttribute_management(LinearLayer, "NEW_SELECTION", SQL_Linear)

        #Select all planar and linear symbols that are not within groups
        SQL_NoGroups = GeoScaler_functions.BuildSQL(InputFeature,AnalysisFields[1],0)
        AP.SelectLayerByAttribute_management(PlanarLayer, "SUBSET_SELECTION", SQL_NoGroups)
        AP.SelectLayerByAttribute_management(LinearLayer, "SUBSET_SELECTION", SQL_NoGroups)

        #Select all linear symbols that are still coted 1
        SQL_No1 = GeoScaler_functions.BuildSQL(InputFeature,ResultField,1)
        AP.SelectLayerByAttribute_management(LinearLayer, "SUBSET_SELECTION", SQL_No1)

        #Select with a buffer all symbols around linear symbols
        AP.SelectLayerByLocation_management(PlanarLayer, "INTERSECT", LinearLayer, NFD, "SUBSET_SELECTION")

        #Calculate to 0 within resulting field, the last selection
        AP.CalculateField_management(PlanarLayer, ResultField, 0)

    #-------------------------------------------------------------------
    # Detect superposed planar symbols with planar symbols
    #-------------------------------------------------------------------
    if AllStepsBool == "true" or StepsName[2] in SpecificSteps:

        AP.AddMessage("*****Detecting overlaps between planar symbols with planar symbols ...")

        #Prepare data
        SQL_Multiple = GeoScaler_functions.BuildSQL(InputFeature,ResultField,1) + " AND " + \
                       GeoScaler_functions.BuildSQL(InputFeature,SymbolField,PlanarValue) + " AND " + \
                       GeoScaler_functions.BuildSQL(InputFeature,AnalysisFields[1],0)

        #Call the above custom function to generalize
        ComplexGeneralization(InputFeatureLayer, SQL_Multiple, NFD, ResultField, AzimuthField, AzimTolerance, \
                              DipField, DipTolerance, NEAR_DIST, NEAR_FID, Feature_ID_Field)

    #-------------------------------------------------------------------
    #Delete unwanted fields
    #-------------------------------------------------------------------
    #Remove from list wanted list
    AnalysisFields.remove(AnalysisFields[0])
    AnalysisFields.remove(AnalysisFields[1])
    AnalysisFields.append(NEAR_FID)
    AnalysisFields.append(NEAR_DIST)
    AP.DeleteField_management(InputFeature, AnalysisFields)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in field: " + str(ResultField)+".")

except EnvironmentError:
     AP.AddError("No ArcInfo licence available, retry later.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))