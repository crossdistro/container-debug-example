#!/usr/bin/python3

import cffi
import os
import sys
import subprocess
import tempfile

ffi = cffi.FFI()
ffi.cdef("""
int unshare(int flags);
int mount(const char *source, const char *target,
          const char *filesystemtype, unsigned long mountflags,
          const void *data);
int pivot_root(const char *new_root, const char *put_old);
""")
libc = ffi.dlopen("libc.so.6")

coding = "utf-8"

CLONE_FS = 0x00000200
CLONE_NEWNS = 0x00020000
CLONE_NEWNET = 0x40000000

CLONE_DEFAULTS = CLONE_NEWNS | CLONE_NEWNET

MS_PRIVATE = 0x40000
MS_SHARED = 0x100000
MS_REC = 0x4000

MS_DEFAULTS = 0

def _check(status):
    if status == -1:
        raise OSError(ffi.errno, os.strerror(ffi.errno))
    return status

def unshare(flags=CLONE_DEFAULTS):
    return _check(libc.unshare(flags))

# TODO: support ffi.NULL
def mount(source, target, fstype, flags, data):
    print(source, target, fstype, flags, data)
    return _check(libc.mount(
        source.encode(coding),
        target.encode(coding),
        fstype.encode(coding),
        flags,
        data.encode(coding)))

def mount_overlay(target, *,
        lowerdir="/",
        upperdir,
        workdir,
        flags=MS_DEFAULTS):
    return mount(
        "overlay",
        target,
        "overlay",
        flags,
        f"lowerdir={lowerdir},upperdir={upperdir},workdir={workdir}")

def mount_unshare(target):
    return _check(libc.mount(
        b"none",
        target.encode("utf-8"),
        ffi.NULL,
        MS_REC | MS_PRIVATE,
        ffi.NULL))

def mount_kernel_filesystems():
    mount("none", "/proc", "proc", 0, "")
    mount("none", "/sys", "sysfs", 0, "")

def pivot_root(new_root, put_old):
    #print(new_root, put_old)
    return _check(libc.pivot_root(
        new_root.encode(coding),
        put_old.encode(coding)))

def pivot_temporary_overlay():
    """High level API for overlay based debugging"""

    assert os.getuid() == 0

    # TODO: Handle cleanup. This is unfortunately not trivial as the
    # temporary directory cannot be removed while things are mounted.
    tmp = tempfile.mkdtemp(prefix="python-container-debug.")
    #print(tmp)
    for d in "root", "upper", "lower", "work", "oldroot":
        os.makedirs(f"{tmp}/{d}", exist_ok=True)

    #print(os.listdir(tmp))
    new_root = f"{tmp}/root"
    mount_overlay(new_root,
            upperdir=f"{tmp}/upper",
            workdir=f"{tmp}/work")
    mount_unshare("/")
    put_old = f"{tmp}/root/oldroot"
    os.makedirs(put_old, exist_ok=True)
    unshare()
    pivot_root(new_root, put_old)
    mount_kernel_filesystems()

    return tmp

if __name__ == "__main__":
    tmp = pivot_temporary_overlay()
    os.environ["OVERLAY_TMP_DIRECTORY"] = tmp
    status = subprocess.run(sys.argv[1:] or ["mount"])
    exit(status.returncode)
