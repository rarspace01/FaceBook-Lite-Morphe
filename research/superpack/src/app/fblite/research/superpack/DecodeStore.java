package app.fblite.research.superpack;

import com.facebook.superpack.SuperpackArchive;
import com.facebook.superpack.SuperpackFile;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Decodes the secondary dex store (assets/secondary-program-dex-jars/store-0.dex.spo) with the app's own
 * libsuperpack-jni.so, on desktop Linux. Research only; run it through decode.sh.
 *
 * Usage: DecodeStore <loader.so> <libsuperpack-jni.so> <store-0.dex.spo> <metadata.txt> <outdir>
 *
 * Every file the store holds is written to outdir and checked against the SHA-1 metadata.txt lists for it.
 * Exits 0 only when all listed files came out with the right hash and nothing else did.
 */
public final class DecodeStore {
    private DecodeStore() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 5) {
            System.err.println("usage: DecodeStore <loader.so> <libsuperpack-jni.so> <store.dex.spo> <metadata.txt> <outdir>");
            System.exit(2);
        }
        Map<String, String> expected = metadata(new File(args[3]));
        File out = new File(args[4]);
        if (!out.isDirectory() && !out.mkdirs()) throw new IllegalStateException("cannot create " + out);

        System.load(new File(args[0]).getAbsolutePath());
        System.load(new File(args[1]).getAbsolutePath());

        int bad = 0;
        byte[] buffer = new byte[1 << 20];
        try (InputStream in = new BufferedInputStream(new FileInputStream(args[2]), 1 << 20)) {
            long archive = SuperpackArchive.readNative(in, "spo", 0L);
            if (archive == 0) throw new IllegalStateException("the library could not open the store");
            try {
                while (!SuperpackArchive.isEmptyNative(archive)) {
                    long file = SuperpackArchive.nextNative(archive);
                    if (file == 0) throw new IllegalStateException("the library returned no file before the end");
                    try {
                        String name = SuperpackFile.getNameNative(file);
                        if (!name.matches("[A-Za-z0-9._-]{1,64}") || name.startsWith(".")) {
                            throw new IllegalStateException("unexpected file name in store: " + name);
                        }
                        int length = SuperpackFile.getLengthNative(file);
                        MessageDigest sha1 = MessageDigest.getInstance("SHA-1");
                        File target = new File(out, name);
                        try (OutputStream os = new FileOutputStream(target)) {
                            for (int at = 0; at < length; ) {
                                int n = Math.min(buffer.length, length - at);
                                SuperpackFile.readBytesNative(file, at, n, buffer, 0);
                                sha1.update(buffer, 0, n);
                                os.write(buffer, 0, n);
                                at += n;
                            }
                        }
                        String actual = hex(sha1.digest());
                        String want = expected.remove(name);
                        if (actual.equals(want)) {
                            System.out.println("OK       " + name + " " + length + " " + actual);
                        } else {
                            bad++;
                            System.out.println((want == null ? "UNLISTED " : "MISMATCH ") + name + " " + length + " " + actual
                                    + (want == null ? "" : " (want " + want + ")"));
                        }
                    } finally {
                        SuperpackFile.closeNative(file);
                    }
                }
            } finally {
                SuperpackArchive.closeNative(archive);
            }
        }
        for (String name : expected.keySet()) {
            bad++;
            System.out.println("MISSING  " + name);
        }
        System.out.println(bad == 0 ? "VERIFIED" : "FAILED " + bad);
        System.exit(bad == 0 ? 0 : 1);
    }

    /** File name to SHA-1 for each "name sha1 ..." line; lines starting with "." describe the store and are skipped. */
    private static Map<String, String> metadata(File file) throws Exception {
        Map<String, String> map = new LinkedHashMap<>();
        for (String line : Files.readAllLines(file.toPath(), StandardCharsets.UTF_8)) {
            String[] parts = line.trim().split("\\s+");
            if (parts.length >= 2 && !parts[0].startsWith(".") && parts[1].matches("[0-9a-f]{40}")) map.put(parts[0], parts[1]);
        }
        if (map.isEmpty()) throw new IllegalStateException("no dex files listed in " + file);
        return map;
    }

    private static String hex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format("%02x", b & 0xff));
        return sb.toString();
    }
}
