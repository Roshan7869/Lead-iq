#!/usr/bin/env python3
import sys
import subprocess

# Run the audit directly
code = open("audit_runner.py").read()
exec(code)
