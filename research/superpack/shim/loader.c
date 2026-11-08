#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <jni.h>
/*
 * Loaded by DecodeStore before the superpack library. Opens the library named by $SPK_LIB with
 * RTLD_DEEPBIND, so its imports resolve to the shims in this directory (found through
 * LD_LIBRARY_PATH) before the JVM's glibc. DecodeStore's own System.load of the same path then
 * reuses this handle and runs its JNI_OnLoad.
 */
JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *r) {
    const char *t = getenv("SPK_LIB");
    if (!t) { fprintf(stderr, "set SPK_LIB to the superpack library\n"); exit(3); }
    if (!dlopen(t, RTLD_NOW | RTLD_GLOBAL | RTLD_DEEPBIND)) { fprintf(stderr, "dlopen: %s\n", dlerror()); exit(3); }
    return JNI_VERSION_1_6;
}
