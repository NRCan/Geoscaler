# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_3Val_01.py
# Gabriel Huot-Vézina (LCNP), 2011
#   Will analyse point feature and produce a raster of density distribution
#   for validation purposes
# Original work: Gabriel H.V. (LCNP), 2009
# ---------------------------------------------------------------------------

#Import standard libs.
import sys, traceback, string, os, math, time
import arcpy as AP
import arcpy.sa as APSA

#Import custom libs.
import GeoScaler_functions

try:
	#-------------------------------------------------------------------
	#Hardcoding variables and input parameters
	#-------------------------------------------------------------------
	#Retrieve input parameters
	InputFeature = sys.argv[1]  #Feature to analyse
	GeneField = sys.argv[2] #Field to base the density analysis on, if needed
	OutputRaster = sys.argv[3] #Feature field to generalize with

	#Other variables
	GeometryDict = {"Point":1, "Polyline":2}
	FeatureLayer = "FeatureLayer" #Will be use for selection purposes within input fault feature

	#-------------------------------------------------------------------
	#Request Spatial Analyst licence
	#-------------------------------------------------------------------
	GeoScaler_functions.RequestLicence("Spatial")

	#-------------------------------------------------------------------
	#Prepare the data
	#-------------------------------------------------------------------
	#Retreive geometry type, will determine with density analysis to do
	Desc = AP.Describe(InputFeature)
	GeomType = Desc.ShapeType

	if GeomType in GeometryDict:
		Geom = GeometryDict[GeomType]

	#Create feature layer
	AP.MakeFeatureLayer_management(InputFeature, FeatureLayer)

	#-------------------------------------------------------------------
	#Density analysis
	#-------------------------------------------------------------------
	#With generalization field selected
	if GeneField != "#":
		#Create an SQL query
		SQL = GeoScaler_functions.BuildSQL(InputFeature, GeneField, 1)
		#Select 1 coted symbols within featureLayer
		AP.SelectLayerByAttribute_management(FeatureLayer, "NEW_SELECTION", SQL)

	#For point density distribution
	if Geom == 1:
		#Analyse
		PntDensity = APSA.PointDensity(FeatureLayer, "NONE", "#", "#", "SQUARE_KILOMETERS")
		PntDensity.save(OutputRaster)

	#For line density distribution
	###This option has been disabled because it causes Arc to crash, even when run manually....
	elif Geom == 2:
		#Analyse
		LineDensity = APSA.LineDensity(FeatureLayer, "NONE", "#", "#", "SQUARE_KILOMETERS")
		LineDensity.save(OutputRaster)

except:
	AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))