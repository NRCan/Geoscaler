# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_3Val_02.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will calculate theorical Radical Law for symbol generalization
# Original work: Gabriel H.V. (LCNP), 2009
# ---------------------------------------------------------------------------

#Import standard libs.
import sys, traceback, string, os, math, time
import arcpy as AP

#Import custom libs.
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class RadicalLawError(CustomError):pass #Child class

try:
    #-------------------------------------------------------------------
    #Hardcoding variables and input parameters
    #-------------------------------------------------------------------
    #Retrieve input parameters
    InputFeature = sys.argv[1]  #Feature to generalize
    EntireFeature = sys.argv[2] #Model will be apply if the entire or a class is entered
    Field = sys.argv[3] #Feature field to generalize with
    FieldValue = sys.argv[4] #Feature field value, generalization will occur only on this class of symbol
    GeneField = sys.argv[5] #Field that contains generalization results
    InitialScale = float(sys.argv[6]) #The initial scale e.g. 50000 for 1:50 000 --> Needs to be float or else math.pow returns 0
    TargetScale = float(sys.argv[7]) #The target scale e.g. 100000 for 1:100 000 --> Needs to be float or else math.pow returns 0
    OutputTextFile = sys.argv[8] #Text file that will contain the results

    #Radical Law algorithm variables
    X = 0 #Exponent, determined by feature geometry
    NumBefore = 0 #Number of symbols before generalization
    RealNumAfter = 0 #Real number of symbols after generalization
    TheoNumAfter = 0 #Theorial number of symbols the user should have after generalization

    #Other variables
    GeometryDict = {"Point":1, "Polyline":2, "Polygon":3}
    ResultDict = {1:0, 0:0} #The keys represent 1 and 0 coted symbols, and the values are the total number for each keys, within feature

    #-------------------------------------------------------------------
    #Prepare the data
    #-------------------------------------------------------------------
    #Retreive geometry type, will determine the exponent of radical law algorithm
    Desc = AP.Describe(InputFeature)
    GeomType = Desc.ShapeType

    if GeomType in GeometryDict:
        X = GeometryDict[GeomType]
    else:
        raise RadicalLawError

    #Iterate through feature to retrieve info from table
    if EntireFeature == "true":
        Cursor = AP.SearchCursor(InputFeature)
    else:
        SQL_query = GeoScaler_functions.BuildSQL(InputFeature,Field,FieldValue)
        Cursor = AP.SearchCursor(InputFeature, SQL_query)

    for rows in Cursor:
        #Build a dictionnary of 0 and 1 values
        if rows.getValue(GeneField)== 1:
            ResultDict[1] = ResultDict[1]+1
        elif rows.getValue(GeneField)== 0:
            ResultDict[0] = ResultDict[0]+1
    del rows, Cursor

    #Date and time
    DateList = time.localtime() #Build a list of time variables (year/month/day/...)
    Date = str(DateList[0]) + "/" + str(DateList[1]) + "/" + str(DateList[2])
    if DateList[4]< 10:
        Min = "h0" + str(DateList[4])
    else:
        Min = "h" + str(DateList[4])
    Time = str(DateList[3]) + Min

    #-------------------------------------------------------------------
    #Calculate algorithm
    #-------------------------------------------------------------------
    #Calculate number of symbols before and after generalization
    NumBefore = ResultDict[1] + ResultDict[0]
    RealNumAfter = ResultDict[1]

    #Calculate radical law
    TheoNumAfter = int(NumBefore * math.sqrt(math.pow(InitialScale/TargetScale,X)))

    #Calculate percentage deviation
    DevPer = round(100.0-((float(TheoNumAfter)/float(RealNumAfter))*100.0),1)

    #-------------------------------------------------------------------
    #Build text file
    #-------------------------------------------------------------------
    ResultList = ["Date: " + Date, "Time: " + Time, "Model: M_3Val_02 / Radical Law validation", "----------------", \
                  "Geometry type: " + GeomType, \
                  "Initial scale: " + str(int(InitialScale)), \
                  "Target scale: " + str(int(TargetScale)), \
                  "Number of symbols before generalization: " + str(NumBefore), \
                  "Number of symbols after generealization: " + str(RealNumAfter), \
                  "Theorical number of symbol (Radical law result):" + str(TheoNumAfter), \
                  "Deviation from theorical number (%): " + str(DevPer)]

    #-------------------------------------------------------------------
    #Save results in textfile
    #-------------------------------------------------------------------
    GeoScaler_functions.SaveSettingToFile(OutputTextFile, ResultList)

    #-------------------------------------------------------------------
    #End message
    #-------------------------------------------------------------------
    AP.AddMessage("Results are available in text file: " + str(OutputTextFile)+".")

except RadicalLawError:
     AP.AddError("Before running this model, last point generalization model B:04 Global generalization must be run first.")
except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))