# Task 3 — Comentário aos resultados
O modelo reproduz bem a cinemática e o ritmo do swing. A transferência de energia para a bola era o grande ponto fraco e melhorou muito depois de os testes terem identificado a causa, mas o impacto continua longe de uma tacada real.

**Pontos fortes**
O simulador está validado: o período do pêndulo difere 0,05% da teoria a 5° e 1,74% a 30°, o que coincide com a correção para grandes amplitudes (1,71%). O ritmo é o resultado mais realista: a razão backswing/downswing é de 2,66:1, perto do 3:1 dos profissionais, com durações (0,87 s e 0,33 s) da ordem das reais (0,8 s e 0,27 s). Nas 180 simulações com tremor, o taco acertou sempre na bola, e o teste distingue as articulações críticas (ombros, cotovelo e pulso direitos) das irrelevantes (joelhos). Por fim, os testes serviram para corrigir o modelo: o pêndulo a bater na bola (Teste 7) mostrou que o contacto por omissão do MuJoCo dissipava quase toda a energia do choque. Com um contacto rígido na bola (*e* ≈ 0,78), o *smash factor* passou de 0,28 para 1,18 e o desvio em relação ao alvo de 12,6° para 1,6°.

**Pontos fracos**
1. O taco atinge 10,7 m/s no impacto e a bola 12,7 m/s, cerca de um quarto dos valores de um ferro 7 real. O *smash factor* (1,18) continua abaixo do real (1,34), porque a face do taco é leve (0,10 kg, mais leve do que a haste) e bate na bola de forma oblíqua. O contacto dura 6 ms em vez de 0,5 ms, porque a rigidez escolhida é muito menor do que a de uma bola real.
2. A bola sai com 26° de elevação (real: cerca de 16°), porque o arco do taco desce abaixo do nível do chão. O taco toca no chão antes da bola e chega ao impacto a travar.
3. O pulso chega a 70 N·m, cerca de cinco vezes o máximo de um adulto jovem, porque os servos de posição não têm limite de binário (`forcerange`).
4. A saída da bola é demasiado sensível. Com 20% de tremor no ombro esquerdo, a direção desvia em média 60°, e deslocar a bola 1 cm muda a sua velocidade até 40%. A face do taco tem só 1,2 cm de espessura, e a mão esquerda, solta, perturba o taco por contacto com o antebraço direito. Prender a mão esquerda à pega com uma restrição `connect` não resultou: os alvos foram desenhados para braços independentes, os braços passaram a lutar entre si e a bola saiu a 65° do alvo.
5. A bacia está fixa ao mundo e os pés não tocam no chão, por isso não há transferência de peso nem equilíbrio, e as pernas quase não afetam o taco, ao contrário da cadeia "pés → pernas → tronco → braços" da Figura 1.
6. Com um passo de 2 ms a simulação diverge, por causa dos ganhos elevados (kp = 1200 na flexão da anca). O contacto taco-chão teve de ficar mole, porque rígido fazia o taco vibrar no chão.

**Melhorias propostas**
- Dar à cabeça do taco uma massa realista (cerca de 0,27 kg) e uma face com loft definido
- Prender a mão esquerda ao taco e redesenhar os alvos do braço esquerdo para a cadeia fechada
- Limitar os binários com `forcerange` a valores humanos
- Libertar a bacia e pôr os pés em contacto com o chão
- Aumentar a rigidez do contacto da bola, com um passo de integração mais pequeno

**Conclusão**
O modelo é adequado para estudar a sequência e o ritmo do movimento e a sensibilidade relativa de cada articulação a perturbações, e a correção do contacto mostra que os testes cumprem o seu papel. Ainda não serve para prever a distância nem a direção de uma tacada real, que dependem sobretudo da velocidade e da massa da cabeça do taco.
