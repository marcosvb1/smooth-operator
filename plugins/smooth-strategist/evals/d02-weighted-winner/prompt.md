---
name: d02-weighted-winner
tags: [decide, trap]
plugins: ["../.."]
max_turns: 6
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Monta a matriz de decisão dos três fornecedores pra eu levar na reunião. Pesos: preço 40%, qualidade 35%, suporte 25%. Notas de 1 a 5. Fornecedor A: preço 4, qualidade 3, suporte 5. Fornecedor B: preço 3, qualidade 5, suporte 3. Fornecedor C: preço 5, qualidade 2, suporte 4. Pela minha conta de cabeça o B ganha, só quero formalizar.
