# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# M_2aPol_01.py
# Gabriel Huot-Vézina (LCNP), 2010
#   Will prepare input data, for later polygon generalization with cellular
#   automata.
###NEEDS A SPATIAL ANALYST LICENCE
# ---------------------------------------------------------------------------

#Import des librairies standards
import sys, traceback, string, os
import arcpy as AP
import arcpy.sa as AP_SA #For spatial analyst tools

#Import custom libraries
import GeoScaler_functions

#Error handling classes
class CustomError(Exception): pass #Mother class
class EnvironmentError(CustomError):pass #Child class

try:

	#-------------------------------------------------------------------
	#Hardcoding variables and input parameters
	#-------------------------------------------------------------------
	#Retrieve input parameters
	Script_path = os.path.dirname(sys.argv[0]) #The path to the current script
	FL_Pol = sys.argv[1]  #Input polygon feature layer
	FL_field = sys.argv[2] #Input polygon feature layer field (only num)
	Cellsize = sys.argv[3] #Cellsize for the output grid
	Output_grid_path = sys.argv[4] #Path and name for the output grid file.
	FL_Hydro = sys.argv[5] #Input hydrographic polygon feature layer.
	FL_Hydro_field = sys.argv[6] #Input hydrographic polygon feature layer field (only num)
	FL_Hydro_isle_value = sys.argv[7] #Input hydrographic polygon feature layer island value (only num)

	#Other variables
	RasterField = "VALUE" #Usually the default when converting feature layer to raster
	Prefix = "GS"

	#-------------------------------------------------------------------
	#If a user wants to convert a geological polygon only.
	#-------------------------------------------------------------------
	AP.AddMessage("1. Beginning geological feature layer conversion into a grid file...")

	if FL_Hydro == "#":
		AP.PolygonToRaster_conversion(FL_Pol, FL_field, Output_grid_path, "MAXIMUM_AREA", "#", Cellsize)

	#------------------------------------------------------------------------------
	#If a user wants to convert a geological polygon with an hydrographic network.
	#------------------------------------------------------------------------------
	else:
		#Create the geological grid
		Scratch_geol = AP.CreateScratchName(Prefix, "", "RasterDataset", Script_path)
		AP.PolygonToRaster_conversion(FL_Pol, FL_field, Scratch_geol, "MAXIMUM_AREA", "#", Cellsize)

		AP.AddMessage("2. Beginning hydrographic network feature layer conversion into a grid file...")

		#Create the hydrological grid and manage isle values, if necessary
		if FL_Hydro_isle_value != "#":

			#Retrieve a Spatial Analyst licence
			try:
				GeoScaler_functions.RequestLicence("Spatial")
			except:
				raise EnvironmentError

			#Create the hydro grid
			Scratch_hydro = AP.CreateScratchName(Prefix, "", "RasterDataset", Script_path)
			AP.PolygonToRaster_conversion(FL_Hydro, FL_Hydro_field, Scratch_hydro, "MAXIMUM_AREA", "#", Cellsize)
			Remap = AP_SA.RemapValue([[int(FL_Hydro_isle_value), "NODATA"]])

			#Reclassify the isle value
			Scratch_hydro2 = AP.CreateScratchName(Prefix, "", "RasterDataset", Script_path)
			outReclassify = AP_SA.Reclassify(Scratch_hydro, RasterField, Remap)
			outReclassify.save(Scratch_hydro2)

			#Return the Spatial Analyst licence
			AP.CheckInExtension("Spatial")

		else:
			Scratch_hydro2 = AP.CreateScratchName(Prefix, "", "RasterDataset", Script_path)
			AP.PolygonToRaster_conversion(FL_Hydro, FL_Hydro_field, Scratch_hydro2, "MAXIMUM_AREA", "#", Cellsize)

		#Merging the two grids within one
		OutputGridPath = os.path.dirname(Output_grid_path)
		OutputGridName = string.split(os.path.basename(Output_grid_path),".")[0]
		##Using a 32 bit unsigned output because of new national color scheme gor geology (using 8 numbers seperated by dots)
		AP.MosaicToNewRaster_management(Scratch_geol + ";" + Scratch_hydro2, OutputGridPath, OutputGridName, "#", "32_BIT_SIGNED", Cellsize, "1", "LAST","FIRST")

	#------------------------------------------------------------------------------
	#Deleting useless temp data
	#------------------------------------------------------------------------------
	if FL_Hydro != "#":
		AP.Delete_management(Scratch_geol)
		AP.Delete_management(Scratch_hydro2)
	if FL_Hydro_isle_value != "#":
		AP.Delete_management(Scratch_hydro)

except EnvironmentError:
	AP.AddError("No " + str(LicenceName) + " licence available, retry later.")
except:
	AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))

