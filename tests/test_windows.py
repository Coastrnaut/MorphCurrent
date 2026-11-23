"""Windows diagnostics are mocked; CI does not need an NVIDIA GPU."""
import platform
from unittest.mock import patch

import pytest

from morph_studio.windows import windows_diagnostics


def test_windows_report_does_not_require_comfy_or_gpu():
    with patch.object(platform, "system", return_value="Windows"), patch(
        "morph_studio.windows.shutil.which", return_value=None
    ):
        report = windows_diagnostics(check_comfy=False)
    assert report["supported_host"] is True
    assert report["comfyui"]["checked"] is False
    assert report["ready_for_offline_development"] is False
    assert report["ready_for_local_gpu_workflows"] is False


def test_linux_host_is_marked_unsupported():
    with patch.object(platform, "system", return_value="Linux"), patch(
        "morph_studio.windows.shutil.which", return_value=None
    ):
        report = windows_diagnostics(check_comfy=False)
    assert report["supported_host"] is False


def test_doctor_rejects_remote_endpoint():
    with pytest.raises(ValueError):
        windows_diagnostics("http://external.example:8188", check_comfy=False)
