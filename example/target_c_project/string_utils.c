#include "string_utils.h"

size_t my_strlen(const char *s)
{
    size_t len = 0;
    while (s[len] != '\0') {
        len++;
    }
    return len;
}

int my_strcmp(const char *a, const char *b)
{
    while (*a && (*a == *b)) {
        a++;
        b++;
    }
    return (unsigned char)*a - (unsigned char)*b;
}

char *my_strcpy(char *dst, const char *src)
{
    char *p = dst;
    while ((*p++ = *src++) != '\0')
        ;
    return dst;
}

void str_to_upper(char *s)
{
    for (int i = 0; s[i] != '\0'; i++) {
        s[i] = TO_UPPER(s[i]);
    }
}

void str_to_lower(char *s)
{
    for (int i = 0; s[i] != '\0'; i++) {
        s[i] = TO_LOWER(s[i]);
    }
}

int str_count_char(const char *s, char c)
{
    int count = 0;
    while (*s) {
        if (*s == c) {
            count++;
        }
        s++;
    }
    return count;
}
