# ComfyUI Portable NVIDIA setup for MorphCurrent (native Windows 11)

Use this guide for the **NVIDIA RTX A6000 48 GB (Ampere)** running ComfyUI locally.
All MorphCurrent helper scripts are **Python**. Windows Command Prompt is sufficient:
no PowerShell, WSL, GPU passthrough, Docker or Linux setup.

## Official download — standard NVIDIA RTX build

- **Download (official current-release link):**
  https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z
- Official installation instructions:
  https://docs.comfy.org/installation/comfyui_portable_windows
- Upstream project:
  https://github.com/Comfy-Org/ComfyUI

Choose **NVIDIA GPU (modern RTX / CUDA 13.0 / Python 3.13)**, as shown in the
official documentation when this guide was written (2026-11-23).
**Do not choose** the legacy NVIDIA 10-series/CUDA 12.6/Python 3.12 archive for
the RTX A6000. The direct latest-release link follows future releases, so the
bundled Python and PyTorch CUDA versions may change: verify after extraction.
CUDA support requires a sufficiently recent compatible NVIDIA Windows driver;
do not assume your installed driver has been checked by this repository.

ComfyUI Portable includes **its own** Python and CUDA-enabled PyTorch packages.
Do not install or upgrade them with MorphCurrent's controller virtual
environment (C:\GIT\MorphCurrent\.venv).

## Extract under C:\AI

If ComfyUI is **already running successfully**, you do not need to download or
reinstall it; first locate its actual extraction directory and use that
directory in the commands below.

For a new install:

1. In **Windows Command Prompt**, create the parent directory if needed:

   ```cmd
   mkdir C:\AI
   ```

2. Download the **standard NVIDIA RTX** .7z archive from the official URL above.
3. Extract it with [7-Zip](https://7-zip.org/) so the result has **one**
   ComfyUI_windows_portable folder directly inside C:\AI.
4. Check the expected contents:

   ```text
   C:\AI\
      ComfyUI_windows_portable\
         ComfyUI\
            main.py
            models\
         python_embeded\
            python.exe
         run_nvidia_gpu.bat
         ...
   ```

5. In Command Prompt:

   ```cmd
   dir C:\AI\ComfyUI_windows_portable\ComfyUI\main.py
   dir C:\AI\ComfyUI_windows_portable\python_embeded\python.exe
   ```

If either file is not there, the .7z may have created an **extra nested**
ComfyUI_windows_portable folder. Correct the extraction path or pass the
actual folder containing both `ComfyUI` and `python_embeded` to the helper.
Do not assume `C:\AI` or another install directory actually exists.

## Start ComfyUI with MorphCurrent's Python helper

From a native Windows **Command Prompt**:

```cmd
cd /d C:\GIT\MorphCurrent
python scripts\windows\launch_comfyui.py --install-root C:\AI\ComfyUI_windows_portable --dry-run
python scripts\windows\launch_comfyui.py --install-root C:\AI\ComfyUI_windows_portable
```

The helper uses the Portable-embedded `python.exe` and
`ComfyUI\main.py --windows-standalone-build`, and explicitly binds only
`127.0.0.1:8188`. It does **not** download weights, install custom nodes or
modify the ComfyUI Python environment. By default it uses ComfyUI's automatic
memory management; `--memory-mode highvram` is **opt-in** and cannot make two
14B FP16 Wan experts fit simultaneously in 48 GiB VRAM.

You may instead use ComfyUI Portable's supplied `run_nvidia_gpu.bat` as an
**official fallback**, but MorphCurrent itself does not require or generate
batch/PowerShell scripts. If already running, **do not start a second server**;
simply continue to connectivity checks.

The ComfyUI web interface should open at:
http://127.0.0.1:8188

Keep the server's terminal window running while using MorphCurrent.

## Verify RTX A6000 + bundled Python/PyTorch CUDA

In a **separate** native Windows Command Prompt:

```cmd
nvidia-smi
C:\AI\ComfyUI_windows_portable\python_embeded\python.exe -c "import sys, torch; print('Python:', sys.version.split()[0]); print('Torch:', torch.__version__); print('Torch CUDA:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unavailable')"
cd /d C:\GIT\MorphCurrent
python scripts\windows\check.py --check-comfy
.venv\Scripts\python.exe -m morph_studio.cli doctor --strict
```

The CUDA test runs in **ComfyUI Portable's Python**, not MorphCurrent's.
A successful CUDA check plus a responsive local ComfyUI API is a **setup
smoke test**, not proof that Wan 2.2 models/nodes are installed or that
generation works. If using a different ComfyUI folder, adjust the executable
path accordingly.

You can also inspect these in your browser:

- http://127.0.0.1:8188/system_stats
- http://127.0.0.1:8188/object_info

Do not expose ComfyUI to your LAN or the internet. If port 8188 is already
occupied by your running instance, reuse it rather than launching another one.

## Wan 2.1 VAE for Wan 2.2 I2V/FLF2V

For Wan 2.2 first/last-frame video, use the **Wan 2.1 VAE** named `wan_2.1_vae.safetensors`.
The user has already downloaded the VAE and reports placing it here:

```text
C:\AI\ComfyUI_windows_portable\ComfyUI\models\vae\wan_2.1_vae.safetensors
```

Verify the file is present using native Windows Command Prompt:

```cmd
dir C:\AI\ComfyUI_windows_portable\ComfyUI\models\vae\wan_2.1_vae.safetensors
```

In the ComfyUI Wan 2.2 workflow, select `wan_2.1_vae.safetensors` in the
**Load VAE** node. If not listed, refresh the node/model list or restart ComfyUI.
Place VAE files under `models\vae`, **not** `models\diffusion_models`.

This placement is user-reported and has not been checked directly on the Windows host.
Do not add the `.safetensors` model to the Git repository.
## Next: first real MorphCurrent generation

1. Open the **official Wan 2.2** tutorial:
   https://docs.comfy.org/tutorials/video/wan/wan2_2
2. In ComfyUI, load and run a first/last-frame video workflow with the **actual**
   installed Wan I2V/FLF2V model variants and node classes. Resolve any
   missing-weight/node warnings in ComfyUI first.
3. Once a short bridge succeeds, use **Save (API Format)** and store its
   sanitized workflow at `C:\GIT\MorphCurrent\workflows\03_wan22_flf2v.json`.
4. Open this repo in Claude Desktop **Code**, read
   `docs/CLAUDE_DESKTOP_ONESHOT.md`, and ask Claude to verify node mappings
   against `/object_info`. Do not invent node IDs or download models silently.

**No automatic downloads**: this document contains an official link for a
manual installation. The repository does not bundle the ComfyUI archive,
model weights, or external custom-node code.
