/* liblog.so and libandroid.so for the superpack library: logging goes to stderr; assets are never used. */
#include <stdio.h>
#include <stdarg.h>
int __android_log_print(int prio, const char *tag, const char *fmt, ...) { va_list a; va_start(a, fmt); fprintf(stderr, "[%s] ", tag); vfprintf(stderr, fmt, a); fputc('\n', stderr); va_end(a); return 0; }
void *AAssetManager_fromJava(void *env, void *o) { return 0; }
void *AAssetManager_open(void *m, const char *n, int mode) { return 0; }
void AAsset_close(void *a) {}
int AAsset_openFileDescriptor(void *a, long *s, long *l) { return -1; }
