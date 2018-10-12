#***********************************************************
# * Copyright (C) 2017-2018 Brendan A. Smith and Alexey V. Akimov
# * This file is distributed under the terms of the
# * GNU General Public License as published by the
# * Free Software Foundation; either version 3 of the
# * License, or (at your option) any later version.
# * http://www.gnu.org/copyleft/gpl.txt
#***********************************************************/
import os
import sys
import time
import math

# Fisrt, we add the location of the library to test to the PYTHON path
if sys.platform=="cygwin":
    from cyglibra_core import *
elif sys.platform=="linux" or sys.platform=="linux2":
    from liblibra_core import *
from libra_py.workflows.pyxaid2 import *

# Example of usage
opt = 1
scl1 = 2.0*13.60569253 # Ha to eV
scl2 = 1000.0 # some scaling to get plottable data
tmin = 0
tmax = 2

# Energy, couplings and H' in space of orbital indexes
excitation_spectrum.ham_map("res/0_Ham_",   tmin,tmax,"_re" ,opt,scl1,"spectr/ave_Ham_re.dat")
excitation_spectrum.ham_map("res/0_Ham_",   tmin,tmax,"_im" ,opt,scl1,"spectr/ave_Ham_im.dat")


HOMO = 21 # Index begins at 1
minE = 0.0
maxE = 10.0
dE = 0.05

#excitation_spectrum.
[exE, exI] = excitation_spectrum.calculate("res/0_Ham_","_re","res/0_Hprime_","x_im",tmin,tmax,opt,scl1,scl2,"spectr/ab_spectrx.dat",HOMO,minE,maxE,dE)
[eyE, eyI] = excitation_spectrum.calculate("res/0_Ham_","_re","res/0_Hprime_","y_im",tmin,tmax,opt,scl1,scl2,"spectr/ab_spectry.dat",HOMO,minE,maxE,dE)
[ezE, ezI] = excitation_spectrum.calculate("res/0_Ham_","_re","res/0_Hprime_","z_im",tmin,tmax,opt,scl1,scl2,"spectr/ab_spectrz.dat",HOMO,minE,maxE,dE)


