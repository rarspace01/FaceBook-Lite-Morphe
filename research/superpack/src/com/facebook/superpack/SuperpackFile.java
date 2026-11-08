package com.facebook.superpack;

import java.io.InputStream;

/** One file of a superpack archive, as a native handle. Declares every native the library registers on this class. */
public final class SuperpackFile {
    private SuperpackFile() {
    }

    public static native void closeMemfdNative(long file);

    public static native void closeNative(long file);

    public static native long createSuperpackFileNative(String name, InputStream in);

    public static native long createSuperpackFileNative(String name, byte[] bytes);

    public static native int getLengthNative(long file);

    public static native String getNameNative(long file);

    public static native void readBytesNative(long file, int offset, int count, byte[] into, int intoOffset);
}
