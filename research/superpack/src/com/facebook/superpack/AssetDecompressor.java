package com.facebook.superpack;

import android.content.res.AssetManager;

import java.io.InputStream;

/**
 * The library's JNI_OnLoad registers these natives and fails if one is missing, so they are all
 * declared with the names and signatures it registers. DecodeStore calls none of them.
 */
public final class AssetDecompressor {
    private AssetDecompressor() {
    }

    public static native String[] decompress(AssetManager assets, String a, String b, String c);

    public static native String[] decompress_from_so(String a, String b, String c);

    public static native String[] decompress_legacy(InputStream in, String a, String b);

    public static native String[] decompress_range(AssetManager assets, String a, String b, String c, int d, int e);

    public static native String[] decompress_range_from_so(String a, String b, String c, int d, int e);

    public static native String[] decompress_with_ref(String a, String b, String c, String d);

    public static native int get_architecture();

    public static native int sync_directory_to_disk(String path);

    public static native int sync_file_to_disk(String path);

    public static native void testDecompressorLibraryUsable(byte[] bytes);
}
