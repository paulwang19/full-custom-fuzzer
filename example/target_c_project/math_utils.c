#include "math_utils.h"

int factorial(int n)
{
    if (n < 0) {
        return -1;
    }
    if (n == 0 || n == 1) {
        return 1;
    }
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

int fibonacci(int n)
{
    if (n < 0) return -1;
    if (n == 0) return 0;
    if (n == 1) return 1;

    int a = 0, b = 1, c;
    for (int i = 2; i <= n; i++) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}

double power(double base, int exp)
{
    if (exp == 0) return 1.0;

    double result = 1.0;
    int negative = exp < 0;
    int e = ABS(exp);

    while (e > 0) {
        if (e % 2 == 1) {
            result *= base;
        }
        base = SQUARE(base);
        e /= 2;
    }
    return negative ? 1.0 / result : result;
}

int gcd(int a, int b)
{
    a = ABS(a);
    b = ABS(b);
    while (b != 0) {
        int t = b;
        b = a % b;
        a = t;
    }
    return a;
}
