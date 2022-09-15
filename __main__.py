import subprocess
from pathlib import Path

from src.transpile import transpile_file

if __name__ == "__main__":
    for i in Path("examples/src").iterdir():
        print(f"Transpiling {i.name}")
        transpile_file(Path(f"examples/src/{i.stem}.koi"))
        print(f"Compiling {i.stem}.c")
        subprocess.run(["gcc", f"out/{i.stem}.c", "-o", f"out/{i.stem}.out"])

    print("Finished")
