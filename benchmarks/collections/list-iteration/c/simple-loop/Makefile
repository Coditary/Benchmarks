CC ?= gcc
CFLAGS ?= -O3 -std=c11 -Wall -Wextra

.PHONY: build clean

build: bench

bench: main.c
	$(CC) $(CFLAGS) -o bench main.c

clean:
	rm -f bench
