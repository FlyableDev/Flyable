#include "Python.h"

double __flyable__runtime__ceil(double x);
int __flyable__runtime__comb(int n, int k);
double __flyable__runtime__copysign(double x, double y);
double __flyable__runtime__fabs(double x);
int __flyable__runtime__factorial(int x);
double __flyable__runtime__floor(double x);
double __flyable__runtime__fmod(double x, double y);
void __flyable__runtime__frexp(double x,PyObject* array); //returns a tuple with a float and an int
//fsum to implement in Python
int __flyable__runtime__gcd(int a, int b); //to implement
int __flyable__runtime__isclose(double a, double b, double rel_tol, double abs_tol);
int __flyable__runtime__isfinite(double x);
int __flyable__runtime__isinf(double x);
int __flyable__runtime__isnan(double x);
//isqrt can be implemented in Python (see algorithm https://github.com/python/cpython/blob/master/Modules/mathmodule.c)
double __flyable__runtime__ldexp(double x, int i);
void __flyable__runtime__modf(double x,PyObject* array); //returns a tuple with two floats
int __flyable__runtime__perm(int n, int k);
//prod to implement in Python
double __flyable__runtime__remainder(double x, double y);
double __flyable__runtime__trunc(double x); //to implement
double __flyable__runtime__exp(double x);
double __flyable__runtime__expm1(double x);
double __flyable__runtime__log(double x, double base);
double __flyable__runtime__log1p(double x);
double __flyable__runtime__log2(double x);
double __flyable__runtime__log10(double x);
double __flyable__runtime__pow(double x, double y);
double __flyable__runtime__sqrt(double x);
double __flyable__runtime__acos(double x);
double __flyable__runtime__asin(double x);
double __flyable__runtime__atan(double x);
double __flyable__runtime__atan2(double y, double x);
double __flyable__runtime__cos(double x);
double __flyable__runtime__dist(double p, double q); //iterate on the elements of the coordinates
double __flyable__runtime__hypot(double x); //iterate on the elements of the coordinates
double __flyable__runtime__sin(double x);
double __flyable__runtime__tan(double x);
double __flyable__runtime__degrees(double x);
double __flyable__runtime__radians(double x);
double __flyable__runtime__acosh(double x);
double __flyable__runtime__asinh(double x);
double __flyable__runtime__atanh(double x);
double __flyable__runtime__cosh(double x);
double __flyable__runtime__sinh(double x);
double __flyable__runtime__tanh(double x);
double __flyable__runtime__erf(double x);
double __flyable__runtime__erfc(double x);
double __flyable__runtime__gamma(double x);
double __flyable__runtime__lgamma(double x);

double __flyable__runtime__decimal(double x,int decimals);
