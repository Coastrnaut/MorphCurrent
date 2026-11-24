"""Synthetic ComfyUI API graphs for offline image-stage tests.

They use only node classes and input names captured from the owner's real
ComfyUI 0.46.0 ``/object_info`` (tests/fixtures/object_info_image_nodes.json),
shaped like the locally installed Qwen-Image templates. They are NOT the owner's
exports: real ``workflows/01_anchor_t2i.json`` / ``02_anchor_edit.json`` must come
from a successful local render (F02, owner-gated). ``installed_object_info``
simulates the state *after* the owner installs the Qwen files, by appending the
template-declared filenames to the loader choice lists.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
QWEN_UNET_T2I = "qwen_image_fp8_e4m3fn.safetensors"
QWEN_UNET_EDIT = "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
QWEN_TE = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
QWEN_VAE = "qwen_image_vae.safetensors"


def real_object_info() -> dict:
    image = json.loads((FIXTURES / "object_info_image_nodes.json").read_text(encoding="utf-8"))
    wan = json.loads((FIXTURES / "object_info_wan22_flf2v.json").read_text(encoding="utf-8"))
    return {**image, **wan}


def installed_object_info() -> dict:
    info = copy.deepcopy(real_object_info())
    info["UNETLoader"]["input"]["required"]["unet_name"][0] += [QWEN_UNET_T2I, QWEN_UNET_EDIT]
    info["CLIPLoader"]["input"]["required"]["clip_name"][0].append(QWEN_TE)
    info["VAELoader"]["input"]["required"]["vae_name"][0].append(QWEN_VAE)
    return info


def t2i_graph() -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": QWEN_UNET_T2I, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": QWEN_TE, "type": "qwen_image"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": QWEN_VAE}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.1}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": "a glass orchid"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": "blurry"}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 832, "height": 480, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "seed": 1, "steps": 20, "cfg": 2.5, "sampler_name": "euler",
            "scheduler": "simple", "positive": ["5", 0], "negative": ["6", 0],
            "latent_image": ["7", 0], "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "ComfyUI"}},
    }


def edit_graph() -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": QWEN_UNET_EDIT, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": QWEN_TE, "type": "qwen_image"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": QWEN_VAE}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "11": {"class_type": "LoadImage", "inputs": {"image": "example.png"}},
        "12": {"class_type": "FluxKontextImageScale", "inputs": {"image": ["11", 0]}},
        "5": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["2", 0], "prompt": "turn it into a butterfly", "vae": ["3", 0], "image1": ["12", 0]}},
        "6": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["2", 0], "prompt": "", "vae": ["3", 0], "image1": ["12", 0]}},
        "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["12", 0], "vae": ["3", 0]}},
        "8": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "seed": 1, "steps": 20, "cfg": 2.5, "sampler_name": "euler",
            "scheduler": "simple", "positive": ["5", 0], "negative": ["6", 0],
            "latent_image": ["7", 0], "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "ComfyUI"}},
    }


def t2i_profile_dict(graph_sha: str, workflow: str = "workflows/test_t2i.json") -> dict:
    return {
        "profile": "test_qwen_t2i", "capability": "text_to_image", "workflow": workflow,
        "workflow_sha256": graph_sha,
        "bindings": {
            "positive_prompt": {"node_id": "5", "input": "text", "class_type": "CLIPTextEncode"},
            "negative_prompt": {"node_id": "6", "input": "text", "class_type": "CLIPTextEncode"},
            "seed": {"node_id": "8", "input": "seed", "class_type": "KSampler"},
            "width": {"node_id": "7", "input": "width", "class_type": "EmptySD3LatentImage"},
            "height": {"node_id": "7", "input": "height", "class_type": "EmptySD3LatentImage"},
            "filename_prefix": {"node_id": "10", "input": "filename_prefix", "class_type": "SaveImage"},
        },
        "outputs": [{"node_id": "10", "class_type": "SaveImage", "kind": "image"}],
    }


def edit_profile_dict(graph_sha: str, workflow: str = "workflows/test_edit.json") -> dict:
    return {
        "profile": "test_qwen_edit", "capability": "reference_edit", "workflow": workflow,
        "workflow_sha256": graph_sha,
        "bindings": {
            "reference_image": {"node_id": "11", "input": "image", "class_type": "LoadImage"},
            "positive_prompt": {"node_id": "5", "input": "prompt", "class_type": "TextEncodeQwenImageEditPlus"},
            "negative_prompt": {"node_id": "6", "input": "prompt", "class_type": "TextEncodeQwenImageEditPlus"},
            "seed": {"node_id": "8", "input": "seed", "class_type": "KSampler"},
            "filename_prefix": {"node_id": "10", "input": "filename_prefix", "class_type": "SaveImage"},
        },
        "outputs": [{"node_id": "10", "class_type": "SaveImage", "kind": "image"}],
    }
