/*
 * Function-weight energy scheduling test target.
 *
 * This program has a clear call structure:
 *
 *   main -> process_input -> parse_header  (high weight target)
 *                         -> validate_crc  (high weight target)
 *                         -> handle_body
 *        -> fallback_handler
 *
 * The user marks parse_header(90) and validate_crc(60) as important.
 * Via call graph propagation, process_input should get propagated weight.
 *
 * Each function has multiple branches (edges) so we can observe
 * saturation-based decay as coverage increases.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* High-weight target: parse a 4-byte header */
int parse_header(const unsigned char *buf, int len) {
    if (len < 4) return -1;

    int result = 0;

    if (buf[0] == 'H') {
        result += 1;
        if (buf[1] == 'D') {
            result += 2;
            if (buf[2] == 'R') {
                result += 4;
                if (buf[3] == '!') {
                    result += 8;  /* full header match */
                }
            }
        }
    }

    if (buf[0] > 0x80) {
        result += 16;  /* binary header */
    }

    return result;
}

/* High-weight target: validate a simple checksum */
int validate_crc(const unsigned char *buf, int len) {
    if (len < 5) return 0;

    unsigned char crc = 0;
    for (int i = 0; i < len - 1; i++) {
        crc ^= buf[i];
    }

    if (crc == buf[len - 1]) {
        /* CRC matches */
        if (buf[0] == 0xff) {
            return 2;  /* special valid packet */
        }
        return 1;
    }

    if (crc == 0) {
        return -1;  /* null checksum */
    }

    return 0;
}

/* Normal function: process body data (no user weight) */
int handle_body(const unsigned char *buf, int len) {
    if (len < 6) return 0;

    int sum = 0;
    for (int i = 4; i < len; i++) {
        sum += buf[i];
    }

    if (sum > 1000) {
        return 2;
    } else if (sum > 500) {
        return 1;
    }
    return 0;
}

/* Normal function: fallback path */
int fallback_handler(const unsigned char *buf, int len) {
    if (len > 0 && buf[0] == 'F') {
        if (len > 1 && buf[1] == 'B') {
            return 2;
        }
        return 1;
    }
    return 0;
}

/* Intermediate function: calls parse_header and validate_crc.
 * Should receive propagated weight via call graph analysis. */
int process_input(const unsigned char *buf, int len) {
    int hdr = parse_header(buf, len);

    if (hdr > 0) {
        int crc = validate_crc(buf, len);
        int body = handle_body(buf, len);
        return hdr + crc + body;
    }

    return -1;
}

int main(int argc, char **argv) {
    unsigned char buf[1024];
    int len;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }

    len = fread(buf, 1, sizeof(buf), f);
    fclose(f);

    if (len < 1) return 1;

    int result;

    if (buf[0] >= 'A' && buf[0] <= 'Z') {
        result = process_input(buf, len);
    } else {
        result = fallback_handler(buf, len);
    }

    printf("result: %d\n", result);
    return 0;
}
