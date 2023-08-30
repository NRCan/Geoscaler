class ToolValidator:
  """Class for validating a tool's parameter values and controlling
  the behavior of the tool's dialog."""

  def __init__(self):
    """Setup arcpy and the list of tool parameters."""
    import arcpy
    self.params = arcpy.GetParameterInfo()

  def initializeParameters(self):
    """Refine the properties of a tool's parameters.  This method is
    called when the tool is opened."""
    self.params[4].category = "Manage small polygons"
    self.params[6].category = "Manage small polygons"
    self.params[7].category = "Manage small polygons"
    self.params[8].category = "Manage small polygons"
    self.params[9].category = "Manage small polygons"
    self.params[10].category = "Manage small polygons"
    self.params[11].category = "Manage small polygons"
    self.params[12].category = "Manage small polygons"
    self.params[13].category = "Manage small polygons"
    self.params[5].category = "Multiple output (different interval)"

    #Set some enabled = False variables
    self.params[7].enabled = False
    self.params[8].enabled = False
    self.params[9].enabled = False
    self.params[10].enabled = False
    self.params[11].enabled = False
    self.params[12].enabled = False
    self.params[13].enabled = False
    return

  def updateParameters(self):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parmater
    has been changed."""
    #------------------------------------------------------------------
    #Cell size calculator [...]
    #------------------------------------------------------------------
    #Enable or not parameters
    if self.params[6].value == True:
      self.params[7].enabled = True
      self.params[8].enabled = True
      self.params[9].enabled = True
      self.params[10].enabled = True
      self.params[11].enabled = True
      self.params[12].enabled = True
      self.params[13].enabled = True
    else:
      self.params[7].enabled = False
      self.params[8].enabled = False
      self.params[9].enabled = False
      self.params[10].enabled = False
      self.params[11].enabled = False
      self.params[12].enabled = False
      self.params[13].enabled = False

    #Fill in some fields
    if str(self.params[0].value) != "None" and self.params[6].value == True:# and str(self.params[7].value) == "None":

      import arcpy as AP
      from xml.etree import ElementTree
      import os
      
      #Describe raster dataset
      Desc = AP.Describe(self.params[0].value)

      #Fill in raster resolution info.
      self.params[8].value = Desc.MeanCellHeight
      self.params[9].value = Desc.MeanCellWidth
        
      if str(self.params[7].value) == "None":
        #Load environment settings
        CurrentScriptPath = os.path.realpath(__file__)
        WorkingDirectory = CurrentScriptPath.split("#")[0].split("GeoscalerTools10")[0] + "Scripts"
        
        #Retrieve the tool folder path and build the xml path
        XMLFilePath = WorkingDirectory + "\\GeoScaler_CustomSettings.xml"

        #Opening the current xml file
        if os.path.isfile(XMLFilePath):
          tree = ElementTree.parse(XMLFilePath)

          #Fill in the target scale info.
          ParentNode = tree.getiterator('Target_Scale')
          TargetScale = int(ParentNode[0].text)
          self.params[7].value = TargetScale
    
    if self.params[6].value == True and str(self.params[0].value) != "None":
      
      #Calculate areas
      OneCellArea = self.params[8].value * self.params[9].value
      MinAreaScale = (self.params[7].value / 1000) * (self.params[7].value / 1000) #eg. 100 000 scale --> 100 000mm/1000mm gives 100m
      MinAreaVisibility = MinAreaScale * 1.5
      self.params[10].value = MinAreaScale
      self.params[11].value = MinAreaVisibility

      #Calculate cell size
      MinCellScale = MinAreaScale / OneCellArea
      MinCellVisibility = MinAreaVisibility / OneCellArea
      self.params[12].value = MinCellScale
      self.params[13].value = MinCellVisibility
      
    #------------------------------------------------------------------
    #Calculate output interval
    #------------------------------------------------------------------
    if self.params[2].altered == True:
      RangeValue = range(self.params[2].value)
      ValueList = []
      for elems in RangeValue:
        if divmod(self.params[2].value, elems + 1)[1] == 0 and elems != 0:
          ValueList.append(elems + 1)
        elif elems == 0:
          ValueList.append(1)
      self.params[5].filter.list = ValueList

    return

  def updateMessages(self):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""
    self.params[3].clearMessage()
    if self.params[3].value != "#" and self.params[3].altered == True:
      import string, os
      if len(string.split(os.path.basename(str(self.params[3].value)),".")[0]) < 5:
        self.params[3].setErrorMessage("Output raster file must have, at least, 5 caracters.")
    return
