import platform
import subprocess
from titanos.platform.shell import Shell

print(f"Platform: {platform.system()}")
res = Shell.execute("echo $PSVersionTable")
print(f"Stdout: {res.stdout.strip()}")
