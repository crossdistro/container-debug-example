#!/usr/bin/python3

import cffi
import os
import sys
import subprocess
import tempfile
import pyroute2

ffi = cffi.FFI()
ffi.cdef("""
int unshare(int flags);
int mount(const char *source, const char *target,
          const char *filesystemtype, unsigned long mountflags,
          const void *data);
int umount2(const char *target, int flags);
int pivot_root(const char *new_root, const char *put_old);
""")
libc = ffi.dlopen("libc.so.6")

CLONE_FS = 0x00000200
CLONE_NEWNS = 0x00020000
CLONE_NEWNET = 0x40000000

MS_MOVE = 0x2000
MS_REC = 0x4000
MS_PRIVATE = 0x40000
MS_SLAVE = 0x80000
MS_SHARED = 0x100000

MS_DEFAULTS = 0

def _mkdir(target):
    os.makedirs(target, exist_ok=True)

def _check(status):
    if status == -1:
        raise OSError(ffi.errno, os.strerror(ffi.errno))
    return status

def _encode(name):
    if isinstance(name, str):
        return name.encode("utf-8")
    elif name is None:
        return ffi.NULL
    else:
        return name


def unshare(flags):
    return _check(libc.unshare(flags))

def mount(source, target, fstype, flags, data):
    return _check(libc.mount(
        _encode(source),
        _encode(target),
        _encode(fstype),
        flags,
        _encode(data)))

def unmount(target, *, recursive=False):
    flags = 0
    if recursive:
        flags |= MS_REC
    return _check(libc.umount2(_encode(target), flags))

def mount_tmpfs(target, *, makedirs=True):
    if makedirs:
        _mkdir(target)
    return mount(
        "none",
        target,
        "tmpfs",
        0,
        "")

def mount_overlay(target, *,
        lowerdir="/",
        upperdir,
        workdir,
        flags=MS_DEFAULTS,
        makedirs=True):
    if makedirs:
        _mkdir(target)
        _mkdir(lowerdir)
        _mkdir(upperdir)
        _mkdir(workdir)
    return mount(
        "overlay",
        target,
        "overlay",
        flags,
        f"lowerdir={lowerdir},upperdir={upperdir},workdir={workdir}")

def mount_unshare():
    unshare(CLONE_NEWNS)
    return mount(
        "none",
        "/",
        None,
        MS_REC | MS_SLAVE,
        None)

def pivot_root(new_root, put_old, *,
        makedirs=True):
    if makedirs:
        _mkdir(new_root)
        _mkdir(put_old)
    return _check(libc.pivot_root(
        _encode(new_root),
        _encode(put_old)))

def run(command):
    return subprocess.run(command, check=True)

def pivot_temporary_overlay(*, base="/"):
    """High level API for overlay based debugging"""

    assert os.getuid() == 0

    # Disassociate
    mount_unshare()

    # Create tmpfs in a static location to avoid spurious temporary
    # directories that cannot be easily cleaned up. Everything else will be
    # created under that tmpfs and dropped automatically.
    tmp = "/run/pycoz"
    mount_tmpfs(tmp)

    # Create the overlay.
    new_root = "/run/pycoz/root"
    mount_overlay(
        target=new_root,
        lowerdir=base,
        upperdir="/run/pycoz/upper",
        workdir="/run/pycoz/work")

    # Switch root to the overlay.
    old_root = "/oldroot"
    pivot_root(new_root, new_root + old_root)
    os.chdir("/root")

    # Fix missing mounts
    for path in "/dev", "/proc", "/sys":
        mount("/oldroot" + path, path, None, MS_MOVE, None)

    # Get rid of the old root
    run(["umount", "--recursive", old_root])
    os.rmdir(old_root)

def netns_with_veth():
    """High level API for netns based debugging"""

    assert os.getuid() == 0

    # Configure namespace and interfaces
    ip = pyroute2.IPDB()
    ip.create(kind="veth", ifname="pycoz0", peer="pycoz1")
    ip.commit()

    ns = pyroute2.IPDB(nl=pyroute2.NetNS("pycoz"))

    with ip.interfaces.pycoz0 as veth:
        veth.net_ns_fd = "pycoz"
    with ns.interfaces.pycoz0 as veth:
        veth.add_ip("192.168.0.1/24")
        veth.up()
    with ip.interfaces.pycoz1 as veth:
        veth.add_ip("192.168.0.2/24")
        veth.up()

    ip.release()
    ns.release()

    # Switch namespace
    pyroute2.netns.setns("pycoz")

if __name__ == "__main__":
    pivot_temporary_overlay()
    netns_with_veth()
    status = subprocess.run(sys.argv[1:] or ["mount"])
    exit(status.returncode)
