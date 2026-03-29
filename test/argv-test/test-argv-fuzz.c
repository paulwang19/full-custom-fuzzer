/*
   Test target for My-Fuzzer argv fuzzing.

   This program reads input from stdin or a file and behaves differently
   depending on the command-line options provided:
     -a : enables path A (checks for "AAAA" in input)
     -b : enables path B (checks for "BBBB" in input)
     -c : enables path C (checks for "CCCC" in input)

   Different option combinations expose different code paths,
   making this ideal for testing argv fuzzing.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>

int main(int argc, char **argv) {

  int opt_a = 0, opt_b = 0, opt_c = 0;
  int opt;
  char buf[256];

  while ((opt = getopt(argc, argv, "abc")) != -1) {

    switch (opt) {

      case 'a':
        opt_a = 1;
        break;
      case 'b':
        opt_b = 1;
        break;
      case 'c':
        opt_c = 1;
        break;
      default:
        break;

    }

  }

  /* Read input from file argument or stdin */
  FILE *fp = stdin;
  if (optind < argc) {

    fp = fopen(argv[optind], "r");
    if (!fp) {

      fprintf(stderr, "Cannot open input file: %s\n", argv[optind]);
      return 1;

    }

  }

  memset(buf, 0, sizeof(buf));
  size_t n = fread(buf, 1, sizeof(buf) - 1, fp);

  if (fp != stdin) fclose(fp);

  if (n == 0) return 0;

  /* Path A: only reachable with -a */
  if (opt_a && n >= 4 && memcmp(buf, "AAAA", 4) == 0) {

    printf("Path A triggered!\n");
    /* Deeper path */
    if (n >= 8 && memcmp(buf + 4, "DEEP", 4) == 0) {

      printf("Deep path A!\n");
      abort();  /* intentional crash for fuzzer to find */

    }

  }

  /* Path B: only reachable with -b */
  if (opt_b && n >= 4 && memcmp(buf, "BBBB", 4) == 0) {

    printf("Path B triggered!\n");

  }

  /* Path C: only reachable with -c */
  if (opt_c && n >= 4 && memcmp(buf, "CCCC", 4) == 0) {

    printf("Path C triggered!\n");
    /* Another crash path */
    if (n >= 6 && buf[4] == 'X' && buf[5] == 'X') {

      printf("Crash path C!\n");
      abort();

    }

  }

  /* Combined path: -a -b together */
  if (opt_a && opt_b && n >= 2 && buf[0] == 'Z' && buf[1] == 'Z') {

    printf("Combined path A+B!\n");

  }

  return 0;

}
