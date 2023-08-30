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

  def updateParameters(self):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parmater
    has been changed."""

    #-------------------------------------------------------------------
    #If a user wants to enter a class of value instead of entire feature
    #-------------------------------------------------------------------
    if self.params[1].value == False:
      #Enable third parameter
      self.params[2].enabled = True
      self.params[3].enabled = True
      
    else:
      #Disable third parameter
      self.params[2].enabled = False
      self.params[3].enabled = False
      
    #-------------------------------------------------------------------
    #If a user has selected a field
    #-------------------------------------------------------------------
    if self.params[2].altered and self.params[1].value == False and self.params[3].altered == False:
      
      #Import stand. lib.
      import arcpy as AP
      
      #Create empty list
      UniqueValues = []
      
      #Iterate through all unique values
      rows = AP.SearchCursor(self.params[0].value)
      
      for row in rows:
        if str(row.getValue(self.params[2].value)) != "None": #To manage "Null" values within mdb or gdb.
          if str(row.getValue(self.params[2].value)) != "": #To manage empty string values
            if row.getValue(self.params[2].value) not in UniqueValues:
              UniqueValues.append(row.getValue(self.params[2].value))

      #Input all unique values within fourth parameter
      UniqueValues = sorted(UniqueValues)
      self.params[3].filter.list = UniqueValues
    
    else:
      #Disable fourth parameter
      self.params[3].enabled = False
 
    return

  def updateMessages(self):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""
    return
