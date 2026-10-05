#!/usr/bin/env python3
"""Execute production Path/StorageRoot against a real filesystem, with Android stubs.
Not an Android permission/device test. Requires only Python and a JDK.
"""
import os
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
SOURCES = {
    "android/os/Environment.java": '''package android.os;
import java.io.File;
public class Environment {
 public static final String DIRECTORY_DOWNLOADS = "Download";
 public static File shared;
 public static File getExternalStorageDirectory() { return shared; }
 public static File getExternalStoragePublicDirectory(String s) { return new File(shared, s); }
}''',
    "com/github/catvod/Init.java": '''package com.github.catvod;
import java.io.File;
public class Init {
 public static File external, internal;
 public static Init context() { return new Init(); }
 public File getExternalFilesDir(String s) { return external; }
 public File getFilesDir() { return internal; }
 public File getCacheDir() { return new File(internal, "cache"); }
}''',
    "com/orhanobut/logger/Logger.java": '''package com.orhanobut.logger;
public class Logger {
 public static Logger t(String s) { return new Logger(); }
 public void d(String s) {}
}''',
    "com/github/catvod/utils/Util.java": '''package com.github.catvod.utils;
public class Util { public static String md5(String s) { return s; } }''',
    "com/github/catvod/utils/Shell.java": '''package com.github.catvod.utils;
public class Shell { public static void exec(String s) {} }''',
    "com/github/catvod/utils/StorageTest.java": r'''package com.github.catvod.utils;
import java.io.*;
import java.nio.file.Files;
import com.github.catvod.Init;
import android.os.Environment;
public class StorageTest {
 static int assertions;
 static void check(boolean ok, String msg) { assertions++; if (!ok) throw new AssertionError(msg); }
 static void equal(File a, File b) throws Exception { check(a.getCanonicalFile().equals(b.getCanonicalFile()), a + " != " + b); }
 static void reject(Runnable action) { try { action.run(); throw new AssertionError("accepted escape"); } catch (IllegalArgumentException expected) { assertions++; } }
 public static void main(String[] args) throws Exception {
  File fixture = new File(args[0]);
  Environment.shared = new File(fixture, "shared");
  Init.external = new File(fixture, "private/Download");
  Init.internal = new File(fixture, "internal");
  File base = new File(Environment.shared, "Download/mytvx");
  equal(Path.root(), base);
  for (String dir : new String[]{"TVBox", "VOX", "TV"}) {
   File legacy = new File(Environment.shared, dir + "/deep/config.json");
   legacy.getParentFile().mkdirs();
   Files.writeString(legacy.toPath(), "old");
   equal(Path.local(dir + "/deep/config.json"), legacy);
   equal(Path.local("file://" + legacy), legacy);
   File target = new File(base, dir + "/deep/config.json");
   equal(Path.write(legacy, "new".getBytes()), target);
   check(Files.readString(target.toPath()).equals("new"), "write contents");
   check(Files.readString(legacy.toPath()).equals("old"), "legacy untouched");
   equal(Path.local(dir + "/deep/config.json"), target);
   equal(Path.local("file://" + legacy), target);
   equal(Path.root(dir + "/deep/config.json"), target);
   for (String alias : new String[]{"/sdcard", "/storage/emulated/0", "/storage/self/primary"})
    equal(StorageRoot.redirect(new File(alias + "/" + dir + "/deep/config.json"), Environment.shared, base), target);
   File stream = new File(Environment.shared, dir + "/stream.txt");
   equal(Path.write(stream, new ByteArrayInputStream("stream".getBytes())), new File(base, dir + "/stream.txt"));
   check(!stream.exists(), "no legacy stream write");
   File copy = new File(Environment.shared, dir + "/copy.txt");
   Path.copy(legacy, copy);
   check(new File(base, dir + "/copy.txt").isFile() && !copy.exists(), "copy redirected");
   File create = new File(Environment.shared, dir + "/create.txt");
   equal(Path.create(create), new File(base, dir + "/create.txt"));
   check(!create.exists(), "create redirected");
  }
  equal(Path.tv(), new File(base, "TV"));
  equal(Path.root("VOX/nested", "x"), new File(base, "VOX/nested/x"));
  reject(() -> Path.root("../../TVBox/escape"));
  reject(() -> Path.root("VOX", "../../../../escape"));
  File other = new File(Environment.shared, "TVBoxOther/file");
  equal(StorageRoot.redirect(other, Environment.shared, base), other);
  File outside = new File(fixture, "outside"); outside.mkdirs();
  Files.createSymbolicLink(new File(base, "link").toPath(), outside.toPath());
  reject(() -> Path.root("link/escape"));
  // A non-directory public Download is a deterministic permission/failure fixture.
  Environment.shared = new File(fixture, "blocked"); Environment.shared.mkdirs();
  Files.writeString(new File(Environment.shared, "Download").toPath(), "blocked");
  equal(Path.root(), new File(Init.external, "mytvx"));
  equal(Path.write(new File(Environment.shared, "VOX/nested/x"), new byte[]{1}), new File(Init.external, "mytvx/VOX/nested/x"));
  check(!new File(Environment.shared, "VOX").exists(), "fallback never creates root VOX");
  Init.external = null;
  equal(Path.root(), new File(Init.internal, "mytvx"));
  File symlinkBase = new File(fixture, "symlink-base"); symlinkBase.mkdirs();
  Files.createSymbolicLink(new File(symlinkBase, "mytvx").toPath(), outside.toPath());
  equal(StorageRoot.choose(symlinkBase, null, Init.internal), new File(Init.internal, "mytvx"));
  System.out.println("PASS: " + assertions + " assertions; production Path + StorageRoot filesystem tests");
 }
}''',
}

with tempfile.TemporaryDirectory(prefix="mytvx-storage-", dir=os.environ.get("TMPDIR")) as tmp:
    tmp = Path(tmp)
    java = []
    for relative, source in SOURCES.items():
        file = tmp / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(source)
        java.append(str(file))
    for name in ("Path.java", "StorageRoot.java"):
        java.append(str(REPO / "catvod/src/main/java/com/github/catvod/utils" / name))
    subprocess.run(["javac", "-d", str(tmp / "classes"), *java], check=True)
    subprocess.run(["java", "-cp", str(tmp / "classes"), "com.github.catvod.utils.StorageTest", str(tmp / "fixture")], check=True)
