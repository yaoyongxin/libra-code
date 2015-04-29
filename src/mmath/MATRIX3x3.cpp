#include "MATRIX3x3.h"
#include "VECTOR.h"

namespace libmmath{

// In this file we define only those members of the MATRIX3x3 
// class which depend on other classes, such as VECTOR, etc.
// Other members are included in class definition so they are inlined
// We also include here all big functions, which can not be inlined

//---------------------- Constructor ---------------------------------

MATRIX3x3::MATRIX3x3(const VECTOR& r1, const VECTOR& r2, const VECTOR& r3){
  xx = r1.x;  xy = r2.x;  xz = r3.x;
  yx = r1.y;  yy = r2.y;  yz = r3.y;
  zx = r1.z;  zy = r2.z;  zz = r3.z;
}

  
//------------------- Initializations ---------------------------------
void MATRIX3x3::init(VECTOR& r1, VECTOR& r2, VECTOR& r3){
  xx = r1.x;  xy = r2.x;  xz = r3.x;
  yx = r1.y;  yy = r2.y;  yz = r3.y;
  zx = r1.z;  zy = r2.z;  zz = r3.z;
}

void MATRIX3x3::init(const VECTOR& r1, const VECTOR& r2, const VECTOR& r3){
  xx = r1.x;  xy = r2.x;  xz = r3.x;
  yx = r1.y;  yy = r2.y;  yz = r3.y;
  zx = r1.z;  zy = r2.z;  zz = r3.z;
}

//------------------- Special matrices ---------------------------------

// Skew-symmetric matrix
void MATRIX3x3::skew(VECTOR v){
  xx = 0.0; xy =-v.z; xz = v.y;
  yx = v.z; yy = 0.0; yz =-v.x;
  zx =-v.y; zy = v.x; zz = 0.0;
}

void MATRIX3x3::Rotation(const VECTOR& u){
/*  This function initializes the matrix to a rotation matrix
    for rotation around the axis given by direction of the vector: (u/|u|)
    on amount given by norm of vector u: |u|.
    If the vector has a zero length - this will be an identity matrix
*/ 
  double umod,umod2;
  umod2 = u.x*u.x + u.y*u.y + u.z*u.z;
  if(umod2==0.0){
    xx = 1.0;  xy = 0.0;  xz = 0.0;
    yx = 0.0;  yy = 1.0;  yz = 0.0;
    zx = 0.0;  zy = 0.0;  zz = 1.0;
  }
  else{
    umod = sqrt(umod2);
    VECTOR n(u.x/umod, u.y/umod, u.z/umod);
    double cs,sn;
    cs = (1.0 - cos(umod));
    sn = sin(umod);

    /* 
    Here is efficient implementation of Rodrigues formula: 
    M = I + W * sin_psi + W*W*(1.0 - cos_psi)
    where I - identity matrix
                  | 0  -n.z  n.y |
    W = skew(n) = | n.z  0  -n.x |
                  |-n.y n.x  0   |
    */
    double x,y,z,_xy,_xz,_yz,x2,y2,z2;
    x  = n.x * sn;
    y  = n.y * sn;
    z  = n.z * sn;
    x2 = (n.x * n.x - 1.0) * cs;
    y2 = (n.y * n.y - 1.0) * cs;
    z2 = (n.z * n.z - 1.0) * cs;
    _xy = n.x * n.y * cs;
    _xz = n.x * n.z * cs;
    _yz = n.y * n.z * cs;

    xx = 1.0 + x2;  xy =-z   + _xy; xz = y   + _xz;
    yx = z   + _xy; yy = 1.0 + y2;  yz =-x   + _yz;
    zx =-y   + _xz; zy = x   + _yz; zz = 1.0 + z2;
        
  }// else 
}


//------------------ Basic matrix operations --------------------------
MATRIX3x3 MATRIX3x3::inverse(){
  VECTOR r1,r2,r3,g,g1,g2,g3;
  r1.x = xx;  r2.x = xy;  r3.x = xz;
  r1.y = yx;  r2.y = yy;  r3.y = yz;
  r1.z = zx;  r2.z = zy;  r3.z = zz;
  g.cross(r2,r3);    g1 = g/(r1*g);
  g.cross(r3,r1);    g2 = g/(r2*g);
  g.cross(r1,r2);    g3 = g/(r3*g);
  MATRIX3x3 m;
  m.xx = g1.x;  m.xy = g1.y;  m.xz = g1.z;
  m.yx = g2.x;  m.yy = g2.y;  m.yz = g2.z;
  m.zx = g3.x;  m.zy = g3.y;  m.zz = g3.z;
  return m;
}

void MATRIX3x3::eigen(MATRIX3x3& EVAL, MATRIX3x3& EVECT) {
  this->eigen(EVAL, EVECT,1e-30); 
}

void MATRIX3x3::eigen(MATRIX3x3& EVAL, MATRIX3x3& EVECT,double EPS) {
// This function corresponds to JACOBY_EIGEN member-function of MATRIX class
// Description: only for symmetric matrices!
// EVECT * EVAL  =  (*this) * EVECT

// EVAL * EVECT = EVECT * EVAL  =  M * EVECT
// V = P^T
// EVAL = V_M V_{M-1} ... V_0 * M * V_0^T * V_1^T ... V_M^T = Q^T * M * Q
// EVECT = Q = V_0^T * V_1^T ... V_M^T


  MATRIX3x3 V,temp;
  temp.init(*this);

  EVECT.identity();
  double eps;
  // Define convergence criteria.
  eps = temp.xy*temp.xy + temp.xz*temp.xz + temp.yx*temp.yx + temp.yz*temp.yz + temp.zx*temp.zx + temp.zy*temp.zy;

  int row,col;
  double  val, phi;

  while(eps>EPS){
    
    int opt = 0;
    double elem, max_elem;
    val = temp.xy; max_elem = fabs(val);  
    elem = fabs(temp.xz);
    if(elem>max_elem) {max_elem = elem; val = temp.xz; opt = 1;}
    elem = fabs(temp.yz);
    if(elem>max_elem) {max_elem = elem; val = temp.yz; opt = 2;}		   

    switch(opt){
      case 0: { phi = 0.5*atan(2.0*val/(temp.yy-temp.xx)); V.Rz(phi);  } break;
      case 1: { phi = 0.5*atan(2.0*val/(temp.zz-temp.xx)); V.Ry(-phi); } break; 
      case 2: { phi = 0.5*atan(2.0*val/(temp.zz-temp.yy)); V.Rx(phi);  } break;
    }

    temp = V*temp*V.T();
    EVECT = EVECT*V.T();
    eps = temp.xy*temp.xy + temp.xz*temp.xz + temp.yx*temp.yx + temp.yz*temp.yz + temp.zx*temp.zx + temp.zy*temp.zy;

  }
  EVAL = temp;

}

//------------------ Small functions on matrices ----------------------

void MATRIX3x3::get_vectors(VECTOR& r1,VECTOR& r2,VECTOR& r3){
  r1.x = xx;  r2.x = xy;  r3.x = xz;
  r1.y = yx;  r2.y = yy;  r3.y = yz;
  r1.z = zx;  r2.z = zy;  r3.z = zz;
}

void MATRIX3x3::tensor_product(VECTOR v1,VECTOR v2){
  xx = v1.x*v2.x;   xy = v1.x*v2.y;  xz = v1.x*v2.z;
  yx = v1.y*v2.x;   yy = v1.y*v2.y;  yz = v1.y*v2.z;
  zx = v1.z*v2.x;   zy = v1.z*v2.y;  zz = v1.z*v2.z;
}

}// libmmath
