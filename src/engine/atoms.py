import numpy as np
from utils.depend import *
from utils.restart import *
from utils import units

class Atom(dobject):
   """Represent an atom, with position, velocity, mass and related properties.
      This is actually only an interface to the Atoms class, i.e. only stores
      views of the large arrays which contain all the coordinates.      
      """
            
   def __init__(self, system, index, label="X"):
      self.name=label
      dset(self,"p",system.p[3*index:3*index+3])
      dset(self,"q",system.q[3*index:3*index+3])
      dset(self,"m",system.m[index:index+1])
      dset(self,"m3",system.m3[3*index:3*index+3])
      
      dset(self,"kin",depend_value(name="kin", deps=depend_func(func=self.get_kin, dependencies=[depget(self,"p"),depget(self,"m3")]) ))
      dset(self,"kstress",depend_value(name="kstress", 
                         deps=depend_func(func=self.get_kstress, dependencies=[depget(self,"p"),depget(self,"m")]) ))

   def get_kin(self):
      """Calculates the contribution of the atom to the kinetic energy"""
      return np.dot(self.p,self.p)/(2.0*self.m)

   def get_kstress(self):
      """Calculates the contribution of the atom to the kinetic stress tensor"""
      p=depstrip(self.p)
      ks = numpy.zeros((3,3),float)
      for i in range(3):
         for j in range(i,3):
            ks[i,j] = p[i]*p[j]            
      return ks/self.m

class Atoms(dobject):
   """Storage for the atoms positions and velocities. Everything is stored as 3*n-sized contiguous arrays,
   and a convenience-access is provided through a list of Atom objects"""   

   def __init__(self, natoms, _prebind=None):
      self.natoms=natoms
      
      if _prebind is None:
         dset(self,"q",depend_array(name="q",value=np.zeros(3*natoms, float)) ) 
         dset(self,"p",depend_array(name="p",value=np.zeros(3*natoms, float)) )
         dset(self,"m",depend_array(name="m",value=np.zeros(natoms, float)) )
      else:   # it is possible to bind the storage of data elsewhere and just plug it in here
         dset(self,"q",_prebind[0]) 
         dset(self,"p",_prebind[1]) 
         dset(self,"m",_prebind[2])          
         
      dset(self,"px",self.p[0:3*natoms:3]);       dset(self,"py",self.p[1:3*natoms:3]);      dset(self,"pz",self.p[2:3*natoms:3])
      dset(self,"qx",self.q[0:3*natoms:3]);       dset(self,"qy",self.q[1:3*natoms:3]);      dset(self,"qz",self.q[2:3*natoms:3])      
      

      # Interface to get a 3*n-sized array with masses      
      dset(self,"m3",depend_array(name="m3",value=np.zeros(3*natoms, float),deps=depend_func(func=self.mtom3, dependencies=[depget(self,"m")])))

      #  Access to individual atoms' properties via Atom objects     
      self._alist=[ Atom(self, i) for i in range(natoms) ]

      # Derived properties: total mass, kinetic energy, kinetic stress contribution
      dset(self,"M",depend_value(name="M",deps=depend_func(func=self.get_msum,dependencies=[depget(self,"m")])) )      
      dset(self,"kin",depend_value(name="kin",deps=depend_func(func=self.get_kin,dependencies=[depget(self,"p"),depget(self,"m3")])) )
      dset(self,"kstress",depend_value(name="kstress",deps=depend_func(func=self.get_kstress,dependencies=[depget(self,"p"),depget(self,"m")])) )
   
   def __len__(self): return self.natoms

   def __getitem__(self,index):
      return self._alist[index]

   def __setitem__(self,index,value):
      self._alist[index].p=value.p
      self._alist[index].q=value.q 
      self._alist[index].m=value.m
      self._alist[index].name=value.name

   def get_msum(self): return self.m.sum()
   
   def mtom3(self): m3=np.zeros(3*self.natoms,float); m3[0:3*self.natoms:3]=self.m; m3[1:3*self.natoms:3]=m3[0:3*self.natoms:3]; m3[2:3*self.natoms:3]=m3[0:3*self.natoms:3]; return m3
   
                  
   def get_kin(self):
      """Calculates the total kinetic energy of the system,
      by summing the atomic contributions"""
      return 0.5*np.dot(self.p,self.p/self.m3)
      
   def get_kstress(self):
      """Calculates the contribution of the atom to the kinetic stress tensor"""
      p=self.p.view(np.ndarray)
      ks = numpy.zeros((3,3),float)
      ks[0,0]=np.dot(self.px,self.px/self.m)
      ks[1,1]=np.dot(self.py,self.py/self.m)
      ks[2,2]=np.dot(self.pz,self.pz/self.m)
      ks[0,1]=np.dot(self.px,self.py/self.m)
      ks[0,2]=np.dot(self.px,self.pz/self.m)
      ks[1,2]=np.dot(self.py,self.pz/self.m)                        
      return ks
      
from utils.io.io_pdb import read_pdb      
class RestartAtoms(Restart):
   fields={ "natoms" : (RestartValue, (int,0)), "q" : (RestartArray,(float,np.zeros(0))),  "p" : (RestartArray,(float,np.zeros(0))),
            "m" : (RestartArray,(float, np.zeros(0))),  "names" : (RestartArray,(str,np.zeros(0, str))),
            "from_file" : (RestartValue,(str, "")), "init_temp": (RestartValue, (float, -1.0))  }
       
   def __init__(self, atoms=None, filename=""):
      super(RestartAtoms,self).__init__()
      if not atoms is None: self.store(atoms, filename="")
                       
   def store(self, atoms, filename=""):
      self.natoms.store(atoms.natoms)
      self.q.store(depstrip(atoms.q))
      self.p.store(depstrip(atoms.p))
      self.m.store(depstrip(atoms.m))
      self.names.store(np.array([a.name for a in atoms]))
      self.from_file.store(filename)
      
   def fetch(self):
      self.check()
      atoms=Atoms(self.natoms.fetch())
      atoms.q=self.q.fetch()
      atoms.p=self.p.fetch()      
      atoms.m=self.m.fetch()   
      i=0
      for n in self.names.fetch(): 
         atoms[i].name=n; i+=1
      return atoms
   
   def check(self): 
      # if required get data from file and/or initialize
      if self.from_file.fetch() != "":
         myatoms, mycell = read_pdb(open(self.from_file.fetch(),"r"))
         self.store(myatoms, self.from_file.fetch())      