"""
RClone upload / download helper.
"""
import os
import asyncio
from config import Config
from utils.helpers import run_cmd


async def rclone_upload(
    local_path: str,
    remote_path: str,
    config_path: str = None,
) -> tuple[bool, str]:
    """
    Upload local_path to remote_path using rclone.
    remote_path format: 'gdrive:MyFolder/file.mp4'
    Returns (success, output_or_error)
    """
    cfg = config_path or Config.RCLONE_CONFIG
    cmd = (
        f'"{Config.RCLONE_PATH}" copy '
        f'--config "{cfg}" '
        f'--progress '
        f'"{local_path}" "{remote_path}"'
    )
    rc, out, err = await run_cmd(cmd)
    return rc == 0, out or err


async def rclone_download(
    remote_path: str,
    local_dir: str,
    config_path: str = None,
) -> tuple[bool, str]:
    cfg = config_path or Config.RCLONE_CONFIG
    cmd = (
        f'"{Config.RCLONE_PATH}" copy '
        f'--config "{cfg}" '
        f'"{remote_path}" "{local_dir}"'
    )
    rc, out, err = await run_cmd(cmd)
    return rc == 0, out or err


async def rclone_ls(remote_path: str, config_path: str = None) -> list[str]:
    cfg = config_path or Config.RCLONE_CONFIG
    cmd = f'"{Config.RCLONE_PATH}" lsf --config "{cfg}" "{remote_path}"'
    rc, out, _ = await run_cmd(cmd)
    if rc != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]
