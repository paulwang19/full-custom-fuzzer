#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <stddef.h>

/* 巨集函數 */
#define IS_UPPER(c)   ((c) >= 'A' && (c) <= 'Z')
#define IS_LOWER(c)   ((c) >= 'a' && (c) <= 'z')
#define IS_DIGIT(c)   ((c) >= '0' && (c) <= '9')
#define TO_LOWER(c)   (IS_UPPER(c) ? (c) + 32 : (c))
#define TO_UPPER(c)   (IS_LOWER(c) ? (c) - 32 : (c))

size_t my_strlen(const char *s);
int    my_strcmp(const char *a, const char *b);
char  *my_strcpy(char *dst, const char *src);
void   str_to_upper(char *s);
void   str_to_lower(char *s);
int    str_count_char(const char *s, char c);

#endif /* STRING_UTILS_H */
