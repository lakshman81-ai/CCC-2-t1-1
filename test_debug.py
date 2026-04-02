import subprocess
print(subprocess.check_output(["grep", "-n", "Debug Inspector", "index.html"]).decode('utf-8'))
