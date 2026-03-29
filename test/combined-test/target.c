/*
 * Combined test: argv fuzzing (-j) + function-weight (-H)
 *
 * Options:
 *   -p : enable parse_header path (high weight target)
 *   -v : enable validate_crc path (high weight target)
 *   -d : enable debug_dump path   (no weight, decoy)
 *
 * Call structure:
 *   main -> dispatch -> parse_header   (weight 90, via -p)
 *                    -> validate_crc   (weight 60, via -v)
 *                    -> debug_dump     (no weight, via -d)
 *
 * With -j we test multiple option combos; with -H we verify that
 * seeds reaching parse_header / validate_crc get more energy.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>

/* High-weight target: parse a structured header */
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

/* No-weight decoy: should NOT get extra energy */
int debug_dump(const unsigned char *buf, int len) {
    int sum = 0;
    for (int i = 0; i < len; i++) {
        sum += buf[i];
    }

    if (sum > 2000) {
        return 2;
    } else if (sum > 1000) {
        return 1;
    }
    return 0;
}

/* Intermediate dispatcher — should get propagated weight */
int dispatch(const unsigned char *buf, int len, int do_parse, int do_validate,
             int do_debug) {
    int result = 0;

    if (do_parse) {
        result += parse_header(buf, len);
    }

    if (do_validate) {
        result += validate_crc(buf, len);
    }

    if (do_debug) {
        result += debug_dump(buf, len);
    }

    return result;
}

int main(int argc, char **argv) {
    int do_parse = 0, do_validate = 0, do_debug = 0;
    int opt;
    unsigned char buf[1024];

    while ((opt = getopt(argc, argv, "pvd")) != -1) {
        switch (opt) {
            case 'p': do_parse = 1;    break;
            case 'v': do_validate = 1; break;
            case 'd': do_debug = 1;    break;
            default:  break;
        }
    }

    /* Read input from file argument or stdin */
    FILE *fp = stdin;
    if (optind < argc) {
        fp = fopen(argv[optind], "rb");
        if (!fp) {
            fprintf(stderr, "Cannot open: %s\n", argv[optind]);
            return 1;
        }
    }

    int len = fread(buf, 1, sizeof(buf), fp);
    if (fp != stdin) fclose(fp);
    if (len < 1) return 1;

    int result = dispatch(buf, len, do_parse, do_validate, do_debug);
    printf("result: %d\n", result);
    return 0;
}
