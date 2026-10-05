package com.github.catvod.utils;

import java.io.File;
import java.io.IOException;

/** Fork-owned storage policy. No migration and no dependency on Android APIs. */
final class StorageRoot {
    private StorageRoot() {}

    static File choose(File downloads, File externalDownloads, File internalFiles) {
        File[] bases = {downloads, externalDownloads, internalFiles};
        for (File base : bases) {
            if (base == null) continue;
            File candidate = new File(base, "mytvx");
            try {
                // Do not follow a user-created mytvx symlink out of the chosen base.
                if (!candidate.getCanonicalFile().equals(new File(base.getCanonicalFile(), "mytvx"))) continue;
                if ((!candidate.isDirectory() && !candidate.mkdirs()) || !candidate.canWrite()) continue;
                // canWrite alone is not reliable on Android scoped storage/FUSE.
                File probe = File.createTempFile(".write-probe-", ".tmp", candidate);
                if (!probe.delete()) probe.deleteOnExit();
                return candidate;
            } catch (IOException | SecurityException ignored) {
                // Never fall back to the shared-storage root.
            }
        }
        throw new IllegalStateException("No writable mytvx storage directory");
    }

    static File child(File root, String name) {
        try {
            String relative = name.replace('\\', '/');
            while (relative.startsWith("/")) relative = relative.substring(1);
            File file = new File(root, relative);
            String base = root.getCanonicalPath();
            String target = file.getCanonicalPath();
            if (!target.equals(base) && !target.startsWith(base + File.separator)) {
                throw new IllegalArgumentException("Storage path escapes mytvx: " + name);
            }
            return file;
        } catch (IOException e) {
            throw new IllegalArgumentException("Cannot resolve storage path", e);
        }
    }

    static File redirect(File file, File legacyRoot, File root) {
        if (file == null) return null;
        try {
            String path = file.getCanonicalPath();
            String old = legacyRoot.getCanonicalPath();
            for (String alias : new String[]{old, "/sdcard", "/storage/emulated/0", "/storage/self/primary"}) {
                for (String dir : new String[]{"TVBox", "VOX", "TV"}) {
                    String prefix = alias + "/" + dir;
                    if (path.equals(prefix) || path.startsWith(prefix + "/")) {
                        return child(root, dir + path.substring(prefix.length()));
                    }
                }
            }
            return file;
        } catch (IOException e) {
            throw new IllegalArgumentException("Cannot resolve write path", e);
        }
    }
}
