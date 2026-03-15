"""
Utility helpers used across the bot.
"""
import os
import time
import asyncio
import subprocess
import humanize
from pathlib import Path


# ── Progress bar ───────────────────────────────────────────────────────────────
def progress_bar(current: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "▓" * length
    filled = int(length * current / total)
    bar    = "▓" * filled + "░" * (length - filled)
    pct    = current / total * 100
    return f"[{bar}] {pct:.1f}%"


def format_progress(current: int, total: int, speed: float, eta: float) -> str:
    cur  = humanize.naturalsize(current, binary=True)
    tot  = humanize.naturalsize(total,   binary=True)
    spd  = humanize.naturalsize(speed,   binary=True) + "/s"
    eta_str = time.strftime("%M:%S", time.gmtime(int(eta))) if eta > 0 else "∞"
    bar  = progress_bar(current, total)
    return (
        f"{bar}\n"
        f"📦 {cur} / {tot}\n"
        f"⚡ Speed: {spd}\n"
        f"⏱ ETA: {eta_str}"
    )


# ── Human-readable file size ───────────────────────────────────────────────────
def human_size(size: int) -> str:
    return humanize.naturalsize(size, binary=True)


# ── Elapsed time ───────────────────────────────────────────────────────────────
def elapsed(start: float) -> str:
    secs = int(time.time() - start)
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# ── Run shell command async ────────────────────────────────────────────────────
async def run_cmd(cmd: str | list, timeout: int = 3600) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd if isinstance(cmd, str) else " ".join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "Timeout"
    return proc.returncode, out.decode(errors="replace"), err.decode(errors="replace")


# ── FFmpeg helpers ─────────────────────────────────────────────────────────────
async def get_media_info(path: str) -> str:
    """Return ffprobe media info as string."""
    cmd = (
        f'ffprobe -v quiet -print_format json -show_format -show_streams "{path}"'
    )
    rc, out, err = await run_cmd(cmd)
    return out if rc == 0 else f"Error: {err}"


async def get_duration(path: str) -> float:
    """Return media duration in seconds."""
    cmd = (
        f'ffprobe -v quiet -show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 "{path}"'
    )
    rc, out, _ = await run_cmd(cmd)
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


async def take_screenshot(path: str, timestamp: str, out_path: str) -> bool:
    cmd = f'ffmpeg -ss {timestamp} -i "{path}" -frames:v 1 -q:v 2 "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def trim_video(path: str, start: str, end: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -ss {start} -to {end} -c copy "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def trim_audio(path: str, start: str, end: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -ss {start} -to {end} -c copy "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def convert_video(path: str, fmt: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -c:v libx264 -c:a aac "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def convert_audio(path: str, fmt: str, bitrate: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -b:a {bitrate} "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def mute_video(path: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -an -c:v copy "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def extract_audio(path: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -vn -c:a copy "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def video_to_gif(path: str, out_path: str, duration: int = 10) -> bool:
    cmd = (
        f'ffmpeg -t {duration} -i "{path}" '
        f'-vf "fps=10,scale=480:-1:flags=lanczos" '
        f'-loop 0 "{out_path}" -y'
    )
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def add_watermark(path: str, text: str, out_path: str) -> bool:
    cmd = (
        f'ffmpeg -i "{path}" '
        f'-vf "drawtext=text=\'{text}\':fontsize=24:fontcolor=white:'
        f'x=(w-text_w)/2:y=h-th-10:shadowcolor=black:shadowx=2:shadowy=2" '
        f'-c:a copy "{out_path}" -y'
    )
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def merge_video_audio(video: str, audio: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{video}" -i "{audio}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def apply_hardsub(video: str, subtitle: str, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{video}" -vf subtitles="{subtitle}" -c:a copy "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def apply_8d_audio(path: str, out_path: str) -> bool:
    cmd = (
        f'ffmpeg -i "{path}" '
        f'-af "apulsator=hz=0.125" '
        f'"{out_path}" -y'
    )
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def apply_bass_boost(path: str, gain: int, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -af "bass=g={gain}" "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def change_audio_speed(path: str, speed: float, out_path: str) -> bool:
    cmd = f'ffmpeg -i "{path}" -af "atempo={speed}" "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def change_volume(path: str, volume_pct: int, out_path: str) -> bool:
    vol = volume_pct / 100.0
    cmd = f'ffmpeg -i "{path}" -af "volume={vol}" "{out_path}" -y'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


# ── File split ─────────────────────────────────────────────────────────────────
async def split_file(path: str, chunk_size: int, out_dir: str) -> list[str]:
    """Split a file into chunks of chunk_size bytes using split command."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    base = os.path.join(out_dir, "part_")
    cmd  = f'split -b {chunk_size} "{path}" "{base}"'
    rc, _, _ = await run_cmd(cmd)
    if rc != 0:
        return []
    parts = sorted(str(p) for p in Path(out_dir).glob("part_*"))
    return parts


# ── Archive helpers ────────────────────────────────────────────────────────────
async def make_zip(src: str, out_path: str, password: str = "") -> bool:
    if password:
        cmd = f'zip -P "{password}" "{out_path}" "{src}"'
    else:
        cmd = f'zip "{out_path}" "{src}"'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0


async def extract_archive(src: str, out_dir: str, password: str = "") -> bool:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ext = Path(src).suffix.lower()
    if ext == ".zip":
        cmd = f'unzip {"-P " + password if password else ""} "{src}" -d "{out_dir}"'
    elif ext == ".rar":
        cmd = f'unrar x {"-p" + password if password else ""} "{src}" "{out_dir}"'
    elif ext == ".7z":
        cmd = f'7z x {"-p" + password if password else ""} "{src}" -o"{out_dir}"'
    else:
        cmd = f'tar -xf "{src}" -C "{out_dir}"'
    rc, _, _ = await run_cmd(cmd)
    return rc == 0
