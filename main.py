from pathlib import Path
import time
import math

# mujoco contém o motor de simulação.
# mujoco.viewer permite ver a simulação numa janela.
import mujoco
import mujoco.viewer


# O XML fica numa pasta separada para ser fácil de editar e reutilizar.
MODEL_PATH = Path(__file__).parent / "models" / "pendulum.xml"
TORSO_ANGLE = math.radians(45.0)
INITIAL_ANGLE = 1.0
SWING_DURATION = 3.0


def main() -> None:
	"""Carrega o modelo e executa a simulação do pêndulo."""
	# MjModel contém a descrição fixa do sistema: corpos, juntas e parâmetros.
	model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
	# MjData contém o estado que muda durante a simulação.
	data = mujoco.MjData(model)

	# qpos[0] é a rotação do tronco e qpos[1] é o ombro direito.
	# O tronco começa rodado 45 graus, como na postura de preparação.
	data.qpos[0] = TORSO_ANGLE
	data.qpos[1] = INITIAL_ANGLE
	# Atualiza posições e velocidades derivadas depois de alterar qpos manualmente.
	mujoco.mj_forward(model, data)

	# O visualizador corre enquanto a janela estiver aberta.
	with mujoco.viewer.launch_passive(model, data) as viewer:
		while viewer.is_running():
			# Mede o tempo gasto neste ciclo para manter uma velocidade realista.
			step_start = time.perf_counter()

			# Avança a física exatamente um timestep definido no XML.
			mujoco.mj_step(model, data)

			# Reinicia o swing e a bola depois de SWING_DURATION segundos.
			# mj_resetData repõe as posições, velocidades e o tempo da simulação.
			if data.time >= SWING_DURATION:
				mujoco.mj_resetData(model, data)
				data.qpos[0] = TORSO_ANGLE
				data.qpos[1] = INITIAL_ANGLE
				mujoco.mj_forward(model, data)

			# Envia o estado atualizado para a janela.
			viewer.sync()

			# Espera o tempo restante, se o computador tiver calculado o passo depressa.
			elapsed = time.perf_counter() - step_start
			remaining = model.opt.timestep - elapsed
			if remaining > 0:
				time.sleep(remaining)


if __name__ == "__main__":
	main()
