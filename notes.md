# Debugging Network Applications Using Container Technology

Container projects like LXC and Docker use Linux kernel namespacing
features for container based deployment of applications. We will use kernel
features together with Python and convenience libraries to instead perform
debugging, experiments and test automation.

While a combination of bash, strace, ltrace or ptrace called directly from
C program code do their job well, we can do the same in Python while
gathering all information at once and driving the whole process as a single
entity.

All of this can be driven interactively or fully automated. Pavel has
already used automation to drive tests using client and server programs,
collecting and processing data from the individual tests in a uniform way.
Use your imagination and you can take it to another level.

## Links

  * https://docs.python.org/3/howto/instrumentation.html
  * https://github.com/dbecvarik/pycoz
  * https://github.com/vstinner/python-ptrace
  * https://github.com/crossdistro/network-testing

## Debugging and tracing tools

  * gdb interactive debugging
  * ptrace / strace / ltrace / python-ptrace
  * systemtap for userspace programs


