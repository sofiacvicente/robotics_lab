# Simulacao de swing de golfe

Simulacao simplificada de um swing em MuJoCo. O modelo inclui a bacia, o
tronco, os bracos, as pernas articuladas, um taco e uma bola. A animacao abre
uma janela; o modo de teste corre sem interface grafica e verifica o impacto.

## Requisitos e execucao no WSL

O ambiente Python pode ficar fora da pasta do projeto, para nao ser enviado
juntamente com o codigo:

```bash
cd /mnt/c/Users/berna/Desktop/robotica
python3 -m venv ~/.venvs/robotica
source ~/.venvs/robotica/bin/activate
python -m pip install -r requirements.txt
```

Para abrir a simulacao:

```bash
python main.py
```

Este modo precisa de uma sessao grafica disponivel no WSL, por exemplo WSLg.
Para testar sem abrir uma janela:

```bash
python main.py --test --output /tmp/golf-results.csv
```

O teste imprime se houve impacto, o instante e a velocidade da cabeca do taco,
e guarda as medicoes no CSV indicado. O resultado usa `/tmp` para nao criar
ficheiros de teste dentro do projeto.

## Graus de liberdade

O modelo tem doze articulacoes controladas, todas do tipo rotacional:

| Articulacao | Eixo | Funcao aproximada |
| --- | --- | --- |
| Rotacao da bacia (`hip_rotation`) | Z | Rotacao axial da bacia durante o swing |
| Flexao da anca (`hip_flexion`) | Y | Inclinacao do tronco relativamente a bacia |
| Rotacao do tronco (`torso_rotation`) | Z | Rotacao do tronco relativamente a bacia |
| Elevacao/abducao do ombro direito (`right_shoulder_lift`) | X | Abre e eleva lateralmente o braco que segura o taco |
| Ombro direito (`right_shoulder`) | Y | Movimento do braco que segura o taco |
| Cotovelo direito (`right_elbow`) | Y | Flexao/extensao do braco que segura o taco |
| Articulacao do pulso direito (`right_wrist_hinge`) | Y | Inclina o taco relativamente a mao para criar atraso no backswing e liberta-o na descida |
| Elevacao/abducao do ombro esquerdo (`left_shoulder_lift`) | X | Abre e eleva lateralmente o braco de apoio |
| Ombro esquerdo (`left_shoulder`) | Y | Movimento do braco de apoio |
| Cotovelo esquerdo (`left_elbow`) | Y | Flexao/extensao do braco de apoio |
| Joelho esquerdo (`left_knee`) | Y | Flexao/extensao do joelho esquerdo |
| Joelho direito (`right_knee`) | Y | Flexao/extensao do joelho direito |

Os alvos percorrem a preparacao, o takeaway, o backswing, a descida, o impacto
e a finalizacao. No backswing, a bacia roda moderadamente para tras; na descida,
comeca a abrir para o alvo antes do tronco. O cotovelo direito dobra mais no
topo, enquanto o esquerdo se mantem relativamente estendido. O pulso roda para
elevar o taco e liberta-o na descida. A bola esta posicionada para o contacto
ocorrer durante o avanco ascendente da cabeca do taco, e nao no seu regresso.
Os alvos dos ombros procuram manter as maos proximas sem as ligar
mecanicamente. A flexao da anca aumenta na aproximacao ao impacto. O joelho da
frente flete mais na subida e estende na descida; o joelho de tras mantem a
flexao na subida e flete mais na finalizacao.

## Simplificacoes assumidas

- O corpo e composto por formas geometricas simples; nao representa com
  precisao a anatomia nem as proporcoes individuais de um jogador.
- A bacia esta presa ao mundo por uma articulacao de rotacao. Nao ha
  translacao do corpo, deslocamento lateral nem articulacoes independentes
  para as duas ancas.
- A flexao da anca e representada por uma unica articulacao entre a bacia e o
  tronco. A coluna, o pescoco e a cabeca nao se articulam separadamente.
- Cada perna tem uma articulacao no joelho. Os pes sao rigidos, nao colidem
  com o chao e nao existem articulacoes nos tornozelos. O corpo esta ancorado
  pela bacia, pelo que os pes sem colisao nao controlam o equilibrio.
- Cada braco tem duas articulacoes no ombro (elevacao/abducao e
  flexao/extensao) e uma no cotovelo. O pulso direito tem uma articulacao
  rotacional simplificada; o pulso esquerdo e os dedos nao sao articulados.
- As duas maos sao geometrias independentes, sem restricao mecanica que as
  mantenha juntas; as poses dos bracos apenas procuram aproxima-las.
- O taco e liso e ligado a mao direita por uma articulacao rotacional simples
  no pulso. A haste e representada por uma unica geometria continua, sem uma
  pega separada nem flexibilidade do taco.
- A haste nao participa nas colisoes. A cabeca do taco e uma caixa com uma
  inclinacao fixa simplificada para dar componente ascendente ao impacto; pode
  colidir com o chao e com a bola, que e modelada como uma esfera. O voo da
  bola nao esta calibrado para reproduzir uma tacada real.
- Os atuadores seguem posicoes-alvo; nao se modelam musculos, forcas humanas,
  equilibrio ou transferencia de peso com detalhe biomecanico.

Estas escolhas permitem testar uma sequencia visual e o contacto taco-bola,
mas nao pretendem prever o desempenho de um jogador real.
