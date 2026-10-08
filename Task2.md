# Task 2

Todos os testes estão em `tests.py` e correm em Python, sem interface gráfica, com `python tests.py` (ou `python tests.py --only N` para um teste isolado). Cada teste grava os resultados em `results/`. Os valores apresentados foram obtidos com o modelo atual (`models/golfer.xml`), MuJoCo 3.15, integrador RK4 e passo de 1 ms. A direção do alvo é o eixo +Y do mundo (o lado do pé esquerdo do jogador) e a bola começa parada no chão, entre os pés.

## Teste 1 — Perturbações em cada grau de liberdade

**Objetivo.**
Avaliar como uma perturbação em cada uma das 12 articulações afeta o impacto e a saída da bola.

**Procedimento.**
Durante todo o swing, soma-se ao binário dos atuadores um binário de perturbação numa única articulação, através de `data.qfrc_applied`. A perturbação imita um tremor: uma sinusoide com frequência sorteada entre 8 e 12 Hz e fase aleatória. A amplitude é definida em percentagem do binário máximo que a própria articulação usa no swing nominal (5%, 10% e 20%), porque as escalas são muito diferentes entre articulações (de menos de 1 N·m nos joelhos a cerca de 70 N·m no pulso). Cada combinação articulação × amplitude é repetida com 5 sementes aleatórias, num total de 180 simulações.

**Métricas.**
Para cada simulação, compara-se com o swing nominal: se ainda há impacto, a variação do instante de impacto, da velocidade da cabeça do taco, da velocidade de saída da bola e dos ângulos de elevação e de direção da bola (medidos 10 ms depois do impacto).

**Resultado.**
O taco acertou na bola em todas as 180 simulações e a velocidade do taco no impacto variou no máximo 1,8%. A trajetória da bola, pelo contrário, mostrou-se muito sensível. Com perturbação de 20%, as articulações mais críticas foram a elevação do ombro esquerdo (desvio médio de 43° na direção e 28% na velocidade da bola) e a flexão do ombro direito (22° e 17%). O pulso direito provocou desvios de 4° a 7° já desde os 5% de perturbação. Os joelhos e a flexão da anca tiveram efeito desprezável: os joelhos porque a bacia está fixa ao mundo e as pernas não influenciam o taco, e a flexão da anca porque o seu atuador é muito rígido.

Primeiro, o braço esquerdo não está ligado ao taco, mas a mão esquerda encosta ao antebraço direito e transmite-lhe a perturbação por contacto. Segundo, nos ombros o efeito cresce de forma muito não linear entre 10% e 20% (de cerca de 6° para 43° no ombro esquerdo), o que indica que o ponto de contacto na face do taco, com apenas 1,2 cm de espessura, muda de sítio.

| Articulação | Amplitude (N·m) | Desvio na direção (°) | Variação da velocidade da bola (%) | Variação da elevação (°) |
| --- | ---: | ---: | ---: | ---: |
| left_shoulder_lift | 12,7 | 43,1 | 28,2 | 17,4 |
| right_shoulder | 14,4 | 22,1 | 17,3 | 10,5 |
| right_wrist_hinge | 13,9 | 6,7 | 7,1 | 4,0 |
| right_elbow | 12,2 | 5,9 | 2,3 | 1,3 |
| right_shoulder_lift | 16,0 | 5,6 | 4,3 | 2,5 |
| left_shoulder | 5,7 | 3,9 | 6,1 | 3,1 |
| torso_rotation | 9,3 | 1,8 | 2,7 | 2,7 |
| hip_rotation | 11,2 | 1,2 | 2,7 | 1,3 |
| left_elbow | 1,4 | 0,6 | 1,2 | 0,7 |
| right_knee | 0,8 | 0,6 | 1,2 | 0,7 |
| hip_flexion | 23,6 | 0,2 | 0,4 | 0,1 |
| left_knee | 0,7 | 0,0 | 0,1 | 0,0 |

Tabela 1 — Efeito médio de uma perturbação de 20% em cada articulação (média de 5 sementes, valores absolutos). Resultados completos em `results/perturbacoes_resumo.csv` e `results/perturbacoes_todas.csv`.



## Teste 2 — Swing nominal comparado com um swing real

**Objetivo.**
Comparar as grandezas do impacto com valores medidos em jogadores reais.

**Procedimento.**
Simula-se o swing sem perturbações durante 4 s, para a bola ter tempo de parar, e regista-se a velocidade da cabeça do taco no impacto, a velocidade e os ângulos de saída da bola 10 ms depois do impacto, o *smash factor* (velocidade da bola a dividir pela velocidade do taco) e a duração do contacto entre o taco e a bola.

**Referência.**
Como o taco do modelo bate na bola pousada no chão, a comparação mais próxima é um ferro 7. Segundo os dados Trackman do PGA Tour, um ferro 7 é batido a cerca de 92 mph (41 m/s), a bola sai a cerca de 123 mph (55 m/s) [1], o *smash factor* é de cerca de 1,34 [2] e o ângulo de lançamento é de cerca de 16° [3]. O contacto entre o taco e a bola dura cerca de 0,5 ms [4].

**Resultado.**
O modelo fica muito aquém (Tabela 2). A cabeça do taco atinge cerca de 28% da velocidade real e a bola apenas 6%, ou seja, a transferência de energia é muito ineficiente (*smash factor* de 0,28 contra 1,34). O contacto dura 8 ms, 16 vezes mais do que na realidade, o que mostra que o taco empurra a bola em vez de lhe bater. A bola sai demasiado alta e 12,6° desviada do alvo. As causas mais prováveis são o contacto do MuJoCo, que por omissão é mole e não devolve energia (ver Testes 6 e 7), a geometria da cabeça do taco (uma caixa fina, mais leve do que a haste) e o ângulo de ataque muito inclinado, porque o arco do taco desce abaixo do nível do chão.

| Grandeza | Modelo | Referência real (ferro 7) |
| --- | ---: | ---: |
| Velocidade da cabeça do taco no impacto | 11,4 m/s | ≈ 41 m/s |
| Velocidade de saída da bola | 3,2 m/s | ≈ 55 m/s |
| *Smash factor* | 0,28 | ≈ 1,34 |
| Ângulo de elevação da bola | 29,1° | ≈ 16° |
| Desvio em relação ao alvo | 12,6° | ≈ 0° (bola direita) |
| Duração do contacto | 8 ms | ≈ 0,5 ms |

Tabela 2 — Swing nominal comparado com valores reais. Resultados em `results/nominal.csv`.



## Teste 3 — Binários usados comparados com a capacidade humana

**Objetivo.**
Verificar se os atuadores pedem às articulações binários que um humano consegue produzir.

**Procedimento.**
No swing nominal, regista-se em cada passo o binário de cada atuador (`data.actuator_force`) e guarda-se o máximo em valor absoluto.

**Referência.**
Num estudo com 345 adultos saudáveis, o binário isométrico máximo do pulso em homens entre 20 e 29 anos foi de cerca de 14 N·m em flexão e 11 N·m em extensão [5].

**Resultado.**
Os maiores binários foram os da flexão da anca (118 N·m), da elevação do ombro direito (80 N·m), da flexão do ombro direito (72 N·m), do pulso direito (69 N·m) e do cotovelo direito (61 N·m). O caso mais claro é o do pulso: 69 N·m é cerca de cinco vezes o máximo de um adulto jovem. Isto acontece porque os atuadores de posição não têm limite de binário (`forcerange`) e fazem o binário que for preciso para seguir os alvos, o que torna o movimento fisicamente possível no simulador mas não num corpo humano.



## Teste 4 — Ritmo do swing

**Objetivo.**
Comparar a proporção entre a duração do backswing e a do downswing com a de jogadores profissionais.

**Procedimento.**
A partir da velocidade da cabeça do taco em cada passo, define-se o início do swing como o primeiro instante em que a velocidade passa 0,2 m/s, o topo do backswing como o instante de velocidade mínima antes da descida e o impacto como o primeiro contacto entre o taco e a bola.

**Referência.**
A análise de vídeo de jogadores profissionais mostra que o backswing dura cerca de três vezes mais do que o downswing até ao impacto, uma razão de 3:1 [6]; por exemplo, cerca de 0,8 s de backswing e 0,27 s de downswing.

**Resultado.**
O swing começa aos 0,139 s, o topo é aos 1,006 s e o impacto aos 1,332 s, o que dá 0,867 s de backswing, 0,326 s de downswing e uma razão de 2,66:1. É o resultado mais próximo da realidade, tanto na proporção como nas durações absolutas. Note-se que o topo real acontece 0,15 s depois do topo dos alvos (0,86 s), o que mede o atraso dos atuadores em relação ao movimento pedido.



## Teste 5 — Sensibilidade ao passo de integração

**Objetivo.**
Verificar se os resultados dependem do passo de integração escolhido.

**Procedimento.**
Repete-se o swing nominal com passos de 0,5 ms, 1 ms e 2 ms, mantendo o integrador RK4.

**Resultado.**
Entre 0,5 ms e 1 ms, o instante de impacto é o mesmo (1,332 s), a velocidade do taco varia 0,6%, a velocidade da bola 2% e os ângulos de saída cerca de 1,5°. O passo de 1 ms é, portanto, adequado, embora as grandezas que dependem do contacto sejam mais sensíveis do que as do movimento do corpo. Com 2 ms a simulação diverge logo nos primeiros passos.

| Passo | Impacto | Velocidade do taco | Velocidade da bola | Elevação | Direção |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,5 ms | 1,332 s | 11,29 m/s | 3,12 m/s | 30,6° | 14,2° |
| 1 ms | 1,332 s | 11,36 m/s | 3,19 m/s | 29,1° | 12,6° |
| 2 ms | instável | — | — | — | — |

Tabela 3 — Resultados do swing nominal com diferentes passos de integração. Resultados em `results/passo_integracao.csv`.



## Teste 6 — Validação básica

**Objetivo.**
Confirmar, com casos de solução conhecida, que as opções de simulação usadas no modelo (gravidade, integrador e passo) produzem resultados físicos corretos, como sugere a primeira dica do enunciado.

**Procedimento.**
Simula-se um pêndulo simples com uma massa pontual de 1 kg, com comprimentos de 0,5 m e 1 m e amplitudes de 5° e 30°, e mede-se o período pelas passagens por zero. Depois, larga-se a bola do modelo de 1 m de altura sobre o chão do modelo e mede-se a altura do ressalto.

**Resultado.**
Com 5°, o período simulado difere apenas 0,05% de 2π√(L/g). Com 30°, a diferença é de 1,74%, o que coincide com a correção teórica para grandes amplitudes, T ≈ T₀(1 + θ₀²/16) e que prevê cerca de 1,71%. A bola, pelo contrário, não ressalta (coeficiente de restituição 0). Isto acontece porque os contactos do MuJoCo são, por omissão, criticamente amortecidos (`solref="0.02 1"`) e dissipam toda a energia do choque [7].



## Teste 7 — Pêndulo a bater na bola

**Objetivo.**
Isolar o choque entre o taco e a bola num caso de solução conhecida, como pede a primeira dica do enunciado, e verificar se o modelo de contacto explica a fraca transferência de energia do Teste 2.

**Procedimento.**
Um pêndulo de 1 m, cuja massa é uma esfera de 0,10 kg (a massa da face do taco do modelo), é largado de 30° e de 90° e bate de frente na bola do modelo, pousada no chão. Mede-se a velocidade do pêndulo antes do choque, as velocidades do pêndulo e da bola depois do choque, o coeficiente de restituição *e* (velocidade de afastamento a dividir pela velocidade de aproximação) e a duração do contacto. Repete-se o ensaio com três parâmetros de contacto: o do modelo, que é o do MuJoCo por omissão (`solref="0.02 1"`), e dois contactos rígidos definidos diretamente pela rigidez e pelo amortecimento (`solref` negativo). Num choque perfeitamente elástico, a razão entre a velocidade da bola e a do pêndulo seria 2M/(M+m) = 1,38. Numa bola de golfe real contra a face de um taco, *e* é da ordem de 0,8; as regras limitam-no a 0,830 [8].

**Resultado.**
A velocidade do pêndulo antes do choque coincide com √(2gL(1−cos θ₀)) até ao centésimo de m/s. Com o contacto por omissão, *e* fica entre 0,16 e 0,21, o contacto dura cerca de 68 ms e a bola sai mais devagar do que o pêndulo chega (razão de 0,76 a 0,78). Este é o mesmo comportamento do swing (*smash factor* de 0,28, Teste 2). Com um contacto rígido e pouco amortecido (`solref="-200000 -5"`), *e* sobe para 0,98, a razão para 1,36 (a teoria elástica dá 1,38), a quantidade de movimento conserva-se a 0,3% e o contacto dura 7 ms. Aumentando o amortecimento (`solref="-200000 -70"`), obtém-se *e* ≈ 0,78, próximo do de uma bola real. Os resultados quase não dependem da velocidade de impacto. Confirma-se que a principal causa da fraca transferência de energia no swing é o contacto por omissão, e que este pode ser corrigido sem alterar o resto do modelo. A duração do contacto só é medida com a resolução do passo (1 ms).

| Contacto (`solref`) | Amplitude | *e* | Razão v_bola / v_pêndulo | Duração do contacto |
| --- | ---: | ---: | ---: | ---: |
| Omissão (`0.02 1`) | 30° | 0,21 | 0,78 | 67 ms |
| Omissão (`0.02 1`) | 90° | 0,16 | 0,76 | 69 ms |
| Rígido elástico (`-200000 -5`) | 30° | 0,98 | 1,36 | 7 ms |
| Rígido elástico (`-200000 -5`) | 90° | 0,98 | 1,36 | 7 ms |
| Rígido, *e* ≈ 0,78 (`-200000 -70`) | 30° | 0,78 | 1,22 | 7 ms |
| Rígido, *e* ≈ 0,78 (`-200000 -70`) | 90° | 0,79 | 1,23 | 7 ms |

Tabela 4 — Choque entre o pêndulo (0,10 kg) e a bola (0,045 kg). Resultados em `results/validacao_pendulo_bola.csv`.



## Referências
1. Golf Monthly, "How Far PGA Tour Players Hit Every Club In The Bag" (dados Trackman, 2024). https://golfmonthly.com/tour/how-far-pga-tour-players-hit-every-club-in-the-bag
2. Golf Digest, "The most deceiving data point when comparing irons — Smash Factor". https://www.golfdigest.com/story/the-most-deceiving-data-point-when-comparing-irons-smash-factor
3. Golf Digest, "Hot List 2025: highest launching irons for average players". https://www.golfdigest.com/story/hot-list-2025--highest-launching-irons-for-average-players
4. Patente US 9541483, "Contact state observation apparatus of golf ball and contact state observation method of golf ball".
5. V. Decostre et al., "Wrist flexion and extension torques measured by highly sensitive dynamometer in healthy subjects from 5 to 80 years", *BMC Musculoskeletal Disorders* 16:4, 2015. doi:10.1186/s12891-015-0458-9
6. J. Novosel, *Tour Tempo: Golf's Last Secret Finally Revealed*, 2004; resumo em "It's About Time", *Sports Illustrated*, 2010. https://vault.si.com/vault/2010/08/02/its-about-time
7. Documentação do MuJoCo, "Modeling" (parâmetros de contacto `solref` e `solimp`). https://mujoco.readthedocs.io/en/latest/modeling.html
8. USGA/R&A, *Equipment Rules*, Part 2, secção 4.1d (efeito mola e coeficiente de restituição da cabeça do taco, limite de 0,830). https://www.usga.org/equipment-standards/equipment-rules-2019.html
