#*********************************************************************************                     
#* Copyright (C) 2019-2020 Alexey V. Akimov                                                   
#*                                                                                                     
#* This file is distributed under the terms of the GNU General Public License                          
#* as published by the Free Software Foundation, either version 2 of                                   
#* the License, or (at your option) any later version.                                                 
#* See the file LICENSE in the root directory of this distribution   
#* or <http://www.gnu.org/licenses/>.          
#***********************************************************************************
"""
.. module:: dynamics_hdf5
   :platform: Unix, Windows
   :synopsis: This module implements the read/write functions specifically designed to work with the dynamics module
       Uniquely to this module, all the read/write operations involve HDF5 files

       List of classes:

           * class mem_saver
           * class hdf5_saver

       List of functions:

           # TSH
           * init_hdf5(saver, hdf5_output_level, _nsteps, _ntraj, _ndof, _nadi, _ndia)
           * save_hdf5_1D(saver, i, dt, Ekin, Epot, Etot, dEkin, dEpot, dEtot)
           * save_hdf5_2D(saver, i, states)
           * save_hdf5_3D(saver, i, pops, dm_adi, dm_dia, q, p, Cadi, Cdia)
           * save_hdf5_4D(saver, i, tr, hvib_adi, hvib_dia, St, U, projector)

           # HEOM
           * heom_init_hdf5(saver, hdf5_output_level, _nsteps, _nquant)
           * heom_save_hdf5_1D(saver, i, dt)
           * heom_save_hdf5_3D(saver, i, denmat)

           # Exact
           * exact_init_hdf5(saver, hdf5_output_level, _nsteps, _ndof, _nstates, _ngrid)
           * exact_init_custom_hdf5(saver, _nsteps, _ncustom_pops, _nstates)


.. moduleauthor:: Alexey V. Akimov
  
"""

__author__ = "Alexey V. Akimov"
__copyright__ = "Copyright 2019 Alexey V. Akimov"
__credits__ = ["Alexey V. Akimov"]
__license__ = "GNU-3"
__version__ = "1.0"
__maintainer__ = "Alexey V. Akimov"
__email__ = "alexvakimov@gmail.com"
__url__ = "https://quantum-dynamics-hub.github.io/libra/index.html"


import h5py
import numpy as np

import os
import sys
import math
import copy

if sys.platform=="cygwin":
    from cyglibra_core import *
elif sys.platform=="linux" or sys.platform=="linux2":
    from liblibra_core import *

import util.libutil as comn
from . import units
from . import data_read


class mem_saver:
    """
    This class is needed for saving variables into a dictionary

    Example of usage:
    
        x = mem_saver(["q", "p"])

        x.add_data("q", 1.0)
        x.add_data("q", -1.0)

        print(x.data["q"])

    """


    def __init__(self, _keywords=[]):
        """
        Initializes an object that would store the data
        in different formats - the temporary and the numpy-consistent
        
        """
        
        # Names of the data sets
        self.keywords = list(_keywords)  
        
        # "Raw" data - elements could be of whatever data type
        self.data = {}  
        
        # "Numpy" data - elements are numpy arrays
        self.np_data = {}
        
        
        # Only initialize the "raw" data, don't touch the numpy
        for keyword in self.keywords:
            self.data[keyword] = []            

            
    def add_data(self, data_name, _data):
        """
        To collect arbitrary data
        
        Args:
            data_name (string): the name of the data set
            _data (anything): the data to be added
        
        
        This function simply appends the data elements
        to the prepared lists. There is no restriction on the 
        data type for the elements added
        """
        if keyword in self.keywords:
            self.data[data_name].append(_data)

                        
    def add_dataset(self, data_name, shape, dtype):
        """
        To initialize the numpy arrays to hold the data
        
        Args:
            data_name (string): the name of the data set
            shape (tuple of ints): the dimensions of the numpy array
            dtype (one of ["I", "R", or "C"]: the tye of data to be stored in the array
            
        """
        if data_name in self.keywords:
            pass
        else:
            self.keywords.append(data_name)


        if dtype=="I":
            self.np_data[data_name] = np.empty(shape, int)
            
        elif dtype=="R":
            self.np_data[data_name] = np.empty(shape, float)            
            
        elif dtype=="C":
            self.np_data[data_name] = np.empty(shape, complex)            
            
        else:
            print(F"ERROR: the dtype = {dtype} is not allowed in add_dataset")
                
    
              
    def save_scalar(self, istep, data_name, _data):
        """
        Saves a scalar to 1D array
        """

        if data_name in self.keywords and data_name in self.np_data.keys():
            self.np_data[data_name][istep] = _data
            
            
    def save_multi_scalar(self, istep, iscal, data_name, _data):
        """
        Saves a sacalar to 2D array
        """

        if data_name in self.keywords and data_name in self.np_data.keys():            
            self.np_data[data_name][istep, iscal] = _data

        
    def save_matrix(self, istep, data_name, _data):
        """          
        Saves a matrix to a 3D array
        
        Args:

          istep ( int ) :  index of the timestep for the data
          data_name ( string ) : how to call this data set internally
          _data ( (C)MATRIX(nx, ny) ) : the actual data to save          
           
        """

        if data_name in self.keywords and data_name in self.np_data.keys():

            nx, ny = _data.num_of_rows, _data.num_of_cols

            for i in range(nx):
                for j in range(ny):
                    self.np_data[data_name][istep, i, j] = _data.get(i, j)


    def save_multi_matrix(self, istep, imatrix, data_name, _data):
        """          
        Saves one of a series of matrices

        Args:
        
          istep ( int ) :  index of the timestep for the data
          data_name ( string ) : how to call this data set internally
          data ( (C)MATRIX(nx, ny) ) : the actual data to save
           
        """

        if data_name in self.keywords and data_name in self.np_data.keys():

            nx, ny = _data.num_of_rows, _data.num_of_cols

            for i in range(nx):
                for j in range(ny):
                    self.np_data[data_name][istep, imatrix, i, j] = _data.get(i, j)
                        

    
    def save_data(self, filename, data_names, mode):
        """
        To save the numpy data into HDF5 files
        
        Args:
            filename (string): the name of the HDF5 file where to save the res
            data_names (list of strings): the list of the names of the data sets to save
            mode ("w" or "a"): whether to overwrite the file or to append to it
        
        """

        print("In mem_saver.save_data()")
        print("data_name = ", data_names)        
        print("keywords = ", self.keywords)
        print("keys = ", self.np_data.keys() )

        #for key in self.np_data.keys():
        #    print(key, self.np_data[key] )
  
        
        with h5py.File(filename, mode) as f:
            
            for data_name in data_names:                
                if data_name in self.np_data.keys():

                    print(F"Saving the dataset named {data_name}/data")
                                                        
                    g = f.create_group(data_name)                                                            
                    g.create_dataset("data", data = self.np_data[data_name])
                    
                else:
                    print(F"{data_name} is not in the list {self.np_data.keys()}" )


class hdf5_saver:

    def __init__(self, _filename, _keywords=[]):
        """
        The constructor of the class objects

        Args:
            _filename ( string ): the name of the HDF5 file to be created
            _keywords ( list of strings ): the names of the data to be added, if the 
                the `data_name` argument in any of the `save_*` functions doesn't exist 
                in the provided list of keywords, the data will not be actually saved into
                the HDF5 file

        Example:
            saver = hdf5_saver("data.hdf")

        """

        self.keywords = list(_keywords)

        self.filename = _filename
        self.use_compression = 1
        self.c_compression_level = 4
        self.r_compression_level = 4
        self.i_compression_level = 9

        with h5py.File(self.filename, "w") as f:
            g = f.create_group("default")
            g.create_dataset("data", data=[])

        print("HDF5 saver is initialized...")
        print(F"the datasets that can be saved are: {self.keywords}")


    def add_keywords(self, _keywords):

        for keyword in _keywords:
 
            if keyword not in self.keywords:
                self.keywords.append(keyword)



    def set_compression_level(self, _use_compression, _compression_level):
        """
        To control how much of data compression we want to exercise

        """

        self.use_compression = _use_compression;
        self.c_compression_level = _compression_level[0]
        self.r_compression_level = _compression_level[1]
        self.i_compression_level = _compression_level[2]



    def add_dataset(self, data_set_name, dim, data_type):
        """

        Args:

            data_set_name ( string ): the name of the data set
            dim  ( tuple ) : dimensions of the data set
            data_type ["C", "R", "I"] : for complex, real, or integer
        
        Example:

            _nsteps, _ntraj, _ndof, _nstates = 10, 1, 2, 2

            saver.add_dataset("time", (_nsteps,) , "R")  # for saving the time axis
            saver.add_dataset("total_energies", (_nsteps, _ntraj), "R") # for saving trajectory-resolved energies
            saver.add_dataset("q", (_nsteps, _ntraj, _ndof), "R")  # for saving trajectory-resolved coordinates
            saver.add_dataset("Cadi", (_nsteps, _nstates, _nstates), "C") # for saving trajectory-resolve TD-SE amplitudes
            saver.add_dataset("Hadi", (_nsteps, _ntraj, _nstates, _nstates), "C")  # for saving trajectory-resolved H matrices


        """

        with h5py.File(self.filename, "a") as f:
            g = f.create_group(data_set_name)
            g.attrs["dim"] = dim
            g.attrs["data_type"] = data_type

            if self.use_compression==1:

                if data_type == "C":            
                    g.create_dataset("data", dim, dtype=complex, maxshape=dim, compression="gzip", compression_opts = self.c_compression_level)
                elif data_type == "R":            
                    g.create_dataset("data", dim, dtype=float, maxshape=dim, compression="gzip", compression_opts = self.r_compression_level)
                elif data_type == "I":            
                    g.create_dataset("data", dim, dtype=int, maxshape=dim, compression="gzip", compression_opts = self.i_compression_level)

            else:
                if data_type == "C":            
                    g.create_dataset("data", dim, dtype=complex, maxshape=dim)
                elif data_type == "R":            
                    g.create_dataset("data", dim, dtype=float, maxshape=dim)
                elif data_type == "I":            
                    g.create_dataset("data", dim, dtype=int, maxshape=dim)


    def save_scalar(self, istep, data_name, data):

        if data_name in self.keywords:
            with h5py.File(self.filename, "a") as f:
                f[F"{data_name}/data"][istep] = data


    def save_multi_scalar(self, istep, iscal, data_name, data):

        if data_name in self.keywords:
            with h5py.File(self.filename, "a") as f:
                f[F"{data_name}/data"][istep, iscal] = data


    
    def save_matrix(self, istep, data_name, data):
        """          
          Add a matrix

          istep ( int ) :  index of the timestep for the data
          data_name ( string ) : how to call this data set internally
          data ( (C)MATRIX(nx, ny) ) : the actual data to save
           
        """

        if data_name in self.keywords:

            nx, ny = data.num_of_rows, data.num_of_cols

            with h5py.File(self.filename, "a") as f:
      
                for i in range(nx):
                    for j in range(ny):
                        f[F"{data_name}/data"][istep, i, j] = data.get(i, j)



    def save_multi_matrix(self, istep, imatrix, data_name, data):
        """          
          Add a matrix

          istep ( int ) :  index of the timestep for the data
          data_name ( string ) : how to call this data set internally
          data ( (C)MATRIX(nx, ny) ) : the actual data to save
           
        """

        if data_name in self.keywords:

            nx, ny = data.num_of_rows, data.num_of_cols

            with h5py.File(self.filename, "a") as f:

                for i in range(nx):
                    for j in range(ny):
                        f[F"{data_name}/data"][istep, imatrix, i, j] = data.get(i, j)



#===================== TSH calculations output ====================

def init_hdf5(saver, hdf5_output_level, _nsteps, _ntraj, _ndof, _nadi, _ndia):
    """
    saver - can be either hdf5_saver or mem_saver

    """

    if hdf5_output_level>=1:

        # Time axis (integer steps)
        saver.add_dataset("timestep", (_nsteps,) , "I")  

        # Time axis
        saver.add_dataset("time", (_nsteps,) , "R")  
        
        # Average kinetic energy
        saver.add_dataset("Ekin_ave", (_nsteps,) , "R")  
        
        # Average potential energy
        saver.add_dataset("Epot_ave", (_nsteps,) , "R")  
        
        # Average total energy
        saver.add_dataset("Etot_ave", (_nsteps,) , "R")  
        
        # Fluctuation of average kinetic energy
        saver.add_dataset("dEkin_ave", (_nsteps,) , "R")  
        
        # Fluctuation of average potential energy
        saver.add_dataset("dEpot_ave", (_nsteps,) , "R")  
        
        # Fluctuation of average total energy
        saver.add_dataset("dEtot_ave", (_nsteps,) , "R")  


    if hdf5_output_level>=2:

        # Trajectory-resolved instantaneous adiabatic states
        saver.add_dataset("states", (_nsteps, _ntraj), "I") 


    if hdf5_output_level>=3:

        # Average adiabatic SH populations
        saver.add_dataset("SH_pop", (_nsteps, _nadi, 1), "R") 

        # Average adiabatic density matrices
        saver.add_dataset("D_adi", (_nsteps, _nadi, _nadi), "C") 

        # Average diabatic density matrices
        saver.add_dataset("D_dia", (_nsteps, _ndia, _ndia), "C") 



        # Trajectory-resolved coordinates
        saver.add_dataset("q", (_nsteps, _ntraj, _ndof), "R") 

        # Trajectory-resolved momenta
        saver.add_dataset("p", (_nsteps, _ntraj, _ndof), "R") 

        # Trajectory-resolved adiabatic TD-SE amplitudes
        saver.add_dataset("Cadi", (_nsteps, _ntraj, _nadi), "C") 

        # Trajectory-resolved diabatic TD-SE amplitudes
        saver.add_dataset("Cdia", (_nsteps, _ntraj, _ndia), "C") 


    if hdf5_output_level>=4:

        # Trajectory-resolved vibronic Hamiltoninans in the adiabatic representation
        saver.add_dataset("hvib_adi", (_nsteps, _ntraj, _nadi, _nadi), "C") 

        # Trajectory-resolved vibronic Hamiltoninans in the diabatic representation
        saver.add_dataset("hvib_dia", (_nsteps, _ntraj, _ndia, _ndia), "C") 

        # Trajectory-resolved time-overlaps of the adiabatic states
        saver.add_dataset("St", (_nsteps, _ntraj, _nadi, _nadi), "C") 

        # Trajectory-resolved diabatic-to-adiabatic transformation matrices 
        saver.add_dataset("basis_transform", (_nsteps, _ntraj, _ndia, _nadi), "C") 

        # Trajectory-resolved projector matrices (from the raw adiabatic to consistent adiabatic)
        saver.add_dataset("projector", (_nsteps, _ntraj, _nadi, _nadi), "C") 






def save_hdf5_1D(saver, i, dt, Ekin, Epot, Etot, dEkin, dEpot, dEtot):
    """
    saver - can be either hdf5_saver or mem_saver

    """

    # Timestep 
    saver.save_scalar(i, "timestep", i) 

    # Actual time
    saver.save_scalar(i, "time", dt*i)  

    # Average kinetic energy
    saver.save_scalar(i, "Ekin_ave", Ekin)  

    # Average potential energy
    saver.save_scalar(i, "Epot_ave", Epot)  

    # Average total energy
    saver.save_scalar(i, "Etot_ave", Etot)  

    # Fluctuation of average kinetic energy
    saver.save_scalar(i, "dEkin_ave", dEkin)  

    # Fluctuation of average potential energy
    saver.save_scalar(i, "dEpot_ave", dEpot)  

    # Fluctuation average total energy
    saver.save_scalar(i, "dEtot_ave", dEtot)  



def save_hdf5_2D(saver, i, states):
    """
    saver - can be either hdf5_saver or mem_saver

    """


    # Trajectory-resolved instantaneous adiabatic states
    # Format: saver.add_dataset("states", (_nsteps, _ntraj), "I")        
    ntraj = len(states)
    for itraj in range(ntraj):
        saver.save_multi_scalar(i, itraj, "states", states[itraj])




def save_hdf5_3D(saver, i, pops, dm_adi, dm_dia, q, p, Cadi, Cdia):
    """
    saver - can be either hdf5_saver or mem_saver

    """

    # Average adiabatic SH populations
    # Format: saver.add_dataset("SH_pop", (_nsteps, _nadi, 1), "R") 
    saver.save_matrix(i, "SH_pop", pops) 


    # Average adiabatic density matrices
    # Format: saver.add_dataset("D_adi", (_nsteps, _nadi, _nadi), "C") 
    saver.save_matrix(i, "D_adi", dm_adi) 

    # Average diabatic density matrices
    # Format: saver.add_dataset("D_dia", (_nsteps, _ndia, _ndia), "C") 
    saver.save_matrix(i, "D_dia", dm_dia) 


    # Trajectory-resolved coordinates
    # Format: saver.add_dataset("q", (_nsteps, _ntraj, _dof), "R") 
    saver.save_matrix(i, "q", q.T()) 

    # Trajectory-resolved momenta
    # Format: saver.add_dataset("p", (_nsteps, _ntraj, _dof), "R") 
    saver.save_matrix(i, "p", p.T()) 

    # Trajectory-resolved adiabatic TD-SE amplitudes
    # Format: saver.add_dataset("C_adi", (_nsteps, _ntraj, _nadi), "C") 
    saver.save_matrix(i, "Cadi", Cadi.T()) 

    # Trajectory-resolved diabatic TD-SE amplitudes
    # Format: saver.add_dataset("C_dia", (_nsteps, _ntraj, _ndia), "C") 
    saver.save_matrix(i, "Cdia", Cdia.T()) 



def save_hdf5_4D(saver, i, tr, hvib_adi, hvib_dia, St, U, projector):
    """
    saver - can be either hdf5_saver or mem_saver

    """

    # Trajectory-resolved vibronic Hamiltoninans in the adiabatic representation
    # Format: saver.add_dataset("hvib_adi", (_nsteps, _ntraj, _nadi, _nadi), "C") 
    saver.save_multi_matrix(i, tr, "hvib_adi", hvib_adi) 


    # Trajectory-resolved vibronic Hamiltoninans in the diabatic representation
    # Format: saver.add_dataset("hvib_dia", (_nsteps, _ntraj, _ndia, _ndia), "C") 
    saver.save_multi_matrix(i, tr, "hvib_dia", hvib_dia) 

    # Trajectory-resolved time-overlaps of the adiabatic states
    # Format: saver.add_dataset("St", (_nsteps, _ntraj, _nadi, _nadi), "C") 
    saver.save_multi_matrix(i, tr, "St", St) 

    # Trajectory-resolved diabatic-to-adiabatic transformation matrices 
    # Format: saver.add_dataset("basis_transform", (_nsteps, _ntraj, _ndia, _nadi), "C") 
    saver.save_multi_matrix(i, tr, "basis_transform", U) 

    # Trajectory-resolved projector matrices (from the raw adiabatic to consistent adiabatic)
    # Format: saver.add_dataset("projector", (_nsteps, _ntraj, _nadi, _nadi), "C") 
    saver.save_multi_matrix(i, tr, "projector", projector) 



#===================== HEOM output ====================


def heom_init_hdf5(saver, hdf5_output_level, _nsteps, _nquant):

    if hdf5_output_level>=1:

        # Time axis (integer steps)
        saver.add_dataset("timestep", (_nsteps,) , "I")  

        # Time axis
        saver.add_dataset("time", (_nsteps,) , "R")  
        

    if hdf5_output_level>=3:

        # System's density matrix
        saver.add_dataset("denmat", (_nsteps, _nquant, _nquant), "C") 



def heom_save_hdf5_1D(saver, i, dt):
    # Timestep 
    saver.save_scalar(i, "timestep", i) 

    # Actual time
    saver.save_scalar(i, "time", dt*i)  



def heom_save_hdf5_3D(saver, i, denmat):
    # Average adiabatic density matrices
    # Format: saver.add_dataset("denmat", (_nsteps, _nquant, _nquant), "C") 
    saver.save_matrix(i, "denmat", denmat) 




#===================== Exact calculations output ====================

def exact_init_hdf5(saver, hdf5_output_level, _nsteps, _ndof, _nstates, _ngrid):


    if hdf5_output_level>=1:

        # Time axis (integer steps)
        saver.add_dataset("timestep", (_nsteps,) , "I")  

        # Time axis
        saver.add_dataset("time", (_nsteps,) , "R")  
        
        # Kinetic energy in diabatic representation
        saver.add_dataset("Ekin_dia", (_nsteps,) , "R")  

        # Kinetic energy in adiabatic representation
        saver.add_dataset("Ekin_adi", (_nsteps,) , "R")  

        # Potential energy in diabatic representation
        saver.add_dataset("Epot_dia", (_nsteps,) , "R")  

        # Potential energy in adiabatic representation
        saver.add_dataset("Epot_adi", (_nsteps,) , "R")  

        # Total energy in diabatic representation
        saver.add_dataset("Etot_dia", (_nsteps,) , "R")  

        # Total energy in adiabatic representation
        saver.add_dataset("Etot_adi", (_nsteps,) , "R")  

        # Wavefunction norm in diabatic representation
        saver.add_dataset("norm_dia", (_nsteps,) , "R")  

        # Wavefunction norm in adiabatic representation
        saver.add_dataset("norm_adi", (_nsteps,) , "R")  


    if hdf5_output_level>=2:

        # Diabatic populations
        saver.add_dataset("pop_dia", (_nsteps, _nstates, 1), "R") 

        # Adiabatic populations
        saver.add_dataset("pop_adi", (_nsteps, _nstates, 1), "R") 


        # All coordinates computed in diabatic rep
        saver.add_dataset("q_dia", (_nsteps, _ndof, 1), "C") 

        # All coordinates computed in adiabatic rep
        saver.add_dataset("q_adi", (_nsteps, _ndof, 1), "C") 

        # All momenta computed in diabatic rep
        saver.add_dataset("p_dia", (_nsteps, _ndof, 1), "C") 

        # All momenta computed in adiabatic rep
        saver.add_dataset("p_adi", (_nsteps, _ndof, 1), "C") 


        # Higher moments computed in diabatic rep
        saver.add_dataset("q2_dia", (_nsteps, _ndof, 1), "C") 

        # Higher moments computed in adiabatic rep
        saver.add_dataset("q2_adi", (_nsteps, _ndof, 1), "C") 

        # Higher moments computed in diabatic rep
        saver.add_dataset("p2_dia", (_nsteps, _ndof, 1), "C") 

        # Higher moments computed in adiabatic rep
        saver.add_dataset("p2_adi", (_nsteps, _ndof, 1), "C") 




    if hdf5_output_level>=3:

        # Density matrix computed in diabatic rep
        saver.add_dataset("denmat_dia", (_nsteps, _nstates, _nstates), "C") 

        # Density matrix computed in adiabatic rep
        saver.add_dataset("denmat_adi", (_nsteps, _nstates, _nstates), "C") 


    if hdf5_output_level>=4:

        # Wavefunction in diabatic rep
        saver.add_dataset("PSI_dia", (_nsteps, _ngrid, _nstates, 1), "C") 

        # Wavefunction in adiabatic rep
        saver.add_dataset("PSI_adi", (_nsteps, _ngrid, _nstates, 1), "C") 

        # Reciprocal wavefunction in diabatic rep
        saver.add_dataset("reciPSI_dia", (_nsteps, _ngrid, _nstates, 1), "C") 

        # Reciprocal wavefunction in adiabatic rep
        saver.add_dataset("reciPSI_adi", (_nsteps, _ngrid, _nstates, 1), "C") 



def exact_init_custom_hdf5(saver, _nsteps, _ncustom_pops, _nstates):

    # Custom populations indx
    saver.add_dataset("custom_pops", (_nsteps, _ncustom_pops, _nstates, 1), "R") 


