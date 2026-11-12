"""Compose recorded Gazebo observer images and render the saved occupancy map.

python tools/render_gazebo_demonstration.py --raw-root C:/path/to/presentation-runs
The directory contains presentation-mapping-01 and presentation-navigation-01.
Requires Pillow, NumPy, Matplotlib, OpenCV and ffmpeg on PATH.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/08-advanced-applications/simulation-results"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fonts():
    for path in (Path("C:/Windows/Fonts/msyh.ttc"),
                 Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")):
        if path.is_file():
            return ImageFont.truetype(str(path), 22), ImageFont.truetype(str(path), 17)
    raise RuntimeError("Install Microsoft YaHei or Noto Sans CJK SC for captions")


def projected_goal(goal, name):
    """Project recorded world target through the observer's SDF pinhole camera."""
    if name == "overview":
        eye, target, hfov = (-5.5, -4.5, 7.), (-.7, .7, 0), 1.5
    else:
        eye, target, hfov = (-4.1, -2.5, 3.3), (-2., .8, 0), 1.15
    eye, target = np.array(eye), np.array(target)
    forward = (target - eye) / np.linalg.norm(target - eye)
    right = np.cross(forward, [0., 0., 1.])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    delta = np.array([*goal[:2], .015]) - eye
    focal = 640 / (2 * np.tan(hfov / 2))
    depth = delta @ forward
    if depth <= 0:
        return None
    return 320 + focal * (delta @ right) / depth, 200 - focal * (delta @ up) / depth


def movie(raw, mode):
    media = raw / "media"
    records = [json.loads(s) for s in (media / "frames.jsonl").read_text().splitlines()]
    mission = json.loads((raw / "mission/results.json").read_text())
    mission_exit = json.loads((raw / "mission-exit.json").read_text())
    if mission_exit["exit_code"] != 0 or len(mission["results"]) != 3 or not all(
        result["passed"] and result["collision_events"] == 0 for result in mission["results"]
    ):
        raise ValueError(f"Demonstration mission did not complete three checks: {raw}")
    start, end = mission["results"][0]["started_wall"], mission["results"][-1]["finished_wall"]
    views = {name: [r for r in records if r["view"] == name] for name in ("overview", "detail")}
    # Retain complete recorded frames; choose every second observation for
    # compact presentation, synchronize views by recorded simulation time.
    selected = [r for r in views["detail"] if start - 1 <= r["wall"] <= end + .3][::2]
    overview_time = np.array([r["sim_ns"] for r in views["overview"]])
    big, small = fonts()
    output_frames, sources = [], []
    title = "建图：直行、转弯与停车" if mode == "mapping" else "导航：加载地图后，依次驶向三个短程目标"
    for detail in selected:
        index = int(np.argmin(np.abs(overview_time - detail["sim_ns"])))
        overview = views["overview"][index]
        if abs(overview["sim_ns"] - detail["sim_ns"]) > 80_000_000:
            continue
        frame = Image.new("RGB", (1280, 488), "#f5f7fa")
        draw = ImageDraw.Draw(frame)
        elapsed = detail["wall"] - start
        draw.text((16, 9), title, font=big, fill="#17324d")
        draw.text((1030, 13), f"运行时间 {max(0, elapsed):.1f} s", font=small, fill="#17324d")
        active = next((r for r in mission["results"] if r["started_wall"] <= detail["wall"] <= r["finished_wall"]), None)
        for x, item, label in ((0, overview, "房间总览"), (640, detail, "车辆近景")):
            with Image.open(media / item["file"]) as image:
                frame.paste(image.resize((640, 400), Image.Resampling.LANCZOS), (x, 45))
            draw.rectangle((x + 12, 56, x + 112, 84), fill="#f5f7fa")
            draw.text((x + 18, 59), label, font=small, fill="#17324d")
            if mode == "navigation" and active:
                point = projected_goal(active["expected_world_goal"], item["view"])
                if point and 0 < point[0] < 640 and 0 < point[1] < 400:
                    px, py = x + point[0], 45 + point[1]
                    draw.ellipse((px-9, py-9, px+9, py+9), fill="#ffec84", outline="#4c3600", width=2)
                    draw.line((px-12, py, px+12, py), fill="#4c3600", width=2)
                    draw.line((px, py-12, px, py+12), fill="#4c3600", width=2)
                    draw.text((px+14, py-14), f"目标{active['trial']+1}", font=small,
                              fill="#4c3600", stroke_width=2, stroke_fill="#fff8d5")
        if mode == "mapping":
            label = "RGB-D 基线 · RTAB-Map 建图 · 三组直行与转弯动作"
        else:
            label = f"RGB-D 基线 · RTAB-Map 地图定位 + Nav2 · 目标 {(active['trial'] + 1) if active else 1} / 3"
        draw.text((16, 455), label, font=small, fill="#17324d")
        draw.text((1000, 455), "Gazebo 实录 · 加速播放", font=small, fill="#17324d")
        output_frames.append(frame)
        sources.append(dict(detail=detail, overview=overview,
                            detail_sha256=sha(media / detail["file"]),
                            overview_sha256=sha(media / overview["file"])))
    if len(output_frames) < 10:
        raise RuntimeError(f"Too few synchronized observer frames: {mode}")
    name = f"gazebo-{mode}-3d"
    with tempfile.TemporaryDirectory() as temporary:
        video = Path(temporary) / "raw.avi"
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (1280, 488))
        if not writer.isOpened():
            raise RuntimeError("OpenCV MJPEG writer failed")
        for frame in output_frames:
            writer.write(cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR))
        writer.release()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
                        "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(OUT / f"{name}.mp4")], check=True)
    # Global palette avoids per-frame colour flicker. Resize for the inline GIF.
    size = (1024, 390)
    reduced = [frame.resize(size, Image.Resampling.LANCZOS) for frame in output_frames]
    contact = Image.new("RGB", (1024, 390 * 4))
    for j, i in enumerate(np.linspace(0, len(reduced)-1, 4, dtype=int)):
        contact.paste(reduced[i], (0, j * 390))
    palette = contact.quantize(colors=192)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in reduced]
    indexed[0].save(OUT / f"{name}.gif", save_all=True, append_images=indexed[1:],
                    duration=100, loop=0, optimize=True)
    output_frames[len(output_frames)//2].save(OUT / f"{name}-poster.jpg", quality=94)
    evidence = dict(mode=mode, source_run=raw.name, mission=mission,
        mission_exit=mission_exit,
        frames=len(output_frames), displayed_seconds=len(output_frames)/10,
        wall_window_s=[selected[0]["wall"] - start, selected[-1]["wall"] - start],
        source_sha256={"frames.jsonl": sha(media / "frames.jsonl"),
                       "samples.jsonl": sha(raw / "mission/samples.jsonl"),
                       "results.json": sha(raw / "mission/results.json"),
                       "room.sdf": sha(raw / "launch/room.sdf")},
        selected_sources=sources)
    # Compact source-data files let readers inspect timing and the actual map.
    (OUT / f"gazebo-{mode}-frames.json").write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8", newline="\n")
    return evidence


def occupancy(raw):
    path = raw / "media/map.json"
    grid = json.loads(path.read_text())
    (OUT / "gazebo-mapping-grid.json").write_text(json.dumps(grid)+"\n", encoding="utf-8", newline="\n")
    cells = np.array(grid["data"]).reshape(grid["height"], grid["width"])
    # Use the published occupancy values directly: unknown=-1, free=0,
    # positive occupancy probabilities remain a continuous gray scale.
    image = np.where(cells < 0, .55, 1 - cells / 100)
    x, y, resolution = grid["origin"]["x"], grid["origin"]["y"], grid["resolution"]
    plt.rcParams.update({"font.family": "Microsoft YaHei", "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(7, 6), layout="constrained")
    ax.imshow(image, cmap="gray", vmin=0, vmax=1, origin="lower", interpolation="nearest",
              extent=(x, x+grid["width"]*resolution, y, y+grid["height"]*resolution))
    ax.set(xlabel="地图 x（m）", ylabel="地图 y（m）", title="三维演示建图会话保存的二维占用栅格", aspect="equal")
    ax.scatter(0, 0, marker="o", color="#12649b", s=40, label="建图起点附近")
    ax.legend(handles=[Patch(facecolor="black", label="障碍"), Patch(facecolor="white", edgecolor="gray", label="可通行"),
                       Patch(facecolor=".55", label="未知"), ax.collections[0]], loc="upper left")
    fig.savefig(OUT / "gazebo-mapping-grid.png", dpi=170)
    plt.close(fig)
    return dict(source=raw.name, raw_sha256=sha(path), resolution_m=resolution,
                width=grid["width"], height=grid["height"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", required=True, type=Path)
    args = parser.parse_args()
    runs = [movie(args.raw_root / f"presentation-{name}-01", name) for name in ("mapping", "navigation")]
    manifest = dict(date="2026-11-12", kind="fresh Gazebo RGB-D closed-loop demonstration",
        recording_script_sha256=sha(ROOT / "tools/record_gazebo_demonstration.py"),
        rendering_script_sha256=sha(Path(__file__)),
        source_root="/home/enos/wheeltec_vision_sim/results/presentation-<mode>-01",
        changes=["Two static observer cameras added; original world geometry and vehicle preserved.",
                 "Observer images only recorded for presentation; estimator uses original onboard images.",
                 "New mapping database reused in navigation demonstration.",
                 "Every second detail frame selected; overview matched within 80 ms simulation time.",
                 "Display 10 frames per second, uniform intervals, time labels are recorded wall time.",
                 "Resize and label recorded images; global palette quantization for GIF.",
                 "Navigation target from recorded expected_world_goal projected through observer SDF camera, overlaid as a yellow crosshair.",
                 "Demonstration sessions stored separately from the original comparison trials."],
        runs=[{k: v for k,v in run.items() if k != "selected_sources"} for run in runs],
        occupancy=occupancy(args.raw_root / "presentation-mapping-01"))
    manifest["outputs"] = [dict(file=p.name, bytes=p.stat().st_size, sha256=sha(p))
                            for p in sorted(OUT.glob("gazebo-*"))
                            if p.name != "gazebo-demonstration-provenance.json"]
    (OUT / "gazebo-demonstration-provenance.json").write_text(
        json.dumps(manifest, indent=2)+"\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
