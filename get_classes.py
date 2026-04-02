import sys
for line in open("serializer.py"):
    if "class" in line:
        print(line.strip())
