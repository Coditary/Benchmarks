#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static int env_int(const char *name, int fallback) {
    const char *value = getenv(name);
    if (!value || !*value) {
        return fallback;
    }
    return atoi(value);
}

static int cmp_double(const void *a, const void *b) {
    double left = *(const double *)a;
    double right = *(const double *)b;
    return (left > right) - (left < right);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: bench <size>\n");
        return 1;
    }

    long long size = atoll(argv[1]);
    int warmup = env_int("BENCH_WARMUP", 3);
    int runs = env_int("BENCH_RUNS", 0);
    if (runs <= 0) {
        runs = env_int("BENCH_MAX_RUNS", 50);
    }

    double load_start = now_seconds();
    long long *data = malloc((size_t)size * sizeof(long long));
    if (!data) {
        return 1;
    }
    for (long long i = 0; i < size; ++i) {
        data[i] = i;
    }
    double load_seconds = now_seconds() - load_start;

    volatile long long sink = 0;
    for (int w = 0; w < warmup; ++w) {
        for (long long i = 0; i < size; ++i) {
            sink += data[i];
        }
    }

    double *samples = malloc((size_t)runs * sizeof(double));
    if (!samples) {
        free(data);
        return 1;
    }

    for (int r = 0; r < runs; ++r) {
        double start = now_seconds();
        for (long long i = 0; i < size; ++i) {
            sink += data[i];
        }
        samples[r] = now_seconds() - start;
    }

    double sum = 0.0;
    for (int r = 0; r < runs; ++r) {
        sum += samples[r];
    }
    double mean = sum / runs;

    double *sorted = malloc((size_t)runs * sizeof(double));
    if (!sorted) {
        free(samples);
        free(data);
        return 1;
    }
    memcpy(sorted, samples, (size_t)runs * sizeof(double));
    qsort(sorted, (size_t)runs, sizeof(double), cmp_double);

    double median = sorted[runs / 2];
    double variance = 0.0;
    for (int r = 0; r < runs; ++r) {
        double delta = samples[r] - mean;
        variance += delta * delta;
    }
    double stddev = sqrt(variance / runs);

    printf(
        "{\"mean_seconds\":%.9f,\"median_seconds\":%.9f,\"stddev_seconds\":%.9f,"
        "\"min_seconds\":%.9f,\"max_seconds\":%.9f,\"runs\":%d,\"warmup\":%d,"
        "\"load_seconds\":%.9f}\n",
        mean,
        median,
        stddev,
        sorted[0],
        sorted[runs - 1],
        runs,
        warmup,
        load_seconds);

    free(sorted);
    free(samples);
    free(data);
    return 0;
}
