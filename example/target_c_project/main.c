#include <stdio.h>
#include "math_utils.h"
#include "string_utils.h"
#include "io/file_io.h"

#define BUFFER_SIZE 64
#define PRINT_RESULT(label, val) printf("  %-20s = %d\n", label, val)

static void demo_math(void)
{
    printf("=== Math Utils ===\n");
    for (int i = 0; i <= 10; i++) {
        PRINT_RESULT("factorial", factorial(i));
    }

    printf("\nFibonacci sequence:\n");
    for (int i = 0; i < 10; i++) {
        printf("  fib(%d) = %d\n", i, fibonacci(i));
    }

    printf("\npower / gcd:\n");
    printf("  power(2, 10)  = %.0f\n", power(2, 10));
    printf("  power(3, -2)  = %.4f\n", power(3, -2));
    printf("  gcd(48, 18)   = %d\n",   gcd(48, 18));
    printf("  CLAMP(15,0,10)= %d\n",   CLAMP(15, 0, 10));
}

static void demo_string(void)
{
    printf("\n=== String Utils ===\n");

    char buf[BUFFER_SIZE] = "Hello, World!";
    printf("  original : %s\n", buf);

    str_to_upper(buf);
    printf("  to_upper : %s\n", buf);

    str_to_lower(buf);
    printf("  to_lower : %s\n", buf);

    printf("  strlen   : %zu\n", my_strlen(buf));
    printf("  count 'l': %d\n",  str_count_char(buf, 'l'));

    char dst[BUFFER_SIZE];
    my_strcpy(dst, buf);
    printf("  strcpy   : %s\n", dst);

    printf("  strcmp   : %d\n", my_strcmp(buf, dst));
}

static void demo_file_io(void)
{
    const char *tmp = "/tmp/sample_c_demo.txt";
    printf("\n=== File I/O ===\n");

    write_text_file(tmp, "line one\nline two\nline three\n");

    char line[64];
    if (read_first_line(tmp, line, sizeof(line)) == 0)
        printf("  first line : %s\n", line);

    printf("  line count : %d\n", count_lines(tmp));
}

int main(void)
{
    demo_math();
    demo_string();
    demo_file_io();
    return 0;
}
