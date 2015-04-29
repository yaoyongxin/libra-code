/*********************************************************************************
* Copyright (C) 2012 Alexey V. Akimov
*
* This file is distributed under the terms of the GNU General Public License
* as published by the Free Software Foundation, either version 2 of
* the License, or (at your option) any later version.
* See the file LICENSE in the root directory of this distribution
* or <http://www.gnu.org/licenses/>.
*
*********************************************************************************/

#ifndef RANDOM_H
#define RANDOM_H

#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <iostream>
#include <iomanip>
#include <vector>

using namespace std;

namespace libmmath{

class Random{

  int fact(int k);
  double Gamma(double a);
  void bin(vector<double>& in,double minx,double maxx,double dx,vector< pair<double,double> >& out);

  public:

  Random(){ ;; }
  ~Random(){ ;; }


  // Uniform distribution
  double uniform(double a,double b);   // the random number of the disctribution below
  double p_uniform(double a,double b); // how the distribution should look like

  // Exponential distribution
  double exponential(double lambda);
  double p_exp(double x,double lambda);

  // Normal (Gaussian) distribution
  double normal();
  double p_normal(double x);

  // Gamma distribution
  double gamma(double a);
  double p_gamma(double a,double x);

  // Beta distribution
  double beta(double a,double b);
  double p_beta(double x,double a,double b);

  // Poisson distribution
  int poiss(double lambda,double t);
  void poiss(double lambda,double maxT,double dt,vector< pair<double,int> >& out);
  int poiss1(double lambda);
  int poiss2(double lambda);
  double p_poiss(int k,double lambda); // how the distribution should look like

}; // class Random


}// namespace libmmath

#endif // RANDOM_H
