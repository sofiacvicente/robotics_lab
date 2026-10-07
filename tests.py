"""
Testes:
    1. Perturbacoes (tremor) em cada uma das 12 articulacoes
    2. Swing nominal: velocidades, smash factor e angulos de saida da bola
    3. Binarios maximos usados por cada articulacao
    4. Ritmo do swing (razao backswing/downswing)
    5. Sensibilidade ao passo de integracao
    6. Validacao basica: pendulo simples e ressalto da bola

 A direcao do alvo e +Y (o lado do pe esquerdo).
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path

import mujoco
import numpy as np

import main


JOINTS = [
    "hip_rotation",
    "hip_flexion",
    "torso_rotation",
    "right_shoulder_lift",
    "right_shoulder",
    "right_elbow",
    "right_wrist_hinge",
    "left_shoulder_lift",
    "left_shoulder",
    "left_elbow",
    "left_knee",
    "right_knee",
]

PERTURBATION_LEVELS_PCT = (5, 10, 20)  # % do binario maximo nominal da articulacao
TREMOR_FREQ_HZ = (8.0, 12.0)  # gama de frequencias do tremor
NOMINAL_DURATION = 4.0  # mais longo que o swing, para a bola parar
TIMESTEPS = (0.0005, 0.001, 0.002)
START_SPEED_THRESHOLD = 0.2  # m/s: velocidade do taco que marca o inicio do backswing



class Recorder:
    """Regista, a cada passo, a velocidade do taco e o binario de cada atuador."""

    def __init__(self) -> None:
        self.times: list[float] = []
        self.club_speed: list[float] = []
        self.peak_torque: np.ndarray | None = None
        self.peak_time: np.ndarray | None = None
        self.actuator_joint: list[str] = []

    def __call__(self, model: mujoco.MjModel, data: mujoco.MjData, club_speed: float) -> None:
        if self.peak_torque is None:
            self.peak_torque = np.zeros(model.nu)
            self.peak_time = np.zeros(model.nu)
            self.actuator_joint = [
                model.joint(int(model.actuator_trnid[i, 0])).name for i in range(model.nu)
            ]
        self.times.append(float(data.time))
        self.club_speed.append(club_speed)
        torque = np.abs(data.actuator_force)
        larger = torque > self.peak_torque
        self.peak_torque[larger] = torque[larger]
        self.peak_time[larger] = data.time

    def peak_by_joint(self) -> dict[str, float]:
        return {name: float(t) for name, t in zip(self.actuator_joint, self.peak_torque)}


class Unstable(Exception):
    pass


def stop_if_unstable(model: mujoco.MjModel, data: mujoco.MjData, club_speed: float) -> None:
    # Quando a simulacao diverge, o MuJoCo reinicia o estado (o tempo volta a 0)
    # e o ciclo do simulate() nunca terminaria; por isso paramos aqui.
    if data.warning[mujoco.mjtWarning.mjWARN_BADQACC].number > 0:
        raise Unstable(f"instavel em t = {data.warning[mujoco.mjtWarning.mjWARN_BADQACC].lastinfo}")


def launch_metrics(result: dict) -> dict[str, float]:
    """Velocidade e angulos de saida da bola, 10 ms depois do impacto."""
    v = np.array([result[f"ball_velocity_10ms_after_impact_{axis}_m_s"] for axis in "xyz"])
    speed = float(np.linalg.norm(v))
    elevation = math.degrees(math.atan2(v[2], math.hypot(v[0], v[1])))
    # 0 graus = direcao do alvo (+Y); positivo = afasta-se do jogador (+X).
    direction = math.degrees(math.atan2(v[0], v[1]))
    club = result["club_head_speed_at_impact_m_s"]
    smash = speed / club if club and not math.isnan(club) else math.nan
    return {
        "ball_launch_speed_m_s": speed,
        "launch_elevation_deg": elevation,
        "launch_direction_deg": direction,
        "smash_factor": smash,
    }


def joint_dof(model: mujoco.MjModel, name: str) -> int:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    if joint_id < 0:
        raise ValueError(f"Articulacao nao encontrada: {name}")
    return int(model.jnt_dofadr[joint_id])


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {path}")


def fmt(value: float, digits: int = 2) -> str:
    return "n/a" if value is None or (isinstance(value, float) and math.isnan(value)) else f"{value:.{digits}f}"


def try_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        return None


def run_nominal(duration: float = main.SWING_DURATION, timestep: float | None = None):
    recorder = Recorder()
    result = main.simulate(duration, on_step=recorder, timestep=timestep)
    return result, recorder



# Teste 1: perturbacoes em cada articulacao
def make_tremor(dof: int, amplitude: float, freq: float, phase: float):
    """Binario sinusoidal (tremor) aplicado a um unico grau de liberdade."""

    def apply(model: mujoco.MjModel, data: mujoco.MjData) -> None:
        data.qfrc_applied[dof] = amplitude * math.sin(2.0 * math.pi * freq * data.time + phase)

    return apply


def test_perturbations(out: Path, seeds: int) -> None:
    print("\n[1] Perturbacoes (tremor) em cada articulacao")
    nominal, recorder = run_nominal()
    if not nominal["impact_detected"]:
        raise SystemExit("O swing nominal nao atinge a bola; corrige isso antes do teste 1.")
    nominal_launch = launch_metrics(nominal)
    peak = recorder.peak_by_joint()
    model, _ = main.load_model()

    runs = []
    total = len(JOINTS) * len(PERTURBATION_LEVELS_PCT) * seeds
    start = time.perf_counter()
    for joint in JOINTS:
        dof = joint_dof(model, joint)
        for pct in PERTURBATION_LEVELS_PCT:
            amplitude = pct / 100.0 * peak[joint]
            for seed in range(seeds):
                rng = np.random.default_rng(seed)
                freq = float(rng.uniform(*TREMOR_FREQ_HZ))
                phase = float(rng.uniform(0.0, 2.0 * math.pi))
                try:
                    result = main.simulate(
                        main.SWING_DURATION,
                        disturbance=make_tremor(dof, amplitude, freq, phase),
                        on_step=stop_if_unstable,
                    )
                except Unstable:
                    print(f"  aviso: {joint} {pct}% semente {seed} ficou instavel; caso ignorado")
                    continue
                launch = launch_metrics(result)
                hit = bool(result["impact_detected"])
                runs.append(
                    {
                        "joint": joint,
                        "level_pct": pct,
                        "seed": seed,
                        "freq_hz": round(freq, 3),
                        "amplitude_nm": round(amplitude, 4),
                        "impact_detected": hit,
                        "impact_time_s": result["impact_time_s"],
                        "delta_impact_time_ms": (result["impact_time_s"] - nominal["impact_time_s"]) * 1000,
                        "club_speed_m_s": result["club_head_speed_at_impact_m_s"],
                        "delta_club_speed_pct": 100
                        * (result["club_head_speed_at_impact_m_s"] / nominal["club_head_speed_at_impact_m_s"] - 1),
                        "ball_launch_speed_m_s": launch["ball_launch_speed_m_s"],
                        "delta_ball_speed_pct": 100
                        * (launch["ball_launch_speed_m_s"] / nominal_launch["ball_launch_speed_m_s"] - 1),
                        "launch_elevation_deg": launch["launch_elevation_deg"],
                        "delta_elevation_deg": launch["launch_elevation_deg"] - nominal_launch["launch_elevation_deg"],
                        "launch_direction_deg": launch["launch_direction_deg"],
                        "delta_direction_deg": launch["launch_direction_deg"] - nominal_launch["launch_direction_deg"],
                    }
                )
        done = len(runs)
        print(f"  {joint:20s} feito ({done}/{total}, {time.perf_counter() - start:.0f} s)")
    write_csv(out / "perturbacoes_todas.csv", runs)

    summary = []
    for joint in JOINTS:
        for pct in PERTURBATION_LEVELS_PCT:
            group = [r for r in runs if r["joint"] == joint and r["level_pct"] == pct]
            hits = [r for r in group if r["impact_detected"]]

            def mean_abs(key: str) -> float:
                return float(np.mean([abs(r[key]) for r in hits])) if hits else math.nan

            summary.append(
                {
                    "joint": joint,
                    "level_pct": pct,
                    "amplitude_nm": group[0]["amplitude_nm"],
                    "impact_rate_pct": 100 * len(hits) / len(group),
                    "mean_abs_delta_impact_time_ms": mean_abs("delta_impact_time_ms"),
                    "mean_abs_delta_club_speed_pct": mean_abs("delta_club_speed_pct"),
                    "mean_abs_delta_ball_speed_pct": mean_abs("delta_ball_speed_pct"),
                    "mean_abs_delta_elevation_deg": mean_abs("delta_elevation_deg"),
                    "mean_abs_delta_direction_deg": mean_abs("delta_direction_deg"),
                }
            )
    write_csv(out / "perturbacoes_resumo.csv", summary)

    level = max(PERTURBATION_LEVELS_PCT)
    print(f"\n  Resumo com perturbacao de {level}% (media dos valores absolutos):")
    print(f"  {'articulacao':20s} {'amp N.m':>8s} {'impacto':>8s} {'dt ms':>7s} {'dv taco':>8s} {'dv bola':>8s} {'d dir':>7s}")
    for row in sorted(
        (r for r in summary if r["level_pct"] == level),
        key=lambda r: -(r["mean_abs_delta_direction_deg"] if not math.isnan(r["mean_abs_delta_direction_deg"]) else 1e9),
    ):
        print(
            f"  {row['joint']:20s} {row['amplitude_nm']:8.2f} {row['impact_rate_pct']:7.0f}% "
            f"{fmt(row['mean_abs_delta_impact_time_ms'], 1):>7s} {fmt(row['mean_abs_delta_club_speed_pct'], 1):>7s}% "
            f"{fmt(row['mean_abs_delta_ball_speed_pct'], 1):>7s}% {fmt(row['mean_abs_delta_direction_deg'], 1):>6s}°"
        )

    plt = try_pyplot()
    if plt is not None:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        x = np.arange(len(JOINTS))
        width = 0.8 / len(PERTURBATION_LEVELS_PCT)
        for k, pct in enumerate(PERTURBATION_LEVELS_PCT):
            rows = [next(r for r in summary if r["joint"] == j and r["level_pct"] == pct) for j in JOINTS]
            axes[0].bar(x + k * width, [r["mean_abs_delta_direction_deg"] for r in rows], width, label=f"{pct}%")
            axes[1].bar(x + k * width, [r["mean_abs_delta_ball_speed_pct"] for r in rows], width, label=f"{pct}%")
        for ax, title in zip(axes, ("Desvio na direcao de saida da bola (graus)", "Variacao da velocidade da bola (%)")):
            ax.set_xticks(x + width, JOINTS, rotation=60, ha="right", fontsize=8)
            ax.set_title(title)
            ax.legend(title="Perturbacao")
        fig.tight_layout()
        fig.savefig(out / "perturbacoes.png", dpi=150)
        plt.close(fig)
        print(f"  -> {out / 'perturbacoes.png'}")




# Testes 2, 3 e 4: swing nominal, binarios e ritmo
def test_nominal(out: Path) -> None:
    print("\n[2] Swing nominal")
    result, _ = run_nominal(NOMINAL_DURATION)
    launch = launch_metrics(result)
    model, _ = main.load_model()
    row = {
        "impact_detected": result["impact_detected"],
        "impact_time_s": result["impact_time_s"],
        "club_head_speed_at_impact_m_s": result["club_head_speed_at_impact_m_s"],
        "peak_club_head_speed_m_s": result["peak_club_head_speed_m_s"],
        **launch,
        "contact_duration_ms": result["contact_steps"] * model.opt.timestep * 1000,
        "ball_peak_height_m": result["ball_peak_height_m"],
        "ball_displacement_m": result["ball_displacement_m"],
    }
    write_csv(out / "nominal.csv", [row])
    for key, value in row.items():
        print(f"  {key:32s} {value if isinstance(value, bool) else fmt(value, 3)}")


def test_torques(out: Path) -> None:
    print("\n[3] Binarios maximos por articulacao (swing nominal)")
    _, recorder = run_nominal()
    model, _ = main.load_model()
    rows = []
    for i, joint in enumerate(recorder.actuator_joint):
        has_limit = bool(model.actuator_forcelimited[i])
        rows.append(
            {
                "joint": joint,
                "peak_torque_nm": float(recorder.peak_torque[i]),
                "time_of_peak_s": float(recorder.peak_time[i]),
                "force_limit_nm": float(model.actuator_forcerange[i, 1]) if has_limit else math.nan,
            }
        )
    write_csv(out / "binarios.csv", rows)
    for row in sorted(rows, key=lambda r: -r["peak_torque_nm"]):
        print(f"  {row['joint']:20s} {row['peak_torque_nm']:7.1f} N.m  (t = {row['time_of_peak_s']:.2f} s)")


def test_tempo(out: Path) -> None:
    print("\n[4] Ritmo do swing")
    result, recorder = run_nominal()
    t = np.array(recorder.times)
    v = np.array(recorder.club_speed)
    impact = result["impact_time_s"]
    if math.isnan(impact):
        print("  Sem impacto: nao da para calcular o ritmo.")
        return
    moving = np.nonzero((t > 0.05) & (v > START_SPEED_THRESHOLD))[0]
    start = float(t[moving[0]])
    window = (t > start + 0.3) & (t < impact - 0.1)
    top = float(t[np.argmin(np.where(window, v, np.inf))])
    backswing, downswing = top - start, impact - top
    row = {
        "start_s": start,
        "top_of_backswing_s": top,
        "impact_s": impact,
        "backswing_s": backswing,
        "downswing_s": downswing,
        "ratio_backswing_downswing": backswing / downswing,
    }
    write_csv(out / "ritmo.csv", [row])
    write_csv(out / "velocidade_taco.csv", [{"t_s": a, "club_speed_m_s": b} for a, b in zip(t, v)])
    print(f"  inicio {start:.3f} s | topo {top:.3f} s | impacto {impact:.3f} s")
    print(f"  backswing {backswing:.3f} s, downswing {downswing:.3f} s -> razao {backswing / downswing:.2f}:1")

    plt = try_pyplot()
    if plt is not None:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(t, v)
        for x, label in ((start, "inicio"), (top, "topo"), (impact, "impacto")):
            ax.axvline(x, linestyle="--", color="gray")
            ax.text(x, ax.get_ylim()[1] * 0.95, f" {label}", fontsize=8)
        ax.set_xlabel("tempo (s)")
        ax.set_ylabel("velocidade da cabeca do taco (m/s)")
        fig.tight_layout()
        fig.savefig(out / "velocidade_taco.png", dpi=150)
        plt.close(fig)
        print(f"  -> {out / 'velocidade_taco.png'}")




# Teste 5: sensibilidade ao passo de integracao
def test_timestep(out: Path) -> None:
    print("\n[5] Sensibilidade ao passo de integracao")
    rows = []
    for dt in TIMESTEPS:
        start = time.perf_counter()
        try:
            result = main.simulate(main.SWING_DURATION, timestep=dt, on_step=stop_if_unstable)
        except Unstable:
            print(f"  dt={dt:.4f} s: a simulacao torna-se instavel (diverge)")
            rows.append({"timestep_s": dt, "impact_detected": "instavel"})
            continue
        elapsed = time.perf_counter() - start
        launch = launch_metrics(result)
        rows.append(
            {
                "timestep_s": dt,
                "impact_detected": result["impact_detected"],
                "impact_time_s": result["impact_time_s"],
                "club_head_speed_at_impact_m_s": result["club_head_speed_at_impact_m_s"],
                "ball_launch_speed_m_s": launch["ball_launch_speed_m_s"],
                "launch_elevation_deg": launch["launch_elevation_deg"],
                "launch_direction_deg": launch["launch_direction_deg"],
                "wall_time_s": elapsed,
            }
        )
        print(
            f"  dt={dt:.4f} s: impacto={result['impact_detected']} t={fmt(result['impact_time_s'], 3)} s "
            f"v_taco={fmt(result['club_head_speed_at_impact_m_s'])} m/s "
            f"v_bola={fmt(launch['ball_launch_speed_m_s'])} m/s "
            f"elev={fmt(launch['launch_elevation_deg'], 1)}° dir={fmt(launch['launch_direction_deg'], 1)}° "
            f"({elapsed:.2f} s de calculo)"
        )
    write_csv(out / "passo_integracao.csv", rows)



# Teste 6: validacao basica (pendulo e ressalto da bola)
PENDULUM_XML = """
<mujoco model="pendulo">
  <!-- Mesmas opcoes de integracao que o modelo do jogador. -->
  <option gravity="0 0 -9.81" timestep="0.001" integrator="RK4"/>
  <worldbody>
    <body name="bob" pos="0 0 2">
      <joint name="hinge" type="hinge" axis="0 1 0"/>
      <!-- Massa pontual de 1 kg a {length} m do eixo (haste sem massa). -->
      <inertial pos="0 0 -{length}" mass="1" diaginertia="1e-6 1e-6 1e-6"/>
      <geom type="capsule" fromto="0 0 0 0 0 -{length}" size="0.005" mass="0" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
</mujoco>
"""


def pendulum_period(length: float, amplitude_rad: float, periods: int = 10) -> float:
    model = mujoco.MjModel.from_xml_string(PENDULUM_XML.format(length=length))
    data = mujoco.MjData(model)
    data.qpos[0] = amplitude_rad
    crossings = []
    previous = data.qpos[0]
    while len(crossings) < 2 * periods + 1 and data.time < 100:
        mujoco.mj_step(model, data)
        current = data.qpos[0]
        if previous > 0 >= current or previous < 0 <= current:
            # interpolacao linear do instante em que o angulo passa por zero
            frac = previous / (previous - current)
            crossings.append(data.time - model.opt.timestep * (1 - frac))
        previous = current
    return 2 * float(np.mean(np.diff(crossings)))


def ball_bounce(drop_height: float = 1.0) -> dict[str, float]:
    """Larga a bola do modelo do jogador sobre o chao do mesmo modelo."""
    model, data = main.load_model()
    main.reset_swing(model, data)
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "golf_ball")
    qadr = int(model.jnt_qposadr[model.body_jntadr[ball_body]])
    radius = 0.021
    data.qpos[qadr : qadr + 3] = (3.0, 3.0, drop_height + radius)  # longe do jogador
    mujoco.mj_forward(model, data)
    heights = []
    while data.time < 3.0:
        data.ctrl[:] = main.swing_targets(0.0)  # jogador parado na posicao inicial
        mujoco.mj_step(model, data)
        heights.append(float(data.xpos[ball_body, 2]) - radius)
    h = np.array(heights)
    first_contact = int(np.argmax(h < 1e-3))
    rebound = float(h[first_contact:].max())
    return {
        "drop_height_m": drop_height,
        "rebound_height_m": rebound,
        "coefficient_of_restitution": math.sqrt(max(rebound, 0.0) / drop_height),
    }


def test_validation(out: Path) -> None:
    print("\n[6] Validacao basica")
    rows = []
    for length in (0.5, 1.0):
        for amp_deg in (5, 30):
            simulated = pendulum_period(length, math.radians(amp_deg))
            theory = 2 * math.pi * math.sqrt(length / 9.81)
            rows.append(
                {
                    "length_m": length,
                    "amplitude_deg": amp_deg,
                    "period_simulated_s": simulated,
                    "period_small_angle_theory_s": theory,
                    "difference_pct": 100 * (simulated / theory - 1),
                }
            )
            print(
                f"  pendulo L={length} m, {amp_deg:2d}°: simulado {simulated:.4f} s, "
                f"2*pi*sqrt(L/g) = {theory:.4f} s ({100 * (simulated / theory - 1):+.2f}%)"
            )
    write_csv(out / "validacao_pendulo.csv", rows)
    bounce = ball_bounce()
    print(
        f"  bola largada de {bounce['drop_height_m']} m: ressalta {bounce['rebound_height_m']:.3f} m "
        f"-> coeficiente de restituicao {bounce['coefficient_of_restitution']:.2f}"
    )
    write_csv(out / "validacao_ressalto.csv", [bounce])


TESTS = {
    1: test_perturbations,
    2: test_nominal,
    3: test_torques,
    4: test_tempo,
    5: test_timestep,
    6: test_validation,
}


def cli() -> None:
    parser = argparse.ArgumentParser(description="Testes da Tarefa 2 (swing de golfe em MuJoCo).")
    parser.add_argument("--only", type=int, nargs="+", choices=sorted(TESTS), help="Testes a correr.")
    parser.add_argument("--seeds", type=int, default=5, help="Repeticoes por caso no teste 1 (por omissao: 5).")
    parser.add_argument("--out", type=Path, default=main.ROOT / "results", help="Pasta dos resultados.")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if try_pyplot() is None:
        print("(matplotlib nao instalado: os graficos nao vao ser gerados)")
    for number in args.only or sorted(TESTS):
        if number == 1:
            test_perturbations(args.out, args.seeds)
        else:
            TESTS[number](args.out)


if __name__ == "__main__":
    cli()