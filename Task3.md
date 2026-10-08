# Task 3 — Comentário aos resultados
O modelo reproduz bem a **cinemática e o ritmo** do swing, mas falha na **transferência de energia para a bola**. As causas principais estão identificadas, e quase todas são escolhas de modelação que se podem corrigir.

**Pontos fortes.**
O simulador está validado: o período do pêndulo difere 0,05% da teoria a 5°, e a 30° difere 1,74%, que é o que a correção para grandes amplitudes prevê (1,71%). O passo de 1 ms é adequado, porque com 0,5 ms o instante de impacto é o mesmo e a velocidade do taco muda 0,6%. O ritmo é o resultado mais realista: a razão backswing:downswing é de 2,66:1, perto do 3:1 dos profissionais, e as durações (0,87 s e 0,33 s) são da ordem das reais (0,8 s e 0,27 s). O swing é robusto ao nível do impacto: nas 180 simulações com tremor, o taco acertou sempre na bola e a sua velocidade variou no máximo 1,8%. O teste de perturbações também identifica as articulações críticas (ombros e pulso) e as irrelevantes (joelhos e flexão da anca), uma hierarquia que faz sentido num jogador real.

**Pontos fracos.**
1. *Impacto pouco realista.* A cabeça do taco atinge 11,4 m/s (28% de um ferro 7 real) e a bola sai a 3,2 m/s (6%). O *smash factor* é de 0,28, contra 1,34. O contacto dura 8 ms em vez de cerca de 0,5 ms e a bola não ressalta no chão. A causa é o contacto do MuJoCo por omissão (`solref="0.02 1"`), que é mole e criticamente amortecido: dissipa a energia em vez de a devolver. A cabeça do taco também pesa só 0,10 kg (uma real tem cerca de 0,27 kg) e é mais leve do que a haste.
2. *Bola desviada.* A bola sai com 29° de elevação (real: cerca de 16°) e 12,6° fora do alvo. Isto resulta da face fixa e simplificada e do arco do taco, que desce abaixo do nível do chão.
3. *Binários sobre-humanos.* O pulso chega a 69 N·m, cerca de cinco vezes o máximo de um adulto jovem. Os servos de posição não têm `forcerange` e fazem o binário que for preciso: o movimento é possível no simulador, mas não num corpo humano.
4. *Sensibilidade excessiva da direção da bola.* Com 20% de tremor no ombro esquerdo, a direção desvia em média 43°. Parte deste efeito é artificial: a mão esquerda não está presa ao taco e perturba-o por contacto com o antebraço direito. Além disso, a face do taco tem só 1,2 cm de espessura, e um ponto de contacto ligeiramente diferente muda muito a saída da bola.
5. *Simplificações do corpo.* A bacia está fixa ao mundo e os pés não tocam no chão, por isso não há transferência de peso nem equilíbrio. As pernas acabam por não ter qualquer efeito no taco, o que contraria a cadeia "pés → pernas → tronco → braços" da Figura 1 do enunciado.
6. *Estabilidade numérica.* Com um passo de 2 ms a simulação diverge, por causa dos ganhos elevados (kp = 1200 na flexão da anca).

**Melhorias propostas.**
- Usar um contacto rígido entre o taco e a bola. O Teste 7 (pêndulo a bater na bola) já o confirma: com o contacto por omissão, *e* ≈ 0,2; com `solref="-200000 -70"`, *e* ≈ 0,78, perto de uma bola real.
- Dar à cabeça do taco uma massa realista (cerca de 0,27 kg) e uma face com loft definido.
- Prender a mão esquerda ao taco com uma restrição `weld`.
- Limitar os binários com `forcerange` a valores humanos.
- Libertar a bacia e pôr os pés em contacto com o chão.

**Conclusão.**
O modelo é adequado para estudar a **sequência e o ritmo do movimento** e a **sensibilidade relativa de cada articulação** a perturbações. Ainda não serve para prever a distância nem a direção da bola, porque estas grandezas dependem sobretudo do modelo de contacto e da massa da cabeça do taco, que são as primeiras coisas a corrigir.
