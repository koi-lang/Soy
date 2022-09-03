import subprocess
from src.transpile import transpile_file

if __name__ == "__main__":
    transpile_file("examples/src/text_adventure.koi")
    subprocess.run(["gcc", "out/main.c", "-o", "out/main.out"])
