#include <stdlib.h>

int main(int c, char **v) {
    long long n = atoll(v[1]);
    long long *a = malloc((size_t)n * 8);
    for (long long i = 0; i < n; ++i) a[i] = i;
    volatile long long t = 0;
    for (long long i = 0; i < n; ++i) t += a[i];
    free(a);
    return 0;
}
