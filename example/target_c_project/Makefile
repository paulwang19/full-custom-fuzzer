CC      = gcc
CFLAGS  = -Wall -Wextra -std=c11 -g
TARGET  = sample
SRCS    = main.c math_utils.c string_utils.c io/file_io.c
OBJS    = $(SRCS:.c=.o)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: clean
