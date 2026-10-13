"""Download the four model files into ml/models/ from the team's Drive folder.

Used at deploy time, because the files are not in git. Does nothing unless FETCH_MODELS=1.
On your own machine, copying the files in by hand works just as well.

    FETCH_MODELS=1 python -m ml.fetch_models
"""
import os
import subprocess
import sys
from pathlib import Path

MODELS = Path(__file__).parent / "models"
# File ids in https://drive.google.com/drive/folders/1Zxi-auctfcBx3Jhcx89zlIls5CgT20VN
FILES = {
    "osteoporosis_best.pt": "1SRRqJoYE_FzEmW3pziLxZ5p5PENj94g0",
    "arthritis_best.pt": "1uTH6lJF9w9eNJBfkwv3hNPCctW9rWToC",
    "sarcopenia_ANN_1.joblib": "1fN3EjU9aRpI-CpnGjAIsGtoXI2r8S9PP",
    "osteoporosis_XGBoost_1.joblib": "1x-KNg6nDiOmJYXcS0CVRx7t8iE5IjXvG",
}

if __name__ == "__main__":
    if os.environ.get("FETCH_MODELS") != "1":
        print("FETCH_MODELS is not 1: skipping the model download.")
        sys.exit(0)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "gdown"])
    import gdown

    MODELS.mkdir(exist_ok=True)
    for name, file_id in FILES.items():
        target = MODELS / name
        if target.exists():
            print(f"{name}: already here")
            continue
        if not gdown.download(id=file_id, output=str(target), quiet=True):
            sys.exit(f"Could not download {name}. Is the Drive folder still shared by link?")
        print(f"{name}: {target.stat().st_size // 1024} KB")
