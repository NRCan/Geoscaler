# -*- coding: cp1252 -*-
# ---------------------------------------------------------------------------
# Initialize.py
# Gabriel Huot-Vézina (LCNP), 2010
#   Will store the new reference scale within an xml and an ArcGIS environment file
# ---------------------------------------------------------------------------
#Import des librairies standards
import traceback, os, sys
import arcpy as AP
from xml.etree.ElementTree import Element, SubElement, ElementTree

try:
    #---------------------------------------------------------------------
    #Global variables and inputs
    #---------------------------------------------------------------------
    #Retrieve inputs
    Script_path = os.path.realpath(os.path.dirname(sys.argv[0]))
    Initial_scale = sys.argv[1]
    Target_scale = sys.argv[2]
    Input_Toolbox_path = sys.argv[3] ###Get from ToolValidator from the tool.

    #Variables
    XMLName = "GeoScaler_CustomSettings"
    XMLFileName = XMLName + ".xml"
    XMLFilePath = Script_path + "\\" + XMLFileName

    #---------------------------------------------------------------------
    #Build the top xml heading
    #---------------------------------------------------------------------
    top = Element('GEOSCALER_PROJECT')

    #---------------------------------------------------------------------
    #Build the children nodes for environment settings
    #---------------------------------------------------------------------
    child = SubElement(top, 'Context')
    child.text = 'Environment Settings'

    ScaleChild = SubElement(child, 'Initial_Scale')
    ScaleChild.text = str(Initial_scale)

    ScaleChild = SubElement(child, 'Target_Scale')
    ScaleChild.text = str(Target_scale)

    ScaleChild = SubElement(child, 'ToolboxPath')
    ScaleChild.text = str(Input_Toolbox_path)

    #---------------------------------------------------------------------
    #Save the XML
    #---------------------------------------------------------------------
    ElementTree(top).write(XMLFilePath)

except:
    AP.AddError("Line: " + str(traceback.tb_lineno(sys.exc_info()[2]))+ " " + str(AP.GetMessages()))



