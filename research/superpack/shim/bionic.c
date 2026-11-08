#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <errno.h>
#include <unistd.h>
#include <dlfcn.h>
/*
 * libc.so for running Facebook Lite's x86_64 libsuperpack-jni.so on desktop Linux (glibc).
 *
 * The library is built against Android's bionic libc. Most of what it imports behaves the same in
 * glibc, which this shim links against and forwards to. This file adds what bionic has and glibc
 * lacks or does differently: __errno, the __sF stdio array, BSD funopen, bionic's sysconf numbers,
 * the fortify helpers __strlen_chk / __strchr_chk / __strncpy_chk2, and android_dlopen_ext.
 * loader.c binds the library to this file before glibc with RTLD_DEEPBIND.
 */
int *__errno(void) { return __errno_location(); }
/* bionic FILE is 152 bytes on LP64; the library only takes &__sF[n] for stdin/stdout/stderr. */
char __sF[3 * 152];
static FILE *map(FILE *f) {
    char *p = (char *)f;
    if (p >= __sF && p < __sF + sizeof __sF) {
        long i = (p - __sF) / 152;
        return i == 0 ? stdin : i == 1 ? stdout : stderr;
    }
    return f;
}
#define REAL(name) static __typeof__(name) *real = 0; if (!real) real = dlsym(RTLD_NEXT, #name)
int fprintf(FILE *f, const char *fmt, ...) { va_list a; va_start(a, fmt); int r = vfprintf(map(f), fmt, a); va_end(a); return r; }
size_t fwrite(const void *p, size_t s, size_t n, FILE *f) { REAL(fwrite); return real(p, s, n, map(f)); }
size_t fread(void *p, size_t s, size_t n, FILE *f) { REAL(fread); return real(p, s, n, map(f)); }
int fflush(FILE *f) { REAL(fflush); return real(f ? map(f) : f); }
int fileno(FILE *f) { REAL(fileno); return real(map(f)); }
int feof(FILE *f) { REAL(feof); return real(map(f)); }
int ferror(FILE *f) { REAL(ferror); return real(map(f)); }
int setvbuf(FILE *f, char *b, int m, size_t s) { REAL(setvbuf); return real(map(f), b, m, s); }
char *fgets(char *b, int n, FILE *f) { REAL(fgets); return real(b, n, map(f)); }
/* bionic numbers its sysconf names differently from glibc. */
long sysconf(int name) {
    REAL(sysconf);
    switch (name) {
    case 0x27: case 0x28: return real(_SC_PAGESIZE);
    case 0x60: return real(_SC_NPROCESSORS_CONF);
    case 0x61: return real(_SC_NPROCESSORS_ONLN);
    }
    fprintf(stderr, "[shim] sysconf(%#x) unknown\n", name);
    return -1;
}
size_t __strlen_chk(const char *s, size_t len) { return strlen(s); }
char *__strchr_chk(const char *s, int c, size_t len) { return strchr(s, c); }
char *__strncpy_chk2(char *d, const char *s, size_t n, size_t dl, size_t sl) { return strncpy(d, s, n); }
void *android_dlopen_ext(const char *f, int fl, const void *info) { return dlopen(f, fl); }
/* funopen via fopencookie */
struct ck { void *c; int (*r)(void *, char *, int); int (*w)(void *, const char *, int); long (*s)(void *, long, int); int (*cl)(void *); };
static ssize_t ck_r(void *p, char *b, size_t n) { struct ck *k = p; return k->r(k->c, b, (int)n); }
static ssize_t ck_w(void *p, const char *b, size_t n) { struct ck *k = p; return k->w(k->c, b, (int)n); }
static int ck_s(void *p, off64_t *o, int wh) { struct ck *k = p; long r = k->s(k->c, *o, wh); if (r < 0) return -1; *o = r; return 0; }
static int ck_c(void *p) { struct ck *k = p; int r = k->cl ? k->cl(k->c) : 0; free(k); return r; }
FILE *funopen(void *c, int (*r)(void *, char *, int), int (*w)(void *, const char *, int), long (*s)(void *, long, int), int (*cl)(void *)) {
    struct ck *k = calloc(1, sizeof *k); k->c = c; k->r = r; k->w = w; k->s = s; k->cl = cl;
    cookie_io_functions_t io = { r ? ck_r : 0, w ? ck_w : 0, s ? ck_s : 0, ck_c };
    return fopencookie(k, r && w ? "r+" : r ? "r" : "w", io);
}
