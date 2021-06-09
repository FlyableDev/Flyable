#include <math.h>
#include "math.h"


const double pi = 3.141592653589793238462643383279502884197;
const double tau = 6.283185307179586476925286766559005768394;
const double logpi = 1.144729885849400174143427351353058711647;
const double sqrtpi = 1.772453850905516027298167483341145182798;
const double e = 2.718281828459045235360287471352662497757;


double __flyable__runtime__ceil(double x)
{
    return ceil(x);
}


int __flyable__runtime__comb(int n, int k)
{

    if (n == 0)
    {
        return 0;
    }

    if (k == 0)
    {
        return 0;
    }

    if (n < 0)
    {
        //PyExc_ValueError, "n must be a non-negative integer"
        return 0;
    }

    if (k < 0)
    {
        //PyExc_ValueError, "k must be a non-negative integer"
        return 0;
    }

    int temp = n - k;
    if (temp < 0)
    {
        return 0;
    }

    //k = min(k, temp);

    //Overflow to manage

    //Don't get the matematical expression with CPython implementation... here's a temporary implementation
    return __flyable__runtime__factorial(n) / (__flyable__runtime__factorial(k) * __flyable__runtime__factorial(n - k));
}


double __flyable__runtime__copysign(double x, double y)
{
    return copysign(x, y);
}


double __flyable__runtime__fabs(double x)
{
    return fabs(x);
}


//CPython implementation is more performant, see how it is done
int __flyable__runtime__factorial(int x)
{

    if (x < 0)
    {
        //raise error
        ;
    }

    if (x == 0)
    {
        return 1;
    }

    int result = 1;
    int i;
    for (i = 2; i <= x; i++){
        result *= i;
    }

    return result;
}


double __flyable__runtime__floor(double x)
{
    return floor(x);
}


double __flyable__runtime__fmod(double x, double y)
{
    return fmod(x, y);
}


//returns a tuple with a float and an int
void __flyable__runtime__frexp(double x,PyObject* array)
{
    int i;
    double rx;
    if (isinf(x) || isnan(x))
    {
        rx = x;
        i = 0;
    }
    else {
        rx = frexp(x, &i);
    }

    /*FlyFloat* arrayData = array->content;
    arrayData[0] = (float) i;
    arrayData[1] = rx;*/
}

int __flyable__runtime__isclose(double a, double b, double rel_tol, double abs_tol)
{
    double diff = 0.0;

    if (rel_tol < 0.0 || abs_tol < 0.0 ) {
        //raise PyExc_ValueError, "tolerances must be non-negative"
        return -1;
    }

    if ( a == b ) {
        return 1;
    }

   if (isinf(a) || isinf(b)) {
        return 0;
    }

    diff = fabs(b - a);

    return (((diff <= fabs(rel_tol * b)) ||
             (diff <= fabs(rel_tol * a))) ||
            (diff <= abs_tol));
}

int __flyable__runtime__isfinite(double x)
{
    return isfinite(x);
}


int __flyable__runtime__isinf(double x)
{
    return isinf(x);
}


int __flyable__runtime__isnan(double x)
{
    return isnan(x);
}


double __flyable__runtime__ldexp(double x, int i)
{
    //check for underflow, overflow, x is finite and if i is an int
    return ldexp(x, i);
}


void __flyable__runtime__modf(double x,PyObject* array)
{
    double xres,y;
    xres = modf(x, &y);
    /*FlyFloat* arrayContent = array->content;
    arrayContent[0] = xres;
    arrayContent[1] = y;*/
}


int __flyable__runtime__perm(int n, int k)
{
    if (n == 0 || k == 0)
    {
        return 0;
    }

    if (n < 0)
    {
        //PyExc_ValueError, "n must be a non-negative integer"
        return 0;
    }

    if (k < 0)
    {
        //PyExc_ValueError, "k must be a non-negative integer"
        return 0;
    }

    int temp = n - k;
    if (temp < 0)
    {
        return 0;
    }

    //Overflow to manage?

    int i;
    int result = 1;
    for (i = temp + 1; i <= n; i++)
    {
        result *= i;
    }

    return result;
}


double __flyable__runtime__remainder(double x, double y)
{
    /* Deal with most common case first. */
    if (isfinite(x) && isfinite(y)) {
        double absx, absy, c, m, r;

        if (y == 0.0) {
            return NAN;
        }

        absx = fabs(x);
        absy = fabs(y);
        m = fmod(absx, absy);

        c = absy - m;
        if (m < c) {
            r = m;
        }
        else if (m > c) {
            r = -c;
        }
        else {
            r = m - 2.0 * fmod(0.5 * (absx - m), absy);
        }
        return copysign(1.0, x) * r;
    }

    /* Special values. */
    if (isnan(x)) {
        return x;
    }
    if (isnan(y)) {
        return y;
    }
    if (isinf(x)) {
        return NAN;
    }

    return x;
}


double __flyable__runtime__exp(double x)
{
    return exp(x);
}


double __flyable__runtime__expm1(double x)
{
    return expm1(x);
}


double __flyable__runtime__log(double x, double base)
{
    return log(x) / log(base);
}


double __flyable__runtime__log1p(double x)
{
    return log1p(x);
}


double __flyable__runtime__log2(double x)
{
    return log2(x);
}


double __flyable__runtime__log10(double x)
{
    return log10(x);
}


double __flyable__runtime__pow(double x, double y)
{
 return pow(x, y);
}


double __flyable__runtime__sqrt(double x)
{
 return sqrt(x);
}


double __flyable__runtime__acos(double x)
{
    return acos(x);
}


double __flyable__runtime__asin(double x)
{
    return asin(x);
}


double __flyable__runtime__atan(double x)
{
    return atan(x);
}


double __flyable__runtime__atan2(double y, double x)
{
    return atan2(y, x);
}


double __flyable__runtime__cos(double x)
{
    return cos(x);
}


double __flyable__runtime__sin(double x)
{
    return sin(x);
}


double __flyable__runtime__tan(double x)
{
    return tan(x);
}


double __flyable__runtime__degrees(double x)
{
    return x * 180.0 / pi;
}


double __flyable__runtime__radians(double x)
{
    return x * pi / 180.0;
}


double __flyable__runtime__acosh(double x)
{
    return acosh(x);
}


double __flyable__runtime__asinh(double x)
{
    return asinh(x);
}


double __flyable__runtime__atanh(double x)
{
    return atanh(x);
}


double __flyable__runtime__cosh(double x)
{
    return cosh(x);
}


double __flyable__runtime__sinh(double x)
{
    return sinh(x);
}


double __flyable__runtime__tanh(double x)
{
    return tanh(x);
}


double __flyable__runtime__erf(double x)
{
    return erf(x);
}


double __flyable__runtime__erfc(double x)
{
    return erfc(x);
}


double __flyable__runtime__gamma(double x)
{
    return tgamma(x);
}


double __flyable__runtime__lgamma(double x)
{
    return lgamma(x);
}


