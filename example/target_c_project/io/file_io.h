#ifndef FILE_IO_H
#define FILE_IO_H

#include <stddef.h>

/* 將 buf 內容寫入 path，成功回傳 0，失敗回傳 -1 */
int write_text_file(const char *path, const char *buf);

/* 讀取 path 的第一行（最多 max_len-1 字元）到 buf，成功回傳 0，失敗回傳 -1 */
int read_first_line(const char *path, char *buf, size_t max_len);

/* 計算檔案的行數，失敗回傳 -1 */
int count_lines(const char *path);

#endif /* FILE_IO_H */
