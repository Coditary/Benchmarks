#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        return 1;
    }

    int64_t size = (int64_t)atoll(argv[1]);
    if (size < 0) {
        return 1;
    }

    int64_t *data = malloc((size_t)size * sizeof(int64_t));
    if (data == NULL) {
        return 1;
    }

    for (int64_t i = 0; i < size; i++) {
        data[i] = i;
    }

    int64_t total = 0;
    for (int64_t i = 0; i < size; i++) {
        total += data[i];
    }

    (void)total;
    free(data);
    return 0;
}
