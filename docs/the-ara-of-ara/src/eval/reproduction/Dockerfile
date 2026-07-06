# Reproduction Agent — Execution Container
#
# Provides an isolated environment for the coding agent to install packages,
# download data, and run experiments. Follows PaperBench's container design:
#   - Agent rollout happens on the host (API calls)
#   - Bash commands execute inside this container
#
# Build:
#   docker build -t ara-repro-agent code/eval/reproduction/
#
# Usage (managed by run_agent.py --docker):
#   docker run --rm -it \
#     -v /path/to/artifacts:/artifacts:ro \
#     -v /path/to/output:/output \
#     --gpus all \
#     ara-repro-agent

FROM python:3.12-slim

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Conda (for papers that need it)
RUN curl -fsSL https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh \
    -o /tmp/miniforge.sh \
    && bash /tmp/miniforge.sh -b -p /opt/conda \
    && rm /tmp/miniforge.sh
ENV PATH="/opt/conda/bin:$PATH"

# Common ML packages (pre-install to speed up agent runs)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
    numpy scipy matplotlib scikit-learn pandas \
    jax jaxlib \
    tqdm wandb tensorboard \
    gymnasium mujoco

# Working directory
WORKDIR /output

# Default shell
CMD ["/bin/bash"]
