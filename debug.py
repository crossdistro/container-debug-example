#!/usr/bin/python3

import cffi
import subprocess
import tempfile
import os

ffi = cffi.FFI()
ffi.cdef("""
int unshare(int flags);
int mount(const char *source, const char *target,
          const char *filesystemtype, unsigned long mountflags,
          const void *data);
""")
libc = ffi.dlopen("libc.so.6")

CLONE_FS = 0x00000200
CLONE_NEWNET = 0x40000000

def run(command):
    return subprocess.run(command, shell=True, check=True)

def _check(status):
    if status == -1:
        raise OSError(ffi.errno, os.strerror(ffi.errno))
    return status

def mount(source, target, fstype, flags, data):
    #print(source, target, fstype, flags, data)
    coding = "utf-8"
    return _check(libc.mount(
        source.encode(coding),
        target.encode(coding),
        fstype.encode(coding),
        flags,
        data.encode(coding)))

run("ip address")

def unshare(*args):
    flags = 0
    for arg in args:
        flags |= arg
    return _check(libc.unshare(flags))

unshare(CLONE_FS, CLONE_NEWNET)

# TODO: Handle cleanup. This is unfortunately not trivial.
tmp = tempfile.mkdtemp(prefix="pythondebugexample.")
print(tmp)
for d in "root", "upper", "work":
    os.makedirs(f"{tmp}/{d}", exist_ok=True)
print(os.listdir(tmp))
mount(
        "overlay",
        "/",
        "overlay", 
        0,
        f"lowerdir=/,upperdir={tmp}/upper,workdir={tmp}/work",)
run(f"touch /test")
print(os.listdir(f"/"))


