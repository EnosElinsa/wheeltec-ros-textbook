"""Render measured simulation paths; optionally verify and import original JSONL.

Default: python tools/render_simulation_figures.py
Import:  python tools/render_simulation_figures.py --raw-root /path/to/raw-files
Optional dependencies: numpy, matplotlib, Pillow. No simulator is launched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon, Rectangle
from PIL import Image, __version__ as pillow_version


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/08-advanced-applications/simulation-results"
RUNS = {
    "mapping-baseline": "mapping-all-05",
    "localization-baseline": "localization-baseline-04",
    "localization-stereo": "localization-stereo-01",
    "localization-vio": "localization-vio-05",
}
BLUE, ORANGE, GREEN, RED = "#12649b", "#ad5700", "#14775c", "#ad364a"
PHASES = {
    "startup": "启动", "prepare": "试验准备", "motion": "直行、转弯与停车",
    "route": "短程到点", "vision": "视觉中断试验", "imu": "IMU 中断试验",
    "depth": "深度中断试验", "pause": "暂停与恢复", "old_goal": "旧任务阻止恢复",
    "obstacle": "前方障碍试验", "actuator_lease": "执行器断收试验",
}


def summary(name):
    return json.loads((OUT / f"{name}-2026-11-12.json").read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_raw(raw_root):
    fields = ["wall_s", "sim_s", "phase", "gt_stamp_ns", "x_m", "y_m", "yaw_rad",
              "gt_fresh", "safe_v_mps", "wheel_v_mps", "wheel_fresh", "state"]
    provenance = []
    for name, run in RUNS.items():
        source = raw_root / f"{name}.jsonl"
        report = summary(name)
        if digest(source) != report["sample_sha256"]:
            raise ValueError(f"Original sample hash mismatch: {name}")
        rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
        first_wall = rows[0]["wall"]
        destination = OUT / f"{name}-path.csv"
        with destination.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                pose = row.get("ground_truth")
                fresh = row.get("evidence_fresh", {})
                derived = dict(wall_s=row["wall"] - first_wall, sim_s=row["ros_ns"] * 1e-9,
                               phase=row["phase"], gt_fresh=int(fresh.get("gt", False)),
                               safe_v_mps=row["safe_v"], wheel_v_mps=row["wheel_v"],
                               wheel_fresh=int(fresh.get("wheel", False)),
                               state=row.get("health", {}).get("state", "unknown"))
                if pose:
                    x, y, z, w = pose["quaternion"]
                    derived.update(gt_stamp_ns=pose["stamp_ns"], x_m=pose["xyz"][0],
                                   y_m=pose["xyz"][1],
                                   yaw_rad=math.atan2(2 * (w * z + x * y), 1 - 2 * (y*y + z*z)))
                writer.writerow(derived)
        provenance.append(dict(name=name, run=run, raw_sha256=digest(source), rows=len(rows),
                               first_wall=first_wall, csv=destination.name,
                               csv_sha256=digest(destination)))
    manifest = dict(
        schema=1, experiment_date="2026-11-12", runs=provenance,
        source_root="/home/enos/wheeltec_vision_sim/results/<run>/mission/samples.jsonl",
        transformations=[
            "All JSONL rows retained in CSV, including missing/stale truth and startup.",
            "Wall time is relative to the first JSONL row; simulation nanoseconds converted to seconds.",
            "World x/y copied without fitting, scaling, smoothing or path interpolation.",
            "Yaw derived from recorded xyzw quaternion with atan2.",
            "Missing or nonfresh truth is drawn as a gap. Plot lines link adjacent valid observations only.",
            "Animation selects every 10th row plus the last, no interpolated vehicle positions; uniform 100 ms display intervals compress time approximately.",
        ],
        scene=dict(
            revision="d6092f1a270ec64b24c11f8c1c9b1c8d5d473043",
            source="wheeltec_vision_sim/worlds/room.sdf",
            room_floor_m=[12, 10], wall_thickness_m=.15,
            landmarks_xy_m=[[2, 1.8], [0, 3.5], [-2, -1.8], [3.8, -2.2], [-4, 2]],
            landmark_size_m=[.45, .55, 1.1],
            chassis_length_width_m=[.46, .32], wheelbase_m=.34),
        scope="Derived visualization of existing measured sessions, not new trials or planner reference paths.",
    )
    (OUT / "path-figure-provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def data(name):
    manifest = json.loads((OUT / "path-figure-provenance.json").read_text(encoding="utf-8"))
    record = next(r for r in manifest["runs"] if r["name"] == name)
    path = OUT / record["csv"]
    if digest(path) != record["csv_sha256"]:
        raise ValueError(f"Derived CSV hash mismatch: {name}")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = {key: np.array([float(r[key]) if r[key] else np.nan for r in rows])
              for key in ("wall_s", "sim_s", "x_m", "y_m", "yaw_rad", "gt_fresh",
                          "safe_v_mps", "wheel_v_mps", "wheel_fresh")}
    result.update(phase=np.array([r["phase"] for r in rows]),
                  state=np.array([r["state"] for r in rows]), first_wall=record["first_wall"])
    good = (result["gt_fresh"] == 1) & np.isfinite(result["x_m"]) & np.isfinite(result["y_m"])
    result["xy"] = np.column_stack([result["x_m"], result["y_m"]])
    result["xy"][~good] = np.nan
    return result


def axis(ax):
    ax.set(xlabel="世界 x（m）", ylabel="世界 y（m）", aspect="equal")
    ax.grid(color="#e3e8ed", linewidth=.65)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#a5adb6")


def room(ax):
    for x, y, w, h in [(0, 5, 12, .15), (0, -5, 12, .15),
                        (6, 0, .15, 10), (-6, 0, .15, 10)]:
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor="#647284", zorder=1))
    for i, (x, y) in enumerate([(2, 1.8), (0, 3.5), (-2, -1.8), (3.8, -2.2), (-4, 2)]):
        ax.add_patch(Rectangle((x-.225, y-.275), .45, .55, facecolor="#c9a65a",
                               edgecolor="#806730", zorder=1))
        ax.text(x+.35, y+.1, f"L{i}", fontsize=10, color="#685124")
    axis(ax)
    ax.set(xlim=(-6.4, 6.4), ylim=(-5.4, 5.4))


def body(ax, xy, yaw, color, alpha=.2):
    corners = np.array([[-.06, -.16], [.40, -.16], [.40, .16], [-.06, .16]])
    rotation = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
    polygon = Polygon(corners @ rotation.T + xy, facecolor=color, edgecolor=color,
                      alpha=alpha, linewidth=1.4, zorder=3)
    ax.add_patch(polygon)
    ax.annotate("", xy=xy + .35*np.array([math.cos(yaw), math.sin(yaw)]), xytext=xy,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8))


def save(fig, name):
    svg_path = OUT / f"{name}.svg"
    fig.savefig(svg_path, metadata={"Date": None})
    # Matplotlib's text writer uses host line endings; published byte hashes use LF.
    svg_path.write_bytes(svg_path.read_bytes().replace(b"\r\n", b"\n"))
    fig.savefig(OUT / f"{name}.png", dpi=170)
    plt.close(fig)


def overview():
    d = data("mapping-baseline")
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.6), layout="constrained")
    xy = d["xy"]
    good = np.flatnonzero(np.isfinite(xy[:, 0]))
    start, end = good[0], good[-1]
    room(axes[0])
    axes[0].plot(*xy.T, color=BLUE, lw=2, label="实际行驶路径")
    axes[0].scatter(*xy[start], marker="o", color=BLUE, s=50, zorder=5)
    axes[0].scatter(*xy[end], marker="s", color=RED, s=45, zorder=5)
    axes[0].set_title("A  路径在整个房间中的位置", loc="left", fontsize=13)
    axes[0].legend(loc="lower right", frameon=True)
    ax = axes[1]
    axis(ax)
    ax.plot(*xy.T, color=BLUE, lw=2.3)
    body(ax, xy[start], d["yaw_rad"][start], BLUE)
    body(ax, xy[end], d["yaw_rad"][end], RED)
    ax.scatter(*xy[start], marker="o", color=BLUE, s=45, zorder=5)
    ax.scatter(*xy[end], marker="s", color=RED, s=45, zorder=5)
    ax.annotate("起点", xy=xy[start], xytext=(-3.05, -.4), color=BLUE,
                arrowprops=dict(arrowstyle="-", color=BLUE))
    ax.annotate("会话终点", xy=xy[end], xytext=(-2.2, 2.85), color=RED,
                arrowprops=dict(arrowstyle="-", color=RED))
    report = summary("mapping-baseline")
    for scenario, label, offset in [("vision", "① 视觉中断", (-.95, .18)),
                                    ("imu", "② IMU 中断", (-1.15, .1)),
                                    ("obstacle", "③ 前方障碍", (-1.35, .0))]:
        event = next(r for r in report["scenario_results"]["results"] if r["scenario"] == scenario)
        t = event.get("onset_wall", event["started_wall"]) - d["first_wall"]
        i = max(good[0], np.searchsorted(d["wall_s"], t, side="right") - 1)
        ax.scatter(*xy[i], marker="D", color=RED, s=28, zorder=6)
        ax.annotate(label, xy=xy[i], xytext=xy[i]+offset, fontsize=10,
                    arrowprops=dict(arrowstyle="-", color="#6f7882"), color="#303b47")
    ax.set(xlim=(-3.45, -.35), ylim=(-.6, 3.2))
    ax.set_title("B  路径放大与代表性试验位置", loc="left", fontsize=13)
    fig.suptitle("车辆实际走了哪里？——RGB-D 基线建图会话", fontsize=16)
    fig.supxlabel("依据 Gazebo 世界真值绘制；故障标记为相应事件附近的记录位置；车辆轮廓表示起、终姿态。", fontsize=10)
    save(fig, "measured-room-path")


def routes():
    fig, axes = plt.subplots(3, 1, figsize=(7.8, 9.1), layout="constrained")
    for ax, name, title in zip(axes, ["localization-baseline", "localization-stereo", "localization-vio"],
                               ["A  RGB-D + 轮速/IMU EKF", "B  双目 VO", "C  双目 VIO（首轮配置）"]):
        d = data(name)
        results = summary(name)["scenario_results"]["results"]
        axis(ax)
        for i, color in enumerate([BLUE, ORANGE, GREEN]):
            xy = np.where((d["phase"] == f"route/{i}")[:, None], d["xy"], np.nan)
            ax.plot(*xy.T, color=color, lw=2.5, label=f"第 {i+1} 个任务")
            good = np.flatnonzero(np.isfinite(xy[:, 0]))
            ax.scatter(*xy[good[0]], marker="|", color=color, s=80, linewidths=2, zorder=6)
            result = next(r for r in results if r["scenario"] == "route" and r["trial"] == i)
            goal, end = np.array(result["expected_world_goal"][:2]), np.array(result["actual_world_endpoint"][:2])
            ax.add_patch(Circle(goal, .25, fill=False, color=color, lw=1.1, linestyle="--", alpha=.7))
            ax.scatter(*goal, color=color, marker="*", s=110, zorder=5)
            ax.scatter(*end, color=color, marker="o", s=35, zorder=6)
            ax.plot([end[0], goal[0]], [end[1], goal[1]], color=color, ls=":", lw=1)
            ax.text(end[0], -.23, f"误差 {result['position_error_m']:.3f} m", ha="center", fontsize=10, color=color)
            ax.text(goal[0], goal[1]+.28, f"目标 {i+1}", color=color, fontsize=10, ha="center")
        ax.set(xlim=(-3.2, -.95), ylim=(-.32, .56))
        ax.set_title(title, loc="left", fontsize=12)
        ax.set_xlabel("")
    axes[-1].set_xlabel("世界 x（m）")
    handles = [Line2D([], [], marker="*", color="#475569", ls="none", markersize=10, label="请求目标"),
               Line2D([], [], marker="o", color="#475569", ls="none", label="实际终点"),
               Line2D([], [], color="#475569", ls="--", label="位置容差 0.25 m")]
    fig.legend(handles=handles, loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle("三种方案的短程到点轨迹", fontsize=16)
    save(fig, "measured-navigation-routes")


def fault_response():
    d = data("localization-baseline")
    event = next(r for r in summary("localization-baseline")["scenario_results"]["results"]
                 if r["scenario"] == "imu" and r["trial"] == 0)
    t = d["wall_s"] - (event["onset_wall"] - d["first_wall"])
    recovered = event["recovery_wall"] - event["onset_wall"]
    selection = (t >= -1) & (t <= 4)
    points = np.flatnonzero(selection & np.isfinite(d["xy"][:, 0]))
    displacement = np.linalg.norm(d["xy"] - d["xy"][points[0]], axis=1)
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.1), sharex=True, layout="constrained")
    for ax in axes:
        ax.axvspan(0, recovered, color="#f7e6d5", zorder=0)
        ax.axvline(0, color=RED, ls="--", lw=1.5)
        ax.axvline(recovered, color="#667381", ls=":", lw=1.3)
        ax.grid(alpha=.2)
        ax.set_xlim(-1, 4)
    axes[0].plot(t[selection], d["safe_v_mps"][selection], color=BLUE, marker="o", ms=3, lw=1.4, label="最终速度指令")
    wheel = d["wheel_v_mps"].copy()
    wheel[d["wheel_fresh"] != 1] = np.nan
    axes[0].plot(t[selection], wheel[selection], color=ORANGE, marker="s", ms=3, lw=1.4, label="轮速观测")
    speed_top = 1.3 * max(np.nanmax(d["safe_v_mps"][selection]), np.nanmax(wheel[selection]))
    axes[0].set(ylabel="前进速度（m/s）", ylim=(-.008, speed_top))
    axes[0].legend(loc="upper right", ncol=2)
    axes[0].text(.04, speed_top*.93, "停止 IMU 输入", color=RED, fontsize=10)
    axes[0].text(recovered+.05, speed_top*.93, "恢复输入", color="#475569", fontsize=10)
    axes[1].plot(t[selection], displacement[selection], color=GREEN, marker="o", ms=3, lw=1.5)
    axes[1].set(xlabel="距故障注入的墙钟时间（s）", ylabel="距窗口起点的直线距离（m）",
                ylim=(-.003, np.nanmax(displacement[selection])*1.25))
    fig.suptitle("输入中断后，指令与车辆运动怎样变化？", fontsize=16)
    fig.supxlabel("RGB-D 导航会话，第 1 次 IMU 停流；约 0.1 s 记录一次，连线辅助阅读，不用于精确超时测量。", fontsize=10)
    save(fig, "measured-fault-stop")


def animation():
    d = data("mapping-baseline")
    xy = d["xy"]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5), layout="constrained")
    room(axes[0])
    axes[0].set_title("房间中的位置", fontsize=12)
    axis(axes[1])
    axes[1].set(xlim=(-3.45, -.35), ylim=(-.6, 3.2), title="车辆与路径放大")
    lines, vehicles, arrows = [], [], []
    for ax in axes:
        ax.plot(*xy.T, color="#d5dce3", lw=1.5)
        lines.append(ax.plot([], [], color=BLUE, lw=2)[0])
        vehicle = Polygon(np.zeros((4, 2)), facecolor=BLUE, edgecolor="#174263", alpha=.75, zorder=5)
        ax.add_patch(vehicle)
        vehicles.append(vehicle)
        arrows.append(ax.plot([], [], color="white", lw=1.8, zorder=6)[0])
    heading = fig.suptitle("", fontsize=13)
    fig.supxlabel("世界真值轨迹回放；灰线为完整记录，蓝线为已回放路径；约每 10 条记录取一帧，加速播放。", fontsize=9)
    frames = list(range(0, len(xy), 10))
    if frames[-1] != len(xy)-1:
        frames.append(len(xy)-1)
    def update(i):
        valid = np.all(np.isfinite(xy[i]))
        for line, vehicle, arrow in zip(lines, vehicles, arrows):
            line.set_data(*xy[:i+1].T)
            vehicle.set_visible(valid)
            arrow.set_visible(valid)
            if valid:
                yaw = d["yaw_rad"][i]
                corners = np.array([[-.06, -.16], [.40, -.16], [.40, .16], [-.06, .16]])
                rotation = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
                vehicle.set_xy(corners @ rotation.T + xy[i])
                vehicle.set_facecolor(RED if d["state"][i] == "STOPPED" else BLUE)
                tip = xy[i] + .34*np.array([math.cos(yaw), math.sin(yaw)])
                arrow.set_data([xy[i, 0], tip[0]], [xy[i, 1], tip[1]])
        phase = PHASES.get(d["phase"][i].split("/")[0], d["phase"][i])
        heading.set_text(f"RGB-D 建图回放  |  墙钟 {d['wall_s'][i]:.1f} s  |  {phase}  |  {d['state'][i]}")
        return lines + vehicles + arrows + [heading]
    replay = FuncAnimation(fig, update, frames=frames, interval=100, blit=False)
    replay.save(OUT / "measured-mapping-replay.gif", writer=PillowWriter(fps=10), dpi=105)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--skip-animation", action="store_true")
    args = parser.parse_args()
    fonts = {f.name for f in font_manager.fontManager.ttflist}
    font = next((f for f in ["Microsoft YaHei", "Noto Sans CJK SC", "SimHei"] if f in fonts), "DejaVu Sans")
    with plt.rc_context({"font.family": font, "font.size": 11, "axes.unicode_minus": False,
                         "svg.fonttype": "path", "savefig.facecolor": "white"}):
        if args.raw_root:
            import_raw(args.raw_root)
        overview()
        routes()
        fault_response()
        if not args.skip_animation:
            animation()
    manifest_path = OUT / "path-figure-provenance.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rendering"] = dict(generator="tools/render_simulation_figures.py",
                                  generator_sha256=digest(Path(__file__)),
                                  matplotlib=matplotlib.__version__, numpy=np.__version__,
                                  pillow=pillow_version, font=font)
    outputs = []
    for path in sorted(OUT.glob("measured-*")):
        item = dict(file=path.name, bytes=path.stat().st_size, sha256=digest(path))
        if path.suffix in {".png", ".gif"}:
            with Image.open(path) as raster:
                item.update(width_px=raster.width, height_px=raster.height,
                            frames=getattr(raster, "n_frames", 1))
                if path.suffix == ".gif":
                    duration = 0
                    for i in range(raster.n_frames):
                        raster.seek(i)
                        duration += raster.info.get("duration", 0)
                    item["display_duration_s"] = duration / 1000
        outputs.append(item)
    manifest["outputs"] = outputs
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
    print("Rendered measured paths, goal endpoints, fault response and requested replay.")


if __name__ == "__main__":
    main()
