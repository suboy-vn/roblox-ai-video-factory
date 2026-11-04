#!/usr/bin/env python3
"""ROBLOX AI VIDEO FACTORY 1.0 - offline Video Factory renderer.

Reads a job manifest, extracts one clip per Director Plan scene, normalizes all
clips to a common profile, concatenates them, and optionally mixes licensed
local audio cues from Sound Studio. No third-party Python package is required.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def log(message: str) -> None:
    print(message, flush=True)


def run_command(args: list[str], description: str) -> subprocess.CompletedProcess:
    log(f"\n[Video Factory] {description}")
    log("[CMD] " + subprocess.list2cmdline(args))
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.stdout:
        # Keep console output readable without hiding the final FFmpeg diagnostics.
        lines = result.stdout.splitlines()
        for line in lines[-35:]:
            log(line)
    if result.returncode != 0:
        raise RuntimeError(f"{description} thất bại (exit code {result.returncode}). Xem log FFmpeg phía trên.")
    return result


def probe_media(ffprobe: str, source: Path) -> dict[str, Any]:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(source)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError("Không đọc được thông tin video bằng ffprobe: " + result.stderr[-1500:])
    payload = json.loads(result.stdout or "{}")
    streams = payload.get("streams", [])
    has_video = any(s.get("codec_type") == "video" for s in streams)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    if not has_video:
        raise RuntimeError("File đầu vào không có video stream.")
    try:
        duration = float(payload.get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        duration = 0.0
    return {"has_audio": has_audio, "duration": duration, "streams": streams}


def ffmpeg_video_filter(width: int, height: int, fps: int, framing: str) -> str:
    if framing in ("Crop to fill (Shorts)", "Crop to fill"):
        fit = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    else:
        fit = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
    return f"{fit},setsar=1,fps={fps},format=yuv420p"


def ffconcat_quote(path: Path) -> str:
    # concat demuxer accepts single-quoted paths; escape embedded single quotes.
    value = str(path.resolve()).replace("\\", "/").replace("'", "'\\''")
    return f"file '{value}'"


def build_mix_command(
    ffmpeg: str,
    concat_video: Path,
    output_video: Path,
    cues: list[dict[str, Any]],
    total_duration: float,
    source_has_audio: bool,
    preserve_source_audio: bool,
    source_audio_volume: float,
) -> list[str] | None:
    active_cues: list[dict[str, Any]] = []
    for cue in cues:
        audio_path = Path(str(cue.get("local_path", "") or ""))
        if not (cue.get("rights_confirmed") and audio_path.is_file()):
            continue
        active_cues.append(cue)

    keep_original = bool(preserve_source_audio and source_has_audio)
    if not keep_original and not active_cues:
        return None

    args = [ffmpeg, "-y", "-i", str(concat_video)]
    filter_parts: list[str] = []
    labels: list[str] = []
    input_index = 1

    if keep_original:
        volume = max(0.0, min(2.0, float(source_audio_volume)))
        filter_parts.append(f"[0:a:0]volume={volume:.3f},apad=whole_dur={total_duration:.3f}[orig]")
        labels.append("[orig]")

    for idx, cue in enumerate(active_cues, start=1):
        local_path = Path(str(cue["local_path"])).resolve()
        if bool(cue.get("loop")):
            args.extend(["-stream_loop", "-1"])
        args.extend(["-i", str(local_path)])

        duration = max(0.1, float(cue.get("duration_seconds", 3) or 3))
        start = max(0.0, float(cue.get("start_seconds", 0) or 0))
        duration = min(duration, max(0.1, total_duration - start))
        volume = max(0.0, min(2.0, float(cue.get("volume", 0.7) or 0)))
        fade_in = min(duration, max(0.0, float(cue.get("fade_in_seconds", 0) or 0)))
        fade_out = min(duration, max(0.0, float(cue.get("fade_out_seconds", 0) or 0)))
        delay_ms = int(start * 1000)
        label = f"cue{idx}"
        filters = [f"atrim=duration={duration:.3f}", "asetpts=PTS-STARTPTS", f"volume={volume:.3f}"]
        if fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in:.3f}")
        if fade_out > 0:
            filters.append(f"afade=t=out:st={max(0.0, duration-fade_out):.3f}:d={fade_out:.3f}")
        filters.append(f"adelay={delay_ms}|{delay_ms}")
        filters.append(f"apad=whole_dur={total_duration:.3f}")
        filter_parts.append(f"[{input_index}:a:0]" + ",".join(filters) + f"[{label}]")
        labels.append(f"[{label}]")
        input_index += 1

    if len(labels) == 1:
        filter_parts.append(f"{labels[0]}anull,alimiter=limit=0.95,apad=whole_dur={total_duration:.3f}[aout]")
    else:
        filter_parts.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=2:normalize=0,alimiter=limit=0.95,apad=whole_dur={total_duration:.3f}[aout]")

    args.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_duration:.3f}", "-movflags", "+faststart", str(output_video)
    ])
    return args


def render(manifest_path: Path) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ffmpeg = str(manifest.get("ffmpeg_path") or "ffmpeg").strip().strip('"')
    ffprobe = str(manifest.get("ffprobe_path") or "").strip().strip('"')
    if not ffprobe:
        ffmpeg_candidate = Path(ffmpeg)
        if ffmpeg_candidate.is_file():
            candidates = [ffmpeg_candidate.with_name("ffprobe.exe"), ffmpeg_candidate.with_name("ffprobe")]
            ffprobe = str(next((c for c in candidates if c.is_file()), Path("ffprobe")))
        else:
            ffprobe = "ffprobe"
    source = Path(str(manifest.get("source_video", ""))).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy video đầu vào: {source}")

    output = Path(str(manifest.get("output_video", ""))).expanduser()
    if not str(output):
        raise ValueError("Manifest thiếu output_video.")
    output.parent.mkdir(parents=True, exist_ok=True)
    profile = manifest.get("profile", {})
    width = int(profile.get("width", 1920))
    height = int(profile.get("height", 1080))
    fps = int(profile.get("fps", 30))
    crf = int(profile.get("crf", 20))
    preset = str(profile.get("preset", "medium"))
    framing = str(profile.get("framing", "Fit with bars (YouTube)"))
    trim_start = max(0.0, float(manifest.get("trim_start_seconds", 0) or 0))
    export_scene_clips = bool(manifest.get("export_scene_clips", True))
    scenes = manifest.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Director Plan không có danh sách scenes hợp lệ.")

    media = probe_media(ffprobe, source)
    has_source_audio = bool(media["has_audio"])
    scene_total = sum(max(0.1, float(s.get("duration_seconds", 6) or 6)) for s in scenes)
    if media["duration"] and trim_start + scene_total > media["duration"] + 0.5:
        raise ValueError(
            f"Director Plan cần {trim_start + scene_total:.1f}s nhưng video chỉ dài {media['duration']:.1f}s. "
            "Hãy kiểm tra Trim start, thời lượng cảnh và file quay OBS."
        )

    job_dir = output.parent / (output.stem + "_work")
    if job_dir.exists():
        shutil.rmtree(job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)
    scene_dir = output.parent / (output.stem + "_scenes")
    if export_scene_clips:
        scene_dir.mkdir(parents=True, exist_ok=True)

    vf = ffmpeg_video_filter(width, height, fps, framing)
    preset_allowed = {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}
    if preset not in preset_allowed:
        preset = "medium"

    list_file = job_dir / "concat_list.txt"
    clip_paths: list[Path] = []
    cursor = trim_start
    for idx, scene in enumerate(scenes, start=1):
        duration = max(0.1, float(scene.get("duration_seconds", 6) or 6))
        scene_number = int(scene.get("scene_number", idx) or idx)
        clip_name = f"Scene_{scene_number:03d}.mp4"
        clip_path = job_dir / clip_name
        cmd = [
            ffmpeg, "-y", "-ss", f"{cursor:.3f}", "-i", str(source), "-t", f"{duration:.3f}",
            "-map", "0:v:0"
        ]
        if has_source_audio:
            cmd.extend(["-map", "0:a:0"])
        cmd.extend([
            "-vf", vf, "-r", str(fps), "-c:v", "libx264", "-preset", preset,
            "-crf", str(crf), "-pix_fmt", "yuv420p"
        ])
        if has_source_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k", "-ar", "48000"])
        else:
            cmd.append("-an")
        cmd.extend(["-movflags", "+faststart", str(clip_path)])
        run_command(cmd, f"Render cảnh {scene_number} ({duration:.1f}s)")
        clip_paths.append(clip_path)
        if export_scene_clips:
            shutil.copy2(clip_path, scene_dir / clip_name)
        cursor += duration

    list_file.write_text("\n".join(ffconcat_quote(p) for p in clip_paths) + "\n", encoding="utf-8")
    concat_video = job_dir / "episode_video_only_or_original_audio.mp4"
    run_command([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(concat_video)], "Nối các cảnh theo thứ tự Director Plan")

    cues = manifest.get("sound_cues", [])
    preserve_audio = bool(manifest.get("preserve_source_audio", True))
    source_volume = float(manifest.get("source_audio_volume", 0.65) or 0)
    mix_cmd = build_mix_command(
        ffmpeg, concat_video, output, cues if isinstance(cues, list) else [],
        scene_total, has_source_audio, preserve_audio, source_volume
    )
    if mix_cmd:
        run_command(mix_cmd, "Trộn audio gốc và các cue từ Sound Studio")
    elif has_source_audio and not preserve_audio:
        run_command([ffmpeg, "-y", "-i", str(concat_video), "-map", "0:v:0", "-c:v", "copy", "-an", str(output)], "Xuất video không kèm audio gốc")
    else:
        shutil.copy2(concat_video, output)

    try:
        final_media = probe_media(ffprobe, output)
        log(f"\n[HOÀN TẤT] {output}")
        log(f"Thời lượng file: {final_media['duration']:.2f}s | Audio: {'Có' if final_media['has_audio'] else 'Không'}")
    except Exception:
        log(f"\n[HOÀN TẤT] {output}")
    if not export_scene_clips:
        shutil.rmtree(scene_dir, ignore_errors=True)
    log(f"Thư mục làm việc: {job_dir}")
    if export_scene_clips:
        log(f"Các clip cảnh: {scene_dir}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Roblox AI Video Factory episode")
    parser.add_argument("--manifest", required=True, help="Path to Video Factory manifest JSON")
    args = parser.parse_args()
    try:
        output = render(Path(args.manifest).resolve())
        print(f"\nVideo đã xuất: {output}")
        return 0
    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
