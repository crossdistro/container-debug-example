#!/usr/bin/python3

import subprocess
import os
import ptrace.debugger

import containers

def run(command):
    return subprocess.run(command, shell=True, check=True)

containers.pivot_temporary_overlay()
containers.netns_with_veth()

command = ["ping", "-n", "192.168.0.2"]

debugger = ptrace.debugger.PtraceDebugger()
process = debugger.addProcess(ptrace.debugger.child.createChild(command, False), True)

while True:
    process.syscall()
    #event = debugger.waitProcessEvent()
    event = debugger.waitProcessEvent()
    if isinstance(event, ptrace.debugger.ProcessExit):
        break
    elif isinstance(event, ptrace.debugger.ProcessSignal):
        print(event.signum)
        print(event.name)
        print(process.syscall_state.event(ptrace.func_call.FunctionCallOptions()))

debugger.quit()
