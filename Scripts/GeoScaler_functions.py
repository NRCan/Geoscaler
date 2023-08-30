# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# Ganfeld_functions.py
# Gabriel Huot-Vézina (LCNP), 2010
# ---------------------------------------------------------------------------

def FieldDictionnary(ScriptName):
	#-----------------------------------------------------
	#This function will help create a resulting field name.
	#Preventing modification in each model validation script.
	#Modification will only occur here.
	#-----------------------------------------------------
	import arcpy as AP

	try:
		#{Script name: [Field prefix, hierarchy]}
		Model_dictionnary = {"M2aSymPol01":["A01_",1,"Poly"], \
							 "M_2aSymPol_02":["A02_",0,"Poly"], \
							 "M_2aSymPnt_01":["B01_",0,"Point"], \
							 "M_2aSymPnt_02":["B02_",0,"Point"], \
							 "M_2aSymPnt_03":["B03_",0,"Point"], \
							 "M_2aSymPnt_04":["B04_",3,"Point"], \
							 "M_2aSymLine_01":["D01_",0,"polyline"], \
							 "M_2aSymLine_02":["D02_",0,"polyline"], \
							 "M_2aSymLine_03":["D03_",0,"polyline"], \
							 "M_2aSymLine_04":["D04_",0,"polyline"], \
							 "M_2aSymLine_06":["D06_",2,"polyline"], \
							 "M_2aSymLinePnt":["E01_",2,"Point"], \
							 "M_2aSymPost_01":["G01_",1,"Point/polyline"], \
							 "M_2bSym":["H01_",1,"Point"]}

		#Verify secret entry
		if ScriptName == "Dictionnary":
			return Model_dictionnary
		else:
			#Return the correct field name
			return Model_dictionnary[ScriptName][0]

	except:
		AP.AddError("Script name is not a valid name within FieldDictionnary() function.")

def ResultFieldDictionnary(Field):
	#-----------------------------------------------------
	#This function will help create a resulting field name.
	#Preventing modification in each model validation script.
	#Modification will only occur here.
	#-----------------------------------------------------
	import arcpy as AP

	try:
		Model_dictionnary = {"From":"SCALE_FROM", \
							 "To":"SCALE_TO"}

		#Return the correct field name
		return Model_dictionnary[Field]

	except:
		AP.AddError("Field name is not a valid name within ResultFieldDictionnary() function.")

def VerifyResultingField(feature, field):
	#-----------------------------------------------------
	#This custom function will help verify the existence
	#of the field containing results within the feature, if
	#the field doesn't exist, create it
	#-----------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	#Verify the existence
	fields = AP.ListFields(feature)
	if field not in fields:
		#Add the field
		AP.AddField_management(feature, field, "LONG")

	return

def BuildResultingField(Field):
	#-----------------------------------------------------
	#This custom function will add the scale within the
	#name of a resulting field, e.g. A01_, would become
	#A01_50k.
	#-----------------------------------------------------
	#Import stand. lib.
	import os, sys, traceback
	from xml.etree import ElementTree
	import arcpy as AP

	#Error handling classes
	class CustomError(Exception): pass #Mother class
	class EnvironmentError(CustomError):pass #Child class

	try:
		#Variables
		XML_name = "GeoScaler_CustomSettings.xml"
		ScaleNode = "Target_Scale"

		#Load current script path
		XML_path = os.path.realpath(os.path.dirname(sys.argv[0])) + "\\" + XML_name

		#Verify if the xml file exists
		if os.path.isfile(XML_path) == False:
			raise EnvironmentError

		#Parse the file
		tree = ElementTree.parse(XML_path)

		#Retreive the desire node within a list variable
		Node = tree.getiterator(ScaleNode)
		Scale = Node[0].text

		#Create the field name
		Light_scale = int(Scale)/1000
		if Light_scale < 10000:
		  ResultField = Field + str(Light_scale) + "k"

		return  ResultField

	except EnvironmentError:
		AP.AddError("Found no initialization XML. Initialize GeoScaler and restart script.")
	except:
		AP.AddError("ERROR line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def BuildComplexSQL(Feature, Field, Value, Symbol):
	#-----------------------------------------------------
	#This custom function will build a proper SQL query, by
	#managing, type of feature (mdb, gdb, shapefile) and type
	#of data (numerical or alpha).
	#-----------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	#Error handling classes
	class CustomError(Exception): pass #Mother class
	class TypeError(CustomError):pass #Child class

	try:

		#List of numerical field type
		TypeList = ["SmallInteger", "Integer", "Single", "Double"]

		#Add correct delimiters around field name
		SQL_field = AP.AddFieldDelimiters(Feature, Field) #[Field] for shapes and gdb, "Field" for mdb

		#Add correct delimiters around field value
		if str(AP.ListFields(Feature, Field)[0].type) == "String":
			SQL_value = "'" + str(Value) + "'"
		elif str(AP.ListFields(Feature, Field)[0].type) in TypeList:
			SQL_value = str(Value)
		else:
			raise TypeError

		#Build query
		SQL_query = SQL_field + Symbol + SQL_value

		return  SQL_query

	except TypeError:
		AP.AddError("Selected field value is not numeric or text.")
	except:
		AP.AddError("Error in BuildComplexSQL() function.")

def BuildSQL(Feature, Field, Value):
	#-----------------------------------------------------
	#This custom function will build a proper SQL query, by
	#managing, type of feature (mdb, gdb, shapefile) and type
	#of data (numerical or alpha).
	#-----------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	#Error handling classes
	class CustomError(Exception): pass #Mother class
	class TypeError(CustomError):pass #Child class

	try:

		#List of numerical field type
		TypeList = ["SmallInteger", "Integer", "Single", "Double", "OID"]

		#Add correct delimiters around field name
		SQL_field = AP.AddFieldDelimiters(Feature, Field) #[Field] for shapes and gdb, "Field" for mdb

		#Add correct delimiters around field value
		if str(AP.ListFields(Feature, Field)[0].type) == "String":
			SQL_value = "'" + str(Value) + "'"
		elif str(AP.ListFields(Feature, Field)[0].type) in TypeList:
			SQL_value = str(Value)
		else:
			raise TypeError

		#Build query
		SQL_query = SQL_field + " = " + SQL_value

		return  SQL_query

	except TypeError:
		AP.AddError("Selected field value is not numeric or text.")
	except:
		AP.AddError("Error in BuildSQL() function.")

def RequestLicence(LicenceName):
###Possible LicenceName
### 3D, Schematics, ArcScan, Business, DataInteroperability
### GeoStats, JTX, Network, Aeronautical, Defence, Foundation
### Datareviewer, Nautical, Spatial, StreetMap, Tracking

	#-------------------------------------------------------------
	#This custom function will retrieve an extension from the pool
	#-------------------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	try:

		#Check the availability
		if AP.CheckExtension(LicenceName) == "Available":
			AP.CheckOutExtension(LicenceName)
		else:
			raise

	except:
		AP.AddError("Error in RequestLicence() function.")

def RequestArcInfo():
	#-------------------------------------------------------------
	#This custom function will verify if the user has an ArcInfo licence
	#-------------------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	try:
		#Check the availability
		if AP.ProductInfo() != "ArcInfo":
			return "ArcInfo not licenced"
		else:
			return ""
	except:
		AP.AddError("Error in RequestArcInfo() function.")

def ExtractUniqueValuesByList(Object, field):
	#-------------------------------------------------------------
	#This custom function will retrieve unique values out of a
	#feature or raster dataset, and return a list.
	#-------------------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	try:
		#Create an empty list
		UniqueValues = []

		#Retrieve a list of values with a cursor
		Cursor = AP.SearchCursor(Object)

		#Iterate through all data
		for values in Cursor:
			#Extract unique values
			if values.getValue(field) not in UniqueValues:
				UniqueValues.append(values.getValue(field))

		return UniqueValues
	except:
		AP.AddError("Error in ExtractUniqueValuesByList() function.")

def ExtractUniqueValuesByList_double(Object, FirstField, SecondField):
	#-------------------------------------------------------------
	#This custom function will retrieve unique values out of a
	#feature from a second fields and return a dictionnary
	#Like a summarize from one field to second field
	#-------------------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	try:
		#Create an empty list
		UniqueValues = {}

		#Retrieve a list of values with a cursor
		Cursor = AP.SearchCursor(Object)

		#Iterate through all data
		for values in Cursor:

			#For first occurence within first field
			if values.getValue(FirstField) not in UniqueValues:
				#Add an empty to list to new dictionnary key (field
				UniqueValues[values.getValue(FirstField)] = []


			#Add values from second field
			if values.getValue(SecondField) not in UniqueValues[values.getValue(FirstField)]:
				UniqueValues[values.getValue(FirstField)].append(values.getValue(SecondField))

				#Sort values
				UniqueValues[values.getValue(FirstField)].sort()

		return UniqueValues
	except:
		AP.AddError("Error in ExtractUniqueValuesByList_double() function.")

def M_2aSymPol_01(InputFeature, FeatureField, FeatureFieldValue, MinArea, champ_result, Query):
	#-------------------------------------------------------------
	#This custom function is the same as script M_2aSymPol_01.py,
	#the difference is the results will be stored in chosen field,
	#not, the one used in the real script.
	#-------------------------------------------------------------
	#Import stand. lib.
	import arcpy as AP

	#Import custom libraries
	import GeoScaler_functions

	try:
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

			#On met é jour la ligne
			Cursor.updateRow(lines)

		del Cursor, lines #To prevent some locks

	except:
		AP.AddError("Error in M_2aSymPol_01() function.")

def ToolboxPath():
	#------------------------------------------------------------
	#This custom function will retrieve the GeoScaler10.tbx path,
	#within the xml file
	#------------------------------------------------------------
	#Import stand. lib.
	import os, sys, traceback
	from xml.etree import ElementTree
	import arcpy as AP

	#Error handling classes
	class CustomError(Exception): pass #Mother class
	class EnvironmentError(CustomError):pass #Child class

	try:
		#Variables
		XML_name = "GeoScaler_CustomSettings.xml"
		ScaleNode = "ToolboxPath"

		#Load current script path
		XML_path = os.path.realpath(os.path.dirname(sys.argv[0])) + "\\" + XML_name

		#Verify if the xml file exists
		if os.path.isfile(XML_path) == False:
			raise EnvironmentError

		#Parse the file
		tree = ElementTree.parse(XML_path)

		#Retreive the desire node within a list variable
		Node = tree.getiterator(ScaleNode)
		Path = Node[0].text

		return  Path

	except EnvironmentError:
		AP.AddError("Found no initialization XML. Initialize GeoScaler and restart script.")
	except:
		AP.AddError("ERROR line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def RetrieveInfoFromXML(WantedNodeList):
	#------------------------------------------------------------
	#This custom function will retrieve any given node from list,
	#from XML environment file
	#------------------------------------------------------------
	#Import stand. lib.
	import os, sys, traceback
	from xml.etree import ElementTree
	import arcpy as AP

	#Error handling classes
	class CustomError(Exception): pass #Mother class
	class EnvironmentError(CustomError):pass #Child class

	try:
		#Variables
		XML_name = "GeoScaler_CustomSettings.xml"
		ScaleNodeInfoList = [] #An empty list to store results

		#Load current script path
		XML_path = os.path.realpath(os.path.dirname(sys.argv[0])) + "\\" + XML_name

		#Verify if the xml file exists
		if os.path.isfile(XML_path) == False:
			raise EnvironmentError

		#Parse the file
		tree = ElementTree.parse(XML_path)

		for ScaleNode in WantedNodeList:

			#Retreive the desire node within a list variable
			Node = tree.getiterator(ScaleNode)
			ScaleNodeInfoList.append(Node[0].text)

		return  ScaleNodeInfoList

	except EnvironmentError:
		AP.AddError("Found no initialization XML. Initialize GeoScaler and restart script.")
	except:
		AP.AddError("ERROR line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def M_2aSymPnt_01(InputFeature, FeatureField, FeatureFieldValue, NFD, ScriptName):
	#------------------------------------------------------------
	# Will help generalizing individual symbol classes by eliminating
	# superposition between symbols.
	#------------------------------------------------------------
	#Import standard libs.
	import sys, traceback, string, os
	import arcpy as AP

	#Import custom libs.
	import GeoScaler_functions

	#Error handling classes
	class CustomError(Exception): pass #Mother class
	class EnvironmentError(CustomError):pass #Child class

	try:
		#Set field names
		Field_NF = "NEAR_FID" #Field name that will serve multiple superposition generalization
		Field_ND = "NEAR_DIST" #Field name that will serve double superposition generalization
		Field_ID = AP.ListFields(InputFeature)[0].name #Field name containing unique ids

		#Other variables
		FeatureLayer = "InputFeature"

		#-------------------------------------------------------------------
		#Verify the product licence, scripts need ArcInfo
		#-------------------------------------------------------------------
		if GeoScaler_functions.RequestArcInfo() != "":
			raise EnvironmentError

		#-------------------------------------------------------------------
		#Retrieve generalization results field
		#-------------------------------------------------------------------
		champ_result_alpha = GeoScaler_functions.FieldDictionnary(ScriptName)

		#-------------------------------------------------------------------
		#Build a field name with scale in it
		#-------------------------------------------------------------------
		champ_result = GeoScaler_functions.BuildResultingField(champ_result_alpha)

		#-------------------------------------------------------------------
		#Add results field, if needed
		#-------------------------------------------------------------------
		GeoScaler_functions.VerifyResultingField(InputFeature, champ_result)

		#-------------------------------------------------------------------
		#Multiple superposition generalization
		#-------------------------------------------------------------------
		AP.AddMessage("1. Beginning generalization of multiple superposed symbols...")

		#Create a lyr file
		if FeatureField != "#": #If something is in this parameter
			#Build a correct SQL query
			SQL_query = GeoScaler_functions.BuildSQL(InputFeature,FeatureField,FeatureFieldValue)

			AP.MakeFeatureLayer_management(InputFeature, FeatureLayer, SQL_query)

		else: #Process all the feature
			AP.MakeFeatureLayer_management(InputFeature, FeatureLayer)

		#Calculate all values as 1, to start.
		AP.CalculateField_management(FeatureLayer, champ_result, 1)

		#Loop until there is no more neighbours
		Neighbours = True
		while Neighbours==True:
			Neighbours=False

			#Select only 1 coted symbols, so there are the only one passed to the near analysis
			AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", str(champ_result) + " = 1")

			#Perform a near analysis
			AP.Near_analysis(FeatureLayer, FeatureLayer, str(NFD), "NO_LOCATION", "NO_ANGLE")

			#Create cursor with proper query to select neighbours (symbol with a diff. value of -1 id.)
			Cursor_M = AP.SearchCursor(FeatureLayer, str(champ_result) + " = 1 AND NEAR_FID <> - 1")

			#Variables
			uniqueList = []
			liste_mult_elim = [] #List that will contain all symbols to be coted 0

			for ligne_M in Cursor_M:
				#Find duplicate values within list
				if ligne_M.getValue(Field_NF) not in uniqueList:
					uniqueList.append(ligne_M.getValue(Field_NF))
				else:
					liste_mult_elim.append(ligne_M.getValue(Field_NF))

			#-------------------------------------------------------------------
			#Cursor to update the input feature with generalized informations
			Cursor_M2 = AP.UpdateCursor(FeatureLayer, str(champ_result) + " = 1")

			#If there is multiple neighbours
			if len(liste_mult_elim)!=0 :
				AP.AddMessage("	 Number of symbol coded as 0 in the current iteration: " + str(len(liste_mult_elim)))

				for ligne_M2 in Cursor_M2:
					fid_in_liste = (ligne_M2.getValue(Field_ID) in liste_mult_elim)

					#If the object is in the list
					if fid_in_liste == True:
						ligne_M2.setValue(str(champ_result),0)

					#If the object is not in the list
					else:
						ligne_M2.setValue(str(champ_result),1)

					#Update
					Cursor_M2.updateRow(ligne_M2)
				Neighbours=True

		#-------------------------------------------------------------------
		#Double superposition generalization
		#-------------------------------------------------------------------
		AP.AddMessage("2. Beginning generalization of double superposed symbols...")

		Neighbours_D = True
		while Neighbours_D==True:

			Neighbours_D=False

			#Select only 1 coted symbols, so there are the only one passed to the near analysis
			AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", str(champ_result) + " = 1")

			#Perform a near analysis
			AP.Near_analysis(FeatureLayer, FeatureLayer, str(NFD), "NO_LOCATION", "NO_ANGLE")

			#Create cursor with proper query to select neighbours (symbol with a diff. value of 0m.)
			Cursor_D = AP.SearchCursor(FeatureLayer, str(champ_result) + " = 1 AND NEAR_DIST > 0")

			#Variables
			uniqueList_D = []
			liste_doublons_elim = [] #List that will contain all symbols to be coted 0
			liste_ID_doublons_elim = [] #List that will contain all symbols ids to be coted 0

			for ligne_D in Cursor_D:
				#Find duplicate values within list
				if ligne_D.getValue(Field_ND) not in uniqueList_D:
					uniqueList_D.append(ligne_D.getValue(Field_ND))
				else:
					liste_doublons_elim.append(ligne_D.getValue(Field_ND))
					liste_ID_doublons_elim.append(ligne_D.getValue(Field_NF))

			#-------------------------------------------------------------------
			#Cursor to update the input feature with generalized informations
			Cursor_D2 = AP.UpdateCursor(FeatureLayer,str(champ_result) + " = 1")

			#If there is a neighbour
			if len(liste_ID_doublons_elim)!=0 :
				AP.AddMessage("	 Number of symbol coded as 0 in the current iteration: " + str(len(liste_ID_doublons_elim)))
				for ligne_D2 in Cursor_D2:
					fid_in_liste = (ligne_D2.getValue(Field_ID) in liste_ID_doublons_elim)

					#If the object is in the list
					if fid_in_liste == True:
						ligne_D2.setValue(str(champ_result),0)

					#If the object is not in the list
					else:
						ligne_D2.setValue(str(champ_result),1)
					#Update
					Cursor_D2.updateRow(ligne_D2)
				Neighbours_D=True

		#-------------------------------------------------------------------
		#End message
		#-------------------------------------------------------------------
		AP.AddMessage("Results are available in field: " + str(champ_result)+".")

	except EnvironmentError:
		 AP.AddError("No ArcInfo licence available, retry later.")
	except:
		AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def GenerateNearTable(InputFeature, NearFeature, NearDistance):
	#------------------------------------------------------------
	# Will reproduce the ArcGIS tool GenerateNearTable for neighbour
	# analysis purposes.
	#------------------------------------------------------------
	#Import standard libs.
	import sys, traceback, os
	import arcpy as AP
	import GeoScaler_functions
	try:
		#-------------------------------------------------------------------
		#Hardcoding variables
		#-------------------------------------------------------------------
		Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
		InFID = "IN_FID" #Field that will contains the id from input feature
		NearFID = "NEAR_FID" #Field that will contain the id from near feature
		InLayer = "InLayer" #For selection purposes
		NearLayer = "NearLayer" #For selection purposes
		Prefix = "NT" #For NearTable, will be used for temp data names
		FixID = "FixID" #A new field to store ids.
		FieldNames = [] #An empty to store all the field names from near feature
		NearIDDict = {} #An empty dictionnary to store all the ids of the input and nearest features
		NearIDList = [] #An empty list to store all the ids of the nearest features

		#-------------------------------------------------------------------
		#Prepare output table
		#-------------------------------------------------------------------
		OutputTable = AP.CreateScratchName(Prefix, "", "ArcInfoTable", Script_path)
		TableName = OutputTable.split("\\")[-1]
		AP.CreateTable_management(Script_path, TableName)

		#Add the fields
		AP.AddField_management(OutputTable, InFID, "LONG", "#")
		AP.AddField_management(OutputTable, NearFID, "LONG", "#")

		#-------------------------------------------------------------------
		#Prepare data from the features
		#-------------------------------------------------------------------
		#Describe the near feature
		Desc = AP.Describe(NearFeature)
		Fields = Desc.Fields
		ID = Desc.OIDFieldName

		#Describe the input feature
		Desc = AP.Describe(InputFeature)
		InputID = Desc.OIDFieldName

		for all_fields in Fields:
			FieldNames.append(all_fields.Name)

		if FixID not in FieldNames:
			#Add a new field to store FIDs within feature
			AP.AddField_management(NearFeature, FixID, "LONG", "#")

			#Calculate fixed ids
			FieldDelim = AP.AddFieldDelimiters(NearFeature, ID)
			AP.CalculateField_management(NearFeature, FixID, FieldDelim, "VB")

		#Make layers
		AP.MakeFeatureLayer_management(InputFeature, InLayer)
		AP.MakeFeatureLayer_management(NearFeature, NearLayer)

		#-------------------------------------------------------------------
		#Select nearest features
		#-------------------------------------------------------------------
		#Start a cursor to read each lines from InputFeature
		InputCursor = AP.SearchCursor(InLayer)
		for input_lines in InputCursor:

			#Build an SQL Query to select the current feature
			SQL = GeoScaler_functions.BuildSQL(InputFeature, InputID, int(input_lines.getValue(InputID)))

			#Select one feature only within the Input Feature
			AP.SelectLayerByAttribute_management(InLayer, "NEW_SELECTION", SQL)

			#Apply a select by location with a buffer
			AP.SelectLayerByAttribute_management(NearLayer, "CLEAR_SELECTION")
			CountBefore = AP.GetCount_management(NearLayer)
			AP.SelectLayerByLocation_management(NearLayer, "INTERSECT", InLayer, NearDistance, "NEW_SELECTION")
			CountAfter = AP.GetCount_management(NearLayer)
			AP.AddWarning(str(CountBefore)+ " " + str(CountAfter))
			#If something else than nothing is returned
			if str(CountBefore)!= str(CountAfter) and str(CountAfter)!= "0":
				#Copy the selected features to a temporary output table
				TempTable = AP.CreateScratchName(Prefix, "", "ArcInfoTable", Script_path)
				AP.CopyRows_management(NearLayer,TempTable)

				Desc2 = AP.Describe(TempTable)
				ID2 = Desc2.OIDFieldName

				#Read inside the new feature to retrieve IDs
				NewCursor = AP.SearchCursor(TempTable)
				for newLines in NewCursor:
					NearIDList.append(newLines.getValue(FixID))
				del NewCursor, newLines

				#Append the dictionnary with an ID
				NearIDDict[input_lines.getValue(InputID)] = NearIDList

				#Delete the temp feature
				AP.Delete_management(TempTable)

				AP.AddWarning(str(NearIDDict))

		#-------------------------------------------------------------------
		#Update the output table with nearest features
		#-------------------------------------------------------------------
		InCursor = AP.InsertCursor(OutputTable)

		for new_lines in sorted(NearIDDict):
			#Get the value from dict.clear
			List = NearIDDict[new_lines]

			#Initialize the row object
			rows = InCursor.newRow()

			#Iterate through the value of the key, wich is a list of ids
			for items in List:
				#Input the IN_FID from dictionnary key
				rows.setValue(InFID, new_lines)
				#Input the NEAR_FID from dictionnar list
				rows.setValue(NearFID, items)
				#Insert the new row
				InCursor.insertRow(rows)

		del InCursor, rows

		#-------------------------------------------------------------------
		#Delete temp data
		#-------------------------------------------------------------------
		AP.Delete_management(InLayer)
		AP.Delete_management(NearLayer)

		return OutputTable

	except:
		AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def SaveSettingToFile(OutputFile, ValueList):
	#------------------------------------------------------------
	# Will write into an output text file a set of values from a
	# given list.
	#------------------------------------------------------------
	import arcpy as AP
	import sys, traceback
	try:
		#Create new text file
		outFile = file(OutputFile, "w")

		#Iterate through list and write values within file
		for strings in ValueList:
			outFile.write(strings + "\n")

		outFile.close()
	except:
		AP.AddError("SaveSettingToFile Error, line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def M_2aSymLine_01(InputFeature, Field, FieldValue, MTL, ScriptName):
	#------------------------------------------------------------
	# Will help generalizing individual line symbol classes by eliminating
	# short lines
	#------------------------------------------------------------
	#Import standard libs.
	import sys, traceback, string, os
	import arcpy as AP

	#Import custom libs.
	import GeoScaler_functions

	try:

		#-------------------------------------------------------------------
		#Retrieve generalization results field
		#-------------------------------------------------------------------
		champ_result_alpha = GeoScaler_functions.FieldDictionnary(ScriptName)

		#-------------------------------------------------------------------
		#Build a field name with scale in it
		#-------------------------------------------------------------------
		ResultField = GeoScaler_functions.BuildResultingField(champ_result_alpha)

		#-------------------------------------------------------------------
		#Add results field, if needed
		#-------------------------------------------------------------------
		GeoScaler_functions.VerifyResultingField(InputFeature, ResultField)

		#-------------------------------------------------------------------
		#Generalization
		#-------------------------------------------------------------------
		#Verify if user wants to apply the model on the entire feature or not
		if Field != "#": #If something is in this parameter
			#Create an SQL Query to fit into the cursor
			SQL = GeoScaler_functions.BuildSQL(InputFeature, Field, FieldValue)

			#Create update cursor
			UpCursor = AP.UpdateCursor(InputFeature, SQL)

		else:
			#Create update cursor
			UpCursor = AP.UpdateCursor(InputFeature)

		#Iterate through cursor
		for rows in UpCursor:
			#Get the real length
			Length = rows.Shape.length

			#Validate with MTL value
			if Length <= int(MTL):
				rows.setValue(ResultField, 0)

			elif Length > int(MTL):
				rows.setValue(ResultField, 1)

			#Update
			UpCursor.updateRow(rows)
		del rows, UpCursor

		#-------------------------------------------------------------------
		#End message
		#-------------------------------------------------------------------
		AP.AddMessage("Results are available in field: " + str(ResultField)+".")

	except:
		AP.AddError("M_2aSymLine_01 Error, line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def SymbolsOverPolygons(InputFeature, Field, FieldValue, PolygonFeature, PolField, PolFieldValue, ResultField):
	#------------------------------------------------------------
	# Will generalize any symbol overlaps with wanted polygons.
	#------------------------------------------------------------
	#Import standard libs.
	import sys, traceback, string, os
	import arcpy as AP

	#Import custom libs.
	import GeoScaler_functions

	try:
		#-------------------------------------------------------------------
		#Hardcoding variables and input parameters
		#-------------------------------------------------------------------
		PntFeatureLayer = "Pnt"
		PolFeatureLayer = "Pol"

		#-------------------------------------------------------------------
		#Analyse symbols over given polygons.
		#-------------------------------------------------------------------
		#Make feature layers with inputs
		AP.MakeFeatureLayer_management(InputFeature, PntFeatureLayer)
		AP.MakeFeatureLayer_management(PolygonFeature, PolFeatureLayer)

		#Select given polygons, if user entered one
		if PolField != "#":
			SQL_query = GeoScaler_functions.BuildSQL(PolygonFeature,PolField,PolFieldValue)
			AP.SelectLayerByAttribute_management(PolFeatureLayer, "NEW_SELECTION", SQL_query)

		#Select given point symbol class, if user entered one
		if Field != "#":
			SQL_query2 = GeoScaler_functions.BuildSQL(InputFeature, Field, FieldValue)
			AP.SelectLayerByAttribute_management(PntFeatureLayer, "NEW_SELECTION", SQL_query2)

		#Proceed with a select by location analysis
		CountBefore = AP.GetCount_management(PntFeatureLayer)
		AP.SelectLayerByLocation_management(PntFeatureLayer, "INTERSECT", PolFeatureLayer, "#", "NEW_SELECTION")
		CountAfter = AP.GetCount_management(PntFeatureLayer)

		#Verify the integrity of the last selection
		if CountAfter != 0:
			AP.AddMessage("Number of symbol overlaping polygons: " + str(CountAfter))
			AP.CalculateField_management(PntFeatureLayer, ResultField, 0, "VB")

		else: #The selection returns nothing
			AP.AddWarning("No symbols were superposed with the given polygon class: " + PolField + " = " + PolFieldValue + ".")

	except:
		AP.AddError("SymbolsOverPolygons Error, line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

def MultipleCon_diff(ValueList, Input, Output, FieldValue):
	###Will apply a conditional function on a list a value, with a diff symbol.
	import arcpy.sa as APSA
	import arcpy as AP

	try:
		for values in ValueList:
			if ValueList.index(values) == 0:
				SQL = '"' + FieldValue + '" <> ' + values
			else:
				SQL = SQL + " AND " + '"' + FieldValue + '" <> ' + values
		Con = APSA.Con(Input, Input, "#", SQL)
		Con.save(Output)
	except:
		AP.AddError("Error within MultipleCon() function.")
