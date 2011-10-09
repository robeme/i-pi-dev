import numpy
import math

class Thermostat(object): 
   @property
   def temp(self):
      return self.__temp

   @property
   def dt(self):
      print "base getter called"
      return self.__dt

   @dt.setter
   def dt(self,new):
      print "Thermo dt setter called"
      self.__dt = new
     
   def __init__(self, temp = 1.0, dt = 1.0):
      self.__temp=temp
      self.__dt=dt
