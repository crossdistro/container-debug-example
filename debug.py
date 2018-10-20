#!/usr/bin/python3

import subprocess
import os

import containers

def run(command):
    return subprocess.run(command, shell=True, check=True)

containers.temporary_overlay()
run("touch /test")
print(os.listdir(f"/"))
