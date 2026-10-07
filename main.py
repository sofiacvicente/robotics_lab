from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path

import numpy as np

try:
    import mujoco
except ModuleNotFoundError as exc:
    raise SystemExit(
        "MuJoCo não está instalado no Python atual. No WSL, execute:\n"
        "python3 -m pip install -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "golfer.xml"
DEFAULT_OUTPUT = ROOT / "results.csv"
SWING_DURATION = 2.0


def load_model() -> tuple[mujoco.MjModel, mujoco.MjData]:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Modelo MuJoCo não encontrado: {MODEL_PATH}")
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)
    return model, data


def joint_qpos_index(model: mujoco.MjModel, name: str) -> int:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    if joint_id < 0:
        raise ValueError(f"Articulação não encontrada no modelo: {name}")
    return int(model.jnt_qposadr[joint_id])


def body_id(model: mujoco.MjModel, name: str) -> int:
    result = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if result < 0:
        raise ValueError(f"Corpo não encontrado no modelo: {name}")
    return result


def reset_swing(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    data.qpos[joint_qpos_index(model, "hip_rotation")] = 0.0
    data.qpos[joint_qpos_index(model, "hip_flexion")] = 0.0
    data.qpos[joint_qpos_index(model, "torso_rotation")] = 0.0
    data.qpos[joint_qpos_index(model, "right_shoulder_lift")] = 0.0
    data.qpos[joint_qpos_index(model, "right_shoulder")] = -0.8
    data.qpos[joint_qpos_index(model, "right_elbow")] = 0.2
    data.qpos[joint_qpos_index(model, "right_wrist_hinge")] = 0.0
    data.qpos[joint_qpos_index(model, "left_shoulder_lift")] = 0.0
    data.qpos[joint_qpos_index(model, "left_shoulder")] = -0.8
    data.qpos[joint_qpos_index(model, "left_elbow")] = 0.2
    data.qpos[joint_qpos_index(model, "left_knee")] = 0.12
    data.qpos[joint_qpos_index(model, "right_knee")] = 0.12
    mujoco.mj_forward(model, data)


def swing_targets(t: float) -> tuple[float, ...]:
    """Sequence the backswing, then unwind pelvis, torso, arms, and club."""
    address = (0.0, 0.0, 0.0, 0.0, -0.8, 0.2, 0.0, 0.0, -0.8, 0.2, 0.12, 0.12)
    takeaway = (0.0, 0.0, 0.0, -0.12, -0.8, -0.2, 0.08, 0.12, -0.8, -0.2, 0.20, 0.15)
    top_of_backswing = (
        -0.38, 0.08, -0.55, 0.57, -0.41, -1.20, -1.20, -0.64, -0.63, -0.25, 0.42, 0.20
    )
    impact = (0.36, 0.30, -0.20, 0.0, -0.5, 0.5, 0.0, 0.0, -0.5, 0.5, 0.16, 0.28)
    finish = (0.42, 0.02, 0.18, -0.25, -1.05, -0.35, -0.15, 0.25, -1.05, -0.35, 0.10, 0.40)

    phase = min(max(t / SWING_DURATION, 0.0), 1.0)

    def blend(
        start_pose: tuple[float, ...],
        end_pose: tuple[float, ...],
        start: float,
        end: float,
    ) -> tuple[float, ...]:
        progress = min(max((phase - start) / (end - start), 0.0), 1.0)
        progress = progress**2 * (3.0 - 2.0 * progress)
        return tuple(
            start_value + (end_value - start_value) * progress
            for start_value, end_value in zip(start_pose, end_pose)
        )

    if phase < 0.12:
        return blend(address, takeaway, 0.04, 0.12)
    if phase < 0.43:
        return blend(takeaway, top_of_backswing, 0.12, 0.43)
    down = tuple(
        blend(top_of_backswing, impact, start, end)[index]
        for index, (start, end) in enumerate(
            (
                (0.43, 0.62),
                (0.43, 0.64),
                (0.45, 0.66),
                (0.48, 0.68),
                (0.48, 0.68),
                (0.50, 0.72),
                (0.43, 0.62),
                (0.48, 0.68),
                (0.48, 0.68),
                (0.50, 0.72),
                (0.42, 0.58),
                (0.44, 0.62),
            )
        )
    )
    if phase < 0.78:
        return down
    return tuple(
        blend(impact, finish, start, 1.0)[index]
        for index, start in enumerate(
            (0.78, 0.80, 0.82, 0.84, 0.84, 0.84, 0.84, 0.84, 0.84, 0.84, 0.78, 0.80)
        )
    )


def apply_controls(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    targets = swing_targets(data.time)
    data.ctrl[:] = targets


def simulate(
    duration: float,
    disturbance=None,
    on_step=None,
    timestep: float | None = None,
) -> dict[str, float | int | bool]:
    """Corre um swing sem janela e devolve as medicoes do impacto.

    disturbance: funcao opcional f(model, data), chamada antes de cada passo,
        que escreve binarios de perturbacao em data.qfrc_applied (Tarefa 2).
    on_step: funcao opcional f(model, data, club_speed), chamada depois de
        cada passo, para registar series temporais.
    timestep: passo de integracao alternativo (teste de sensibilidade numerica).
    """
    model, data = load_model()
    if timestep is not None:
        model.opt.timestep = timestep
    reset_swing(model, data)
    ball_id = body_id(model, "golf_ball")
    club_geom_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_GEOM, "club_face_collision"
    )
    ball_geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "ball")
    if club_geom_id < 0 or ball_geom_id < 0:
        raise ValueError(
            "O modelo precisa das geometrias 'club_face_collision' e 'ball'."
        )
    ball_joint_id = int(model.body_jntadr[ball_id])
    if ball_joint_id < 0:
        raise ValueError("A bola precisa de uma articulacao livre para se mover.")
    ball_velocity_address = int(model.jnt_dofadr[ball_joint_id])
    ball_initial = data.xpos[ball_id].copy()
    peak_club_speed = 0.0
    peak_ball_speed = 0.0
    peak_ball_height = float(ball_initial[2])
    impact_time = math.nan
    impact_club_speed = math.nan
    ball_velocity_10ms_after_impact = np.full(3, math.nan)
    ball_velocity_sampled = False
    club_velocity = np.zeros(6)
    contact_steps = 0

    while data.time < duration:
        apply_controls(model, data)
        if disturbance is not None:
            disturbance(model, data)
        mujoco.mj_step(model, data)
        mujoco.mj_objectVelocity(
            model,
            data,
            mujoco.mjtObj.mjOBJ_GEOM,
            club_geom_id,
            club_velocity,
            0,
        )
        club_speed = float(np.linalg.norm(club_velocity[3:]))
        if on_step is not None:
            on_step(model, data, club_speed)
        ball_speed = float(np.linalg.norm(data.cvel[ball_id][3:]))
        peak_club_speed = max(peak_club_speed, club_speed)
        peak_ball_speed = max(peak_ball_speed, ball_speed)
        peak_ball_height = max(peak_ball_height, float(data.xpos[ball_id, 2]))
        if data.ncon > 0:
            for contact_index in range(data.ncon):
                contact = data.contact[contact_index]
                if {contact.geom1, contact.geom2} == {ball_geom_id, club_geom_id}:
                    contact_steps += 1
                    if math.isnan(impact_time):
                        impact_time = float(data.time)
                        impact_club_speed = club_speed
                    break
        if (
            not math.isnan(impact_time)
            and not ball_velocity_sampled
            and data.time >= impact_time + 0.01
        ):
            ball_velocity_10ms_after_impact[:] = data.qvel[
                ball_velocity_address : ball_velocity_address + 3
            ]
            ball_velocity_sampled = True

    ball_final = data.xpos[ball_id].copy()
    result: dict[str, float | int | bool] = {
        "duration_s": float(data.time),
        "impact_detected": not math.isnan(impact_time),
        "impact_time_s": impact_time,
        "club_head_speed_at_impact_m_s": impact_club_speed,
        "peak_ball_speed_m_s": peak_ball_speed,
        "ball_velocity_10ms_after_impact_x_m_s": float(
            ball_velocity_10ms_after_impact[0]
        ),
        "ball_velocity_10ms_after_impact_y_m_s": float(
            ball_velocity_10ms_after_impact[1]
        ),
        "ball_velocity_10ms_after_impact_z_m_s": float(
            ball_velocity_10ms_after_impact[2]
        ),
        "ball_peak_height_m": peak_ball_height,
        "ball_final_x_m": float(ball_final[0]),
        "ball_final_y_m": float(ball_final[1]),
        "ball_displacement_m": float(math.sqrt(((ball_final - ball_initial) ** 2).sum())),
        "peak_club_head_speed_m_s": peak_club_speed,
        "contact_steps": contact_steps,
    }
    return result


def write_result(path: Path, result: dict[str, float | int | bool]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(result))
        if write_header:
            writer.writeheader()
        writer.writerow(result)


def run_viewer() -> None:
    try:
        import mujoco.viewer
    except ImportError as exc:
        raise SystemExit(
            "O visualizador precisa de uma sessão gráfica. No WSL, use WSLg "
            "ou execute os testes sem janela com: python3 main.py --test"
        ) from exc

    model, data = load_model()
    reset_swing(model, data)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = (-0.05, 0.0, 0.95)
        viewer.cam.distance = 3.5
        viewer.cam.azimuth = 100
        viewer.cam.elevation = -12
        while viewer.is_running():
            start = time.perf_counter()
            apply_controls(model, data)
            mujoco.mj_step(model, data)
            if data.time >= SWING_DURATION:
                reset_swing(model, data)
            viewer.sync()
            wait = model.opt.timestep - (time.perf_counter() - start)
            if wait > 0:
                time.sleep(wait)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulação de swing de golfe em MuJoCo.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Executa uma simulação sem janela e apresenta as medições.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=SWING_DURATION,
        help="Duração da simulação de teste em segundos (por omissão: 2.0).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="CSV onde guardar os resultados do teste.",
    )
    args = parser.parse_args()

    if args.test:
        if args.duration <= 0:
            parser.error("--duration tem de ser maior que zero")
        result = simulate(args.duration)
        write_result(args.output, result)
        for key, value in result.items():
            print(f"{key}: {value}")
        print(f"Resultados guardados em: {args.output.resolve()}")
    else:
        run_viewer()


if __name__ == "__main__":
    main()