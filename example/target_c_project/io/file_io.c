#include "file_io.h"

#include <stdio.h>
#include <string.h>

int write_text_file(const char *path, const char *buf)
{
    FILE *fp = fopen(path, "w");
    if (!fp) return -1;
    fputs(buf, fp);
    fclose(fp);
    return 0;
}

int read_first_line(const char *path, char *buf, size_t max_len)
{
    if (max_len == 0) return -1;
    FILE *fp = fopen(path, "r");
    if (!fp) return -1;
    if (!fgets(buf, (int)max_len, fp)) {
        fclose(fp);
        return -1;
    }
    /* 去掉尾端換行 */
    size_t len = strlen(buf);
    if (len > 0 && buf[len - 1] == '\n')
        buf[len - 1] = '\0';
    fclose(fp);
    return 0;
}

int count_lines(const char *path)
{
    FILE *fp = fopen(path, "r");
    if (!fp) return -1;
    int count = 0;
    int c;
    while ((c = fgetc(fp)) != EOF) {
        if (c == '\n') count++;
    }
    fclose(fp);
    return count;
}
