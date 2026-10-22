# Como desenhar a página

## Estilo dos desenhos

- **SVG inline**, à mão, simples: bonequinhos de palito, caixas, setas, ícones grossos. Cara de quadro-negro de professor bom, não de infográfico corporativo.
- Traço grosso (`stroke-width` 3 a 5), cantos arredondados (`stroke-linecap="round"`, `stroke-linejoin="round"`), poucas cores.
- Um desenho por quadro, com `viewBox` e `width="100%"` para escalar. Altura visual entre 220 e 420 px no desktop.
- Etiquetas curtas dentro do desenho (`<text>`). Com `viewBox` de 800 de largura, use `font-size` de no mínimo 32 a 36 (vira cerca de 16 px num celular de 360 px). As palavras do desenho contam no limite de "pouco texto".
- Mostre movimento com setas e numeração (①②③), e antes/depois lado a lado.
- Personagem recorrente ajuda: um mesmo bonequinho (com um boné, um chinelo, uma sacola de feira) atravessando os quadros dá continuidade à história.
- Emoji pode complementar, mas não substitui o desenho.
- Todo `<svg>` tem `role="img"` e um `<title>` descrevendo a cena, para leitor de tela.

## Paleta

Cores de feira e de bandeirinha de São João, sem cara de bandeira nacional. Defina como variáveis no `:root` e redefina para modo escuro:

```css
:root {
  --fundo: #fffaf0;   /* papel */
  --tinta: #1f2937;   /* traço e texto */
  --verde: #16a34a;
  --amarelo: #f59e0b;
  --azul: #2563eb;
  --rosa: #e11d48;
  --suave: #fde68a;   /* destaque de fundo */
}
@media (prefers-color-scheme: dark) {
  :root {
    --fundo: #111827;
    --tinta: #f3f4f6;
    --suave: #78350f;
  }
}
body { background: var(--fundo); color: var(--tinta); }
```

Nos SVGs use `stroke="currentColor"`, `fill="currentColor"` em todo `<text>` (o padrão é preto e some no modo escuro) e cores por `style="fill: var(--verde)"`, que funciona melhor com variáveis CSS do que o atributo `fill=` puro.

## Layout

- Coluna única, `max-width` de ~880 px, centralizada, margem lateral de 16 px no celular. Sem rolagem horizontal.
- Quadro = desenho em cima (ou à esquerda em telas largas) + número, título e até duas frases.
- Muito espaço em branco entre quadros. A página deve ser rolada como um gibi, um quadro por "tela".
- Fonte com personalidade e legível: por exemplo `"Baloo 2"` ou `"Nunito"` do Google Fonts nos títulos, sempre com fallback (`font-family: "Baloo 2", system-ui, sans-serif`), e fonte do sistema no corpo. Corpo com 18 px ou mais.
- O quadro "Onde a comparação falha" pode ter um visual de bilhetinho (fundo `--suave`, borda tracejada).
- O "Resumo de bolso" fica num cartão que caiba num print de celular.

## Esqueleto

```html
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Juros, desenhado</title>
  <style>/* paleta + layout acima */</style>
</head>
<body>
  <header class="capa">
    <h1>Juros, ou: o aluguel do dinheiro</h1>
    <p class="vo">Quem pega dinheiro emprestado paga aluguel por ele.</p>
    <svg role="img" viewBox="0 0 800 400" width="100%"><title>...</title>...</svg>
  </header>

  <section class="quadro">
    <svg role="img" viewBox="0 0 800 360" width="100%"><title>...</title>...</svg>
    <h2><span class="num">1</span> O seu Zé e a caderneta</h2>
    <p>Duas frases, no máximo.</p>
  </section>
  <!-- mais quadros -->

  <aside class="falha">
    <h2>Onde a comparação falha</h2>
    <ul><li>...</li></ul>
  </aside>

  <section class="bolso">
    <h2>Resumo de bolso</h2>
    <ul><li>...</li><li>...</li><li>...</li></ul>
  </section>
</body>
</html>
```

## Erros comuns

- Desenho decorativo que não explica nada (um ícone de "dinheiro" ao lado do texto). O desenho tem que mostrar o mecanismo.
- Texto dentro do SVG pequeno demais no celular.
- Seis quadros com seis universos diferentes: a pessoa perde o fio.
- Cor clara em fundo claro no modo escuro (esqueceu de usar as variáveis).
