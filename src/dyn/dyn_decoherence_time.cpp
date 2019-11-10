/*********************************************************************************
* Copyright (C) 2018-2019 Alexey V. Akimov
*
* This file is distributed under the terms of the GNU General Public License
* as published by the Free Software Foundation, either version 2 of
* the License, or (at your option) any later version.
* See the file LICENSE in the root directory of this distribution
* or <http://www.gnu.org/licenses/>.
*
*********************************************************************************/
/**
  \file dyn_decoherence_time.cpp
  \brief The file implements the methods to compute dephasing rates and decoherence intervals
    
*/

#include "Surface_Hopping.h"
#include "Energy_and_Forces.h"

/// liblibra namespace
namespace liblibra{

/// libdyn namespace
namespace libdyn{


MATRIX edc_rates(CMATRIX& Hvib, double Ekin, double C_param, double eps_param){
/**
    This function computes the decoherence rates matrix used in the 
    energy-based decoherence scheme of Granucci-Persico and Truhlar
    Reference: Granucci, G.; Persico, M. J. Chem. Phys. 2007, 126, 134114
    
    \param[in]       Hvib  [ CMATRIX ] Vibronic Hamiltonian matrix. 
    \param[in]        Ekin [ float ] The classical kinetic energy of nuclei. Units = Ha
    \param[in]     C_param [ float ] The method parameter, typically set to 1.0 Ha
    \param[in]   eps_param [ float ] The method parameter, typically set to 0.1 Ha

*/

  int i,j;
  int nst = Hvib.n_cols;
  MATRIX decoh_rates(nst, nst);

  for(i=0; i<nst; i++){
    for(j=0; j<nst; j++){

      double itau = fabs( Hvib.get(i,i).real() - Hvib.get(j,j).real()) / ( C_param + (eps_param/Ekin) );
      decoh_rates.set(i,j, itau);

    }
  }

  return decoh_rates;

}


vector<MATRIX> edc_rates(vector<CMATRIX>& Hvib, vector<double>& Ekin, double C_param, double eps_param){

  int ntraj = Hvib.size();
  int nst = Hvib[0].n_cols;

  if(Ekin.size()!=ntraj){
    cout<<"ERROR in edc_rates: the sizes of the input variables Hvib and Ekin are inconsistent\n";
    cout<<"Hvib.size() = "<<Hvib.size()<<"\n";
    cout<<"Ekin.size() = "<<Ekin.size()<<"\n";
    cout<<"exiting...\n";
    exit(0);
  }

  vector<MATRIX> res(ntraj, MATRIX(nst, nst));
  for(int traj=0; traj<ntraj; traj++){
    res[traj] = edc_rates(Hvib[traj], Ekin[traj], C_param, eps_param);
  }

  return res;

}


void dephasing_informed_correction(MATRIX& decoh_rates, CMATRIX& Hvib, MATRIX& ave_gaps){
/**
    This function computes the corrected dephasing rates  
    The correction is based on the instnataneous energy levels and on the average
    of absolute values of the energy gaps

    Reference: Sifain, A. E.; Wang, L.; Teritiak, S.; Prezhdo, O. V. J. Chem. Phys. 2019, 150, 194104
    
    \param[in, out]  decoh_rates [ MATRIX ] uncorrected decoherence rates [units: a.u.t.^-1]
    \param[in]             Hvib  [ CMATRIX ] Instantaneous vibronic Hamiltonian [units: Ha]
    \param[in]          ave_gaps [ MATRIX ] time-averaged module of the energy level gaps: <|E_i - E_j|>  [units: Ha]

*/

  int i,j;
  int nst = Hvib.n_cols;

  for(i=0; i<nst; i++){
    for(j=0; j<nst; j++){

      double dE_ij = fabs( Hvib.get(i,i).real() - Hvib.get(j,j).real());

      if(ave_gaps.get(i,j) > 0.0){

        decoh_rates.scale(i,j, dE_ij / ave_gaps.get(i,j) );

      }
      else{

       decoh_rates.set(i,j, 1e+25);

      }

    }// for j
  }// for i

}


void dephasing_informed_correction(vector<MATRIX>& decoh_rates, vector<CMATRIX>& Hvib, MATRIX& ave_gaps){

  int ntraj = Hvib.size();

  if(decoh_rates.size()!=ntraj){
    cout<<"ERROR in dephasing_informed_correction: the sizes of the input variables \
    decoh_rates and Hvib are inconsistent\n";
    cout<<"decoh_rates.size() = "<<decoh_rates.size()<<"\n";
    cout<<"Hvib.size() = "<<Hvib.size()<<"\n";
    cout<<"exiting...\n";
    exit(0);
  }

  for(int traj=0; traj<ntraj; traj++){

    dephasing_informed_correction(decoh_rates[traj], Hvib[traj], ave_gaps);

  }

}



MATRIX coherence_intervals(CMATRIX& Coeff, MATRIX& rates){
/**
  This function computes the time-dependent (and population-dependent) coherence intervals
  (the time after which different states should experience a decoherence event)
  as described by Eq. 11 in:
  Jaeger, H. M.; Fischer, S.; Prezhdo, O. V. Decoherence-Induced Surface Hopping. J. Chem. Phys. 2012, 137, 22A545.

  1/tau_i  (t) =  sum_(j!=i)^nstates {  rho_ii(t) * rate_ij }


  \param[in] Coeff Amplitudes of the electronic states
  \param[in] rates A matrix containing the decoherence rates (inverse of the
  decoherence time for each given pair of states)

  Returns: A matrix of the coherence intervals for each state

*/
  int nstates = Coeff.n_rows; 

  CMATRIX denmat(nstates, nstates);   
  //denmat = (Coeff * Coeff.H() ).conj();
  denmat = Coeff * Coeff.H();

  MATRIX tau_m(nstates, 1); tau_m *= 0.0;
  

  for(int i=0;i<nstates;i++){

    double summ = 0.0;
    for(int j=0;j<nstates;j++){

      if(j!=i){
        summ += denmat.get(j,j).real() * rates.get(i,j); 
      }// if

    }// for j

    if(summ>0.0){   tau_m.set(i, 1.0/summ); }
    else        {   tau_m.set(i, 1.0e+25);  } // infinite coherence interval
    
     
  }// for i

//  delete denmat;

  return tau_m;
}





}// namespace libdyn
}// liblibra

