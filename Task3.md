# Task 3 — Comentário aos resultados
O modelo reproduz bem a **cinemática e o ritmo** do swing. A **transferência de energia para a bola** era o grande ponto fraco e melhorou muito depois de os testes terem identificado a causa, mas o impacto continua longe de uma tacada real.

**Pontos fortes.**
O simulador está validado: o período do pêndulo difere 0,05% da teoria a 5°, e a 30° difere 1,74%, que é o que a correção para grandes amplitudes prevê (1,71%). O ritmo é o resultado mais realista: a razão backswing:downswing é de 2,66:1, perto do 3:1 dos profissionais, e as durações (0,87 s e 0,33 s) são da ordem das reais (0,8 s e 0,27 s). O swing é robusto ao nível do impacto: nas 180 simulações com tremor, o taco acertou sempre na bola e a sua velocidade variou no máximo 2,5%. O teste de perturbações identifica as articulações críticas (ombros, cotovelo e pulso direitos) e as irrelevantes (joelhos), uma hierarquia que faz sentido num jogador real. Por fim, os testes serviram para corrigir o modelo: o pêndulo a bater na bola (Teste 7) mostrou que o contacto por omissão do MuJoCo devolvia só cerca de 20% da velocidade de aproximação. Com um contacto rígido na bola (*e* ≈ 0,78), o *smash factor* passou de 0,28 para 1,01, a bola passou a ressaltar e o desvio em relação ao alvo desceu de 12,6° para 3,9°.

**Pontos fracos.**
1. *Impacto ainda pouco realista.* A cabeça do taco atinge 11,4 m/s (28% de um ferro 7 real) e a bola sai a 11,5 m/s (21%). O *smash factor* (1,01) continua abaixo do real (1,34): a face do taco pesa só 0,10 kg (uma real tem cerca de 0,27 kg), é mais leve do que a haste e bate na bola de forma oblíqua. O contacto dura 6 ms em vez de cerca de 0,5 ms, porque a rigidez escolhida é muito menor do que a de uma bola real.
2. *Bola demasiado alta.* A bola sai com 29° de elevação (real: cerca de 16°), porque o arco do taco desce abaixo do nível do chão e o ângulo de ataque é muito inclinado.
3. *Binários sobre-humanos.* O pulso chega a 69 N·m, cerca de cinco vezes o máximo de um adulto jovem. Os servos de posição não têm `forcerange` e fazem o binário que for preciso.
4. *Sensibilidade excessiva da bola.* Com 20% de tremor no ombro esquerdo, a direção desvia em média 61°. Parte deste efeito é artificial: a mão esquerda não está presa ao taco e perturba-o por contacto com o antebraço direito. A face do taco tem só 1,2 cm de espessura, e um ponto de contacto ligeiramente diferente muda muito a saída da bola.
5. *Simplificações do corpo.* A bacia está fixa ao mundo e os pés não tocam no chão, por isso não há transferência de peso nem equilíbrio. As pernas quase não afetam o taco, o que contraria a cadeia "pés → pernas → tronco → braços" da Figura 1 do enunciado.
6. *Limites numéricos.* Com um passo de 2 ms a simulação diverge, por causa dos ganhos elevados (kp = 1200 na flexão da anca). O contacto taco-chão teve de ficar mole: rígido, fazia a face do taco vibrar no chão no início do swing.

**Melhorias propostas.**
- Dar à cabeça do taco uma massa realista (cerca de 0,27 kg) e uma face com loft definido.
- Prender a mão esquerda ao taco com uma restrição `weld`.
- Limitar os binários com `forcerange` a valores humanos.
- Libertar a bacia e pôr os pés em contacto com o chão.
- Aumentar a rigidez do contacto da bola, com um passo de integração mais pequeno.

**Conclusão.**
O modelo é adequado para estudar a **sequência e o ritmo do movimento** e a **sensibilidade relativa de cada articulação** a perturbações. A correção do contacto mostra que os testes cumprem o seu papel. O modelo ainda não serve para prever a distância nem a direção de uma tacada real, que dependem sobretudo da velocidade e da massa da cabeça do taco.
