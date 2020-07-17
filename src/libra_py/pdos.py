#*********************************************************************************
#* Copyright (C) 2018-2019 Alexey V. Akimov
#*
#* This file is distributed under the terms of the GNU General Public License
#* as published by the Free Software Foundation, either version 2 of
#* the License, or (at your option) any later version.
#* See the file LICENSE in the root directory of this distribution
#* or <http://www.gnu.org/licenses/>.
#*
#*********************************************************************************/
"""
.. module:: pdos
   :platform: Unix, Windows
   :synopsis: 
       This module implements functions for computing Projected (Partial) 
       Densities of States (pDOS) from various outputs

.. moduleauthor:: Alexey V. Akimov

"""

import math
import os
import sys
if sys.platform=="cygwin":
    from cyglibra_core import *
elif sys.platform=="linux" or sys.platform=="linux2":
    from liblibra_core import *
from . import units
import numpy as np

def convolve(X0, Y0, dx0, dx, var):
    """
    This function convolves the original data with the Gaussian
    of a given width:  exp(- (x - x0)^2 / (2*var^2) )
    This also means the energy grid spacing may change (usually to a denser one)
    The difference in grid densities is defined by the multiplicative factor dx0/dx

    Args:
        X0 ( MATRIX(N0, 1) ): original X grid, N0 - the number of energy grid points
        Y0 ( MATRIX(N0, Nproj) ): original Y grids, Nproj - the number of projections
            to consider
        dx0 ( double ): original X grid spacing [in units of energy]
        dx ( double ): new X grid spacing [in units of energy]
        var ( double ): width of the Gaussians that broaden the original data [in units of energy]

    Returns:
        tuple: ( X, Y ), where:

            * X ( MATRIX(N, 1) ): new X grid, N - the new number of energy grid points (N*dx = N0*dx0)
            * Y ( MATRIX(N, Nproj) ): new Y grids, Nproj has the same meaning as in Y0

    """

    mult = int(dx0/dx)     # making grid mult times bigger
    print("multiplication factor is = ", mult)
    print("original grid spacing = ", dx0)
    print("new grid spacing = ", dx)
    print("gaussian variance = ", var)
        
    # Prepare arrays
    N0    = Y0.num_of_rows     # how many original grid points
    nproj = Y0.num_of_cols     # how many components
    N  = N0*mult               # how many new grid points

    X = MATRIX(N, 1)           # new X axis
    Y = MATRIX(N, nproj)       # new Y axes


    for i in range(0,N):
        X.set(i,0, X0.get(0,0) + i*dx)


    area = var*math.sqrt(2.0*math.pi)  # area under Gaussian of type exp( -(x - x0)^2 / 2*var^2 ) 
    alp = 0.5/(var**2)

    for j in range(0,nproj):  

        for i0 in range(0,N0):   # all initial grid points
            x0 = X0.get(i0, 0)
            y0 = Y0.get(i0, j)

            area0 = dx0*y0      # initial area
            w = area0/area

            for i in range(0,N):
                x = X.get(i, 0)
                Y.add(i,j, w*math.exp(-alp*(x0-x)**2))

    return X, Y




def QE_pdos(prefix, emin, emax, de, projections, Ef, outfile_prefix, do_convolve, de_new, var, nspin=1):
    """Computes various types of pDOS from the atomic state projections generated by the QE

    Args:
        prefix ( string ): a common prefix of the filenames for files containing the projection information
        emin ( double ): the minimal energy of the pDOS window [eV]
        emax ( double ): maximal energy of the pDOS window [eV]
        de ( double ): the original grid spacing of the pDOS [eV] (not necessarily the one used in pdos.in)
        projections ( list of lists of - see below): groups of atoms and types of projections.
            Each element of this list contains 3 sub-lists, whose intersection defines which files to use:
            e.g. projection = [["s","p"], [1,2,3], ["Cs", "Br"]] - means s and p orbitals of atoms 1, 2, and 3
            as long as any of these atoms are Cs or Br
        Ef ( double ): which energy use as the origin of energy scale (zero) in the output. Usually 
            the Fermi or LUMO energy
        outfile_prefix ( string ): the prefix of the output file that will contain the final projections
        do_convolve ( Bool ): the flag telling whether we want to convolve the original data with the
            Gaussian envelope. The convolution is done with :func:`convolve`
        de_new ( double ): the new energy grid spacing [eV], in effect only if do_convolve == True
        var ( double ): standard deviation of the Gaussian [eV] with which we do a convolution, 
            in effect only if do_convolve == True
        nspin ( int): specifies which nspin was used in the electronic structure calculation.
                      nspin = 1      
                      nspin = 2
                      nspin = 4

    Returns:
        tuple: ( E, pDOSa ), where:

            * E ( MATRIX(N, 1) ): new energy grid, N - the new number of energy grid points
            * pDOSa ( MATRIX(N, Nproj) ): new Y grids, Nproj - len(projections) the number of projections we are interested in
            * if spin = 2, returns pDOSb for beta spin-orbtials as well
            * if spin = 4, returns just the pDOSa (pDOSb = None), but the orbitals now mixed spin states 
    """

    if nspin not in [1,2,4]:
        print ("Error: The value of nspin must be either 1, 2, or 4")
        print ("nspin = 1: Spin-unpolarized")
        print ("nspin = 2: Spin-polarized")
        print ("nspin = 4: Spin-non-colinear")
        print ("Exiting Now ...")
        sys.exit(0)

    #============= Dimensions  =================

    nproj = len(projections)                # number of projections
    N = int(math.floor((emax - emin)/de))+1 # number of the gridpoints

    en   = MATRIX(N, 1)      # energy of the grid points
    dosa = MATRIX(N, nproj)  # Matrix for alpha spin-orbitals dos.get(i,proj) - dos for level i projected on projection proj
    dosb = MATRIX(N, nproj)  # Matrix for beta  spin-orbitals
    for i in range(0,N):
        en.set(i, 0, emin + i*de - Ef)

        #============= Data gathering  =================

    for proj in projections:  # loop over all projection
        ang_mom = proj[0]
        atoms = proj[1]
        elements = proj[2]

        proj_indx = projections.index(proj)

        for a in atoms: # open files for atoms with given indices (indexing from 1)
            for symb in ang_mom:  # for given angular momentum labels
                for wfc in range(0,5): # Specify max wfc type index - usually no more than 3, 5 - should be more than enough  
                    for Elt in elements: # for given atom names

                        if nspin == 4:
                            for k in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]: # total angular momentum label
                                filename = prefix+str(a)+"("+Elt+")_wfc#"+str(wfc)+"("+symb+"_j"+str(k)+")"
                                if os.path.exists(filename):

                                    fa = open(filename,"r")
                                    B = fa.readlines()
                                    check = B[0].split()
                                    fa.close()

                                    for lin in B[1:]:  # read all lines, except for the header
                                        tmp = lin.split()
                                        e = float(tmp[0])
                                        if e<emin or e>emax:
                                            pass
                                        else:
                                            state_indx = int(math.floor((e - emin)/de))
                                            dosa.add(state_indx, proj_indx, float(tmp[1]))

                        else:

                            filename = prefix+str(a)+"("+Elt+")_wfc#"+str(wfc)+"("+symb+")"  # file 
                            if os.path.exists(filename):

                                fa = open(filename,"r")
                                B = fa.readlines()
                                check = B[0].split()
                                fa.close()

                                for lin in B[1:]:  # read all lines, except for the header
                                    tmp = lin.split()

                                    e = float(tmp[0])
                                    if e<emin or e>emax:
                                        pass
                                    else:
                                        state_indx = int(math.floor((e - emin)/de))
                                        dosa.add(state_indx, proj_indx, float(tmp[1]))
                                        if nspin == 2 and check[4] == "ldosdw(E)":
                                            dosb.add(state_indx, proj_indx, float(tmp[2]))

    #============= Optional convolution =================

    E, pDOSa, pDOSb = en, dosa, dosb
    if do_convolve==True:
        E, pDOSa = convolve(en, dosa, de, de_new, var)
        E, pDOSb = convolve(en, dosb, de, de_new, var)

    #============= Print out ==================
    f2a = open(outfile_prefix+"_alp.txt","w"); f2a.close()
    f2b = open(outfile_prefix+"_bet.txt","w"); f2b.close()

    N = E.num_of_rows
    for i in range(0,N):  # loop over grid points
        line = str(E.get(i,0))+"   "
        tot = 0.0
        for j in range(0,nproj):
            tot = tot + pDOSa.get(i,j)
            line = line + str(pDOSa.get(i,j))+"   "
        line = line + str(tot)+"\n"
        f2a = open(outfile_prefix+"_alp.txt","a")
        f2a.write(line)
        f2a.close()

    for i in range(0,N):  # loop over grid points
        line = str(E.get(i,0))+"   "
        tot = 0.0
        for j in range(0,nproj):
            tot = tot + pDOSb.get(i,j)
            line = line + str(pDOSb.get(i,j))+"   "
        line = line + str(tot)+"\n"
        f2b = open(outfile_prefix+"_bet.txt","a")
        f2b.write(line)
        f2b.close()

    if nspin == 2:
        return E, pDOSa, pDOSb
    else:
        pDOSb = MATRIX(pDOSa)
        return E, pDOSa, pDOSb



def libra_pdos(_emin, _emax, _de, projections, prefix, outfile, Nel, do_convolve, _de_new, _var):
    """
    
    Args:
    
        * _emin ( double ): minimal energy of the spectrum [eV]
        
        * _emax ( double ): maximal energy of the spectrum [eV]
        
        * _de ( double ): original energy grid spacing  [eV]
        
        * projections ( list ):  groups of atoms and types of projections 
            e.g. projections = [["s",[1,2,3]], ["p",[1,2,3]], ... 
            
            Possible projections (examples)
            proj = [["s",range(0,360)],["p",range(0,360)],["d",range(0,360)]]
            proj = [["s",range(0,1)],["p",range(0,1)],["d",range(0,1)]]
            proj = [["tot",range(0,112)]]

            
        * prefix ( string ): the common prefix of the files containing the projection information
        
        * outfile ( string ): the name of the file that will contain the computed pDOSs
        
        * Nel ( int ): the number of electrons, to compute the Fermi energy
            
        * _de_new ( double ): new energy grid (for convolved) spacing  [eV]
        
        * _var ( double ): the width of the Gaussian used to broaden each energy grid point [eV] 
        
        
    # Example: of call - for Si QD
    # Si
    #main(-35.0, 35.0, 0.1,[["tot",range(0,103)]],"_alpha_wfc_atom","dos_proj.txt",238)   

    """
    
    # Internally, we work in a.u. (Ha)
    emin = _emin * units.ev2Ha
    emax = _emax * units.ev2Ha
    de = _de * units.ev2Ha
    de_new = _de_new * units.ev2Ha
    var = _var * units.ev2Ha

    # Determine dimensionality and prepare arrays
    nproj = len(projections)                # number of projections
    N = int(math.floor((emax - emin)/de))+1 # number of the gridpoints

    en0 = []
    dosa = MATRIX(N, nproj)  # Matrix for alpha spin-orbitals dos.get(i,proj) - dos for level i projected on projection proj
    dosb = MATRIX(N, nproj)  # Matrix for beta  spin-orbitals
    
    
    for proj in projections:  # loop over all projection
        ang_mom = proj[0]
        atoms = proj[1]

        proj_indx = projections.index(proj)
                                            
        for a in atoms: # open files for all atoms in given group
            fa = open(prefix+str(a),"r")
            B = fa.readlines()
            fa.close()

            for lin in B[1:-4]:  # read all lines
                tmp = lin.split()
                 
                e = float(tmp[0]) # energy in Ha
                if a==0:
                    en0.append(e)  
                
                x = 0.0
                if ang_mom=="s":
                    x = float(tmp[2])
                elif ang_mom=="p":
                    x = float(tmp[3])
                elif ang_mom=="d":
                    x = float(tmp[4])
                elif ang_mom=="tot":
                    x = float(tmp[1])
                else:
                    x = 0.0

                if e<emin or e>emax:
                    pass
                else:
                    grid_indx = int(math.floor((e - emin)/de))  # grid point
                    dosa.add(grid_indx, proj_indx, x)
                    dosb.add(grid_indx, proj_indx, x)


    
    etol = 1e-10
    kT = 0.1 * units.ev2Ha # some reasonable parameters
    Ef = fermi_energy(en0, Nel,2.0, kT, etol)  # Fermi energy in Ha
    

    en = MATRIX(N,1)
    for i in range(0,N):
        en.set(i, 0, emin + i*de - Ef)

    
    E = None                
    if do_convolve==True:
        E, pDOSa = convolve(en, dosa, de, de_new, var)
        #E, pDOSb = convolve(en0, dosb, de, de_new, var)
    else:
        E = MATRIX(dosa)
            
    # Convert the energy axis back to eV 
    E *= (1.0/units.ev2Ha)

        
    f2 = open(outfile,"w")
    f2.write("Ef = %5.3f eV\n" % (Ef / units.ev2Ha) )
    f2.close()

    
    res = np.zeros( (N, nproj+2), dtype=float)
    
    # Now compute projections
    for i in range(0,N):  # loop energy grid

        res[i, 0] = E.get(i,0) 
        line = str(E.get(i,0))+"   "

        tot = 0.0
        for j in range(0,nproj):
            res[i, j+1] = pDOSa.get(i,j)
            tot = tot + pDOSa.get(i,j)
            line = line + str(pDOSa.get(i,j))+"   "
            
        res[i, nproj+1] = tot
        line = line + str(tot)+"\n"

        f2 = open(outfile,"a")
        f2.write(line)
        f2.close()
    

    return res
    
        