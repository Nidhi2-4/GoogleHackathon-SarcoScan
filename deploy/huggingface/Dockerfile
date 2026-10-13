# SarcoScan API on a Hugging Face Space (free: 16 GB memory, so all four models load).
# The Space holds only this file and README.md; the code is cloned from GitHub at build time.
# See docs/DEPLOY.md, "All four models, free: Hugging Face Spaces".
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

# Changes whenever main moves, so a rebuild picks up new code instead of a cached clone.
ADD --chown=user https://api.github.com/repos/Nidhi2-4/HackPulse-CodeSharks/git/refs/heads/main /tmp/main.json
RUN git clone --depth 1 https://github.com/Nidhi2-4/HackPulse-CodeSharks.git .
RUN pip install --no-cache-dir -r backend/requirements.txt

ENV SARCOSCAN_MODELS=xray,tabular STORAGE_BACKEND=cloudinary
EXPOSE 7860
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
