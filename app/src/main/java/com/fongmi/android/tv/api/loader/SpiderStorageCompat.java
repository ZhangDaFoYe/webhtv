package com.fongmi.android.tv.api.loader;

import java.io.File;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/** Compatibility for spiders exposing an optional externalDir override. */
final class SpiderStorageCompat {
    private SpiderStorageCompat() {}

    static boolean configure(Class<?> init, File root) throws ReflectiveOperationException {
        final Field field;
        final Method directory;
        try {
            field = init.getDeclaredField("externalDir");
            directory = init.getDeclaredMethod("makeExternalDir", String.class);
        } catch (NoSuchFieldException | NoSuchMethodException absent) {
            return false; // Most spiders do not expose this compatibility contract.
        }
        if (field.getType() != File.class || !Modifier.isStatic(field.getModifiers())
                || Modifier.isFinal(field.getModifiers()) || directory.getReturnType() != File.class
                || !Modifier.isStatic(directory.getModifiers())) return false;
        if (root == null || !root.isDirectory()) throw new IllegalArgumentException("Missing spider storage root");
        // spring.jar uses this override before its direct Environment/mkdirs fallback.
        // Install BEFORE init(Context), which can start background cookie synchronization.
        field.setAccessible(true);
        field.set(null, root);
        if (!root.equals(field.get(null))) throw new IllegalStateException("Spider storage override not applied");
        return true;
    }
}
