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
    return

  def updateParameters(self):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parmater
    has been changed."""

    #-------------------------------------------------------------------
    #If a user wants to enter a class of value instead of entire feature
    #-------------------------------------------------------------------
    if self.params[2].value == False:
      #Enable parameters
      self.params[1].enabled = False
      self.params[3].enabled = True
      self.params[4].enabled = True
      self.params[5].enabled = True
      self.params[6].enabled = True
      
    else:
      #Disable third parameter
      self.params[1].enabled = True
      self.params[3].enabled = False
      self.params[4].enabled = False
      self.params[5].enabled = False
      self.params[6].enabled = False
      
    #-------------------------------------------------------------------   
    #Loading the settings from the input textfile
    #-------------------------------------------------------------------
    if self.params[4].altered and self.params[5].value == None:
      SettingList = ""
      InFile = file(str(self.params[4].value), "r")
      for lines in InFile.readlines():
        SettingList = SettingList + str(lines.split("\n")[0]) + ";"
      self.params[5].value = SettingList

      InFile.close()
      
    return

  def updateMessages(self):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""
    return
