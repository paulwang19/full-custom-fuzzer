#ifndef MATH_UTILS_H
#define MATH_UTILS_H

/* 巨集函數 */
#define MAX(a, b)          ((a) > (b) ? (a) : (b))
#define MIN(a, b)          ((a) < (b) ? (a) : (b))
#define CLAMP(x, lo, hi)   (MIN(MAX((x), (lo)), (hi)))
#define SQUARE(x)          ((x) * (x))
#define ABS(x)             ((x) < 0 ? -(x) : (x))

int factorial(int n);
int fibonacci(int n);
double power(double base, int exp);
int gcd(int a, int b);

#endif /* MATH_UTILS_H */
