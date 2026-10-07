Teste 1 — Perturbações em cada grau de liberdade

Objetivo
    Avaliar como uma perturbação em cada uma das 12 articulações afeta o impacto e a saída da bola. 

Procedimento
    Durante todo o swing, soma-se ao binário dos atuadores um binário de perturbação numa única articulação, através de data.qfrc_applied. A perturbação imita um tremor: uma sinusoide com frequência sorteada entre 8 e 12 Hz e fase aleatória. A amplitude é definida em percentagem do binário máximo que a própria articulação usa no swing nominal (5%, 10% e 20%), porque as escalas são muito diferentes entre articulações (de menos de 1 N·m nos joelhos a cerca de 70 N·m no pulso). Cada combinação articulação × amplitude é repetida com 5 sementes aleatórias, num total de 180 simulações. 

Métricas
 Para cada simulação, compara-se com o swing nominal: se ainda há impacto, a variação do instante de impacto, da velocidade da cabeça do taco, da velocidade de saída da bola e dos ângulos de elevação e de direção da bola (medidos 10 ms depois do impacto). 

Resultado
    O taco acertou na bola em todas as 180 simulações, e a velocidade do taco no impacto variou no máximo 1,8%. A trajetória da bola, pelo contrário, mostrou-se muito sensível. Com perturbação de 20%, as articulações mais críticas foram a elevação do ombro esquerdo (desvio médio de 43° na direção e 28% na velocidade da bola) e a flexão do ombro direito (22° e 17%). O pulso direito provocou desvios de 4° a 7° já desde os 5% de perturbação. Os joelhos e a flexão da anca tiveram efeito desprezável: os joelhos porque a bacia está fixa ao mundo e as pernas não influenciam o taco, e a flexão da anca porque o seu atuador é muito rígido. Dois resultados merecem nota. Primeiro, o braço esquerdo não está ligado ao taco, mas a mão esquerda encosta ao antebraço direito e transmite-lhe a perturbação por contacto. Segundo, nos ombros o efeito cresce de forma muito não linear entre 10% e 20% (de cerca de 6° para 43° no ombro esquerdo), o que indica que o ponto de contacto na face do taco, com apenas 1,2 cm de espessura, muda de sítio.



Teste 2 — Swing nominal comparado com um swing real

Objetivo
    Comparar as grandezas do impacto com valores medidos em jogadores reais.

Procedimento
    Simula-se o swing sem perturbações durante 4 s, para a bola ter tempo de parar, e regista-se a velocidade da cabeça do taco no impacto, a velocidade e os ângulos de saída da bola 10 ms depois do impacto, o smash factor (velocidade da bola a dividir pela velocidade do taco) e a duração do contacto entre o taco e a bola.
    
Referência
    Como o taco do modelo bate na bola pousada no chão, a comparação mais próxima é um ferro 7. Segundo os dados Trackman do PGA Tour, um ferro 7 é batido a cerca de 92 mph (41 m/s), a bola sai a cerca de 123 mph (55 m/s), o smash factor é de cerca de 1,34 e o ângulo de lançamento é de cerca de 16°. O contacto entre o taco e a bola dura cerca de 0,5 ms.

Resultado
    O modelo fica muito aquém (Tabela 2). A cabeça do taco atinge cerca de 28% da velocidade real e a bola apenas 6%, ou seja, a transferência de energia é muito ineficiente (smash factor de 0,28 contra 1,34). O contacto dura 8 ms, 16 vezes mais do que na realidade, o que mostra que o taco empurra a bola em vez de lhe bater. A bola sai demasiado alta e 12,6° desviada do alvo. As causas mais prováveis são o contacto do MuJoCo, que por omissão é mole e não devolve energia (ver Teste 6), a geometria da cabeça do taco (uma caixa fina, mais leve do que a haste) e o ângulo de ataque muito inclinado, porque o arco do taco desce abaixo do nível do chão.


Teste 3 — Binários usados comparados com a capacidade humana

Objetivo
    Verificar se os atuadores pedem às articulações binários que um humano consegue produzir.

Procedimento
    No swing nominal, regista-se em cada passo o binário de cada atuador (data.actuator_force) e guarda-se o máximo em valor absoluto. 

Referência
    Num estudo com 345 adultos saudáveis, o binário isométrico máximo do pulso em homens entre 20 e 29 anos foi de cerca de 14 N·m em flexão e 11 N·m em extensão

Resultado
    Os maiores binários foram os da flexão da anca (118 N·m), da elevação do ombro direito (80 N·m), da flexão do ombro direito (72 N·m), do pulso direito (69 N·m) e do cotovelo direito (61 N·m). O caso mais claro é o do pulso: 69 N·m é cerca de cinco vezes o máximo de um adulto jovem. Isto acontece porque os atuadores de posição não têm limite de binário (forcerange) e fazem o binário que for preciso para seguir os alvos, o que torna o movimento fisicamente possível no simulador mas não num corpo humano.



