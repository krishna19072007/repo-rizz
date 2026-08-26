with open("python-backend/engine.py", "r") as f:
    lines = f.readlines()
with open("python-backend/engine.py", "w") as f:
    for line in lines:
        if "print(f\"[AI]" not in line:
            f.write(line)
