# Superpack decoder

Facebook Lite keeps all of its code except `classes.dex` in one compressed store,
`assets/secondary-program-dex-jars/store-0.dex.spo`, that only the app's own native library
(`libsuperpack-jni.so`) can unpack. The classes the hide-ads, feed-font and video extensions replace or read
are all in that store, so finding their names in a new app version starts here.

`decode.sh` unpacks the store on an x86_64 Linux PC, with no phone or emulator: it runs the APK's x86_64
library in a desktop JVM, with small shims standing in for the parts of Android's libc (bionic), `liblog` and
`libandroid` it needs.

```sh
./decode.sh facebook-lite-536.apk out/dex536
# OK       secondary-1.dex 10955232 7e4e210e...
# OK       secondary-2.dex 687772 842197b7...
# VERIFIED
```

Each file is checked against the SHA-1 the APK lists in `metadata.txt`, and the script exits non-zero
unless every file matches.

Requirements: x86_64 Linux, gcc, a JDK, unzip, python3.

**The library must be the x86_64 build.** APKMirror and Aptoide publish each version for several CPU types.
If yours is arm64-only, pass an APK that has `lib/x86_64/` as the third argument. The library from 536
decoded the 530 store, and the SHA-1 check proves whether a decode is right:

```sh
./decode.sh facebook-lite-530-arm64.apk out/dex530 facebook-lite-536-x86_64.apk
```

## How it works

| File | Role |
|---|---|
| `unversion.py` | Copies the library with its bionic symbol-version tags removed, so glibc's loader accepts imports such as `malloc@LIBC`. |
| `shim/bionic.c` | Built as `libc.so`. Forwards to glibc and adds what bionic has and glibc lacks or numbers differently: `__errno`, the `__sF` stdio array, `funopen`, `sysconf` constants, fortify helpers, `android_dlopen_ext`. |
| `shim/android.c` | Built as `liblog.so` and `libandroid.so`. Logs go to stderr; the asset functions are never used. |
| `shim/loader.c` | Opens the library with `RTLD_DEEPBIND`, so its imports resolve to the shims before the JVM's glibc. |
| `src/com/facebook/superpack/` | Java classes with the natives the library registers in `JNI_OnLoad`. Every one must be declared, or loading fails. |
| `src/app/fblite/research/superpack/DecodeStore.java` | Reads each file out of the store and checks its SHA-1. |

The library prints `Could not get file descriptor from spo file.` because it is handed a stream rather than an
asset. That is expected, and the decode still works.

This runs code from the APK on your machine. Only use APKs signed by Facebook
(`keytool -printcert -jarfile app.apk` shows `CN=Facebook Corporation`).

Next step: [../version-diff](../version-diff) to find each class's new name.
