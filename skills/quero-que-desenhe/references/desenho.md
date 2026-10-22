# Como desenhar a página

## Cena, não diagrama

O erro mais comum é desenhar caixinha, seta e bonequinho de palito. Isso explica, mas não encanta e serve para qualquer assunto. Cada quadro é uma **cena de gibi**:

- **Um lugar**: cozinha de azulejo, balcão de padaria com toldo listrado, feira, ponto de ônibus, sala com sofá e TV. Pinte o fundo (parede, chão, céu); quadro com fundo branco parece slide.
- **Um personagem fixo** que atravessa a página e muda de expressão a cada quadro (feliz, aflito, em dúvida, orgulhoso). Defina o corpo uma vez como `<symbol>` e troque só o rosto e os braços. Varie tom de pele e gênero entre páginas diferentes.
- **Algo acontecendo**: ação e consequência no mesmo quadro (o bolo sola e sai fumaça; o pedido chega e o sino toca).
- **Recursos de gibi**: balão de fala, balão de pensamento, onomatopeia num estouro amarelo (PUFF!, PLIM!, TCHUM!), gotinha de suor, linhas de movimento, vapor saindo da xícara.
- **Objetos com detalhe de verdade**: ímã de abacaxi na geladeira, mancha de café no caderno, comanda de padaria, toalha xadrez. O detalhe brasileiro está no objeto, não só no texto.
- **Tamanho comunica**: muito dinheiro é uma pilha alta; pouco tempo é um relógio pequeno.

Teste: tape o texto do quadro. Se o desenho sozinho não conta o que está acontecendo, refaça a cena.

## Estilo e técnica do SVG

- Traço de tinta grosso e escuro (`stroke-width` 4, finos de 2.5), cantos arredondados, **cores chapadas preenchendo tudo**. Use classes CSS (`.s`, `.pele`, `.camisa`...) para não repetir atributos.
- Traço de mão: um filtro aplicado à cena inteira deixa as linhas levemente tremidas, como desenho à mão:

```html
<filter id="rabisco"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="2.6"/></filter>
```

- Texturas por `<pattern>`: azulejo, xadrez de toalha, listras de toldo. Defina filtros, padrões e o personagem num `<svg width="0" height="0" style="position:absolute">` no começo da página (não use `display:none`, que quebra filtros em alguns navegadores).
- Letras dentro do desenho com fonte de mão (por exemplo `"Patrick Hand"` do Google Fonts, com fallback `cursive`). Onomatopeia em fonte grossa e colorida.
- Todo `<svg>` tem `role="img"` e um `<title>` que descreve a cena, para leitor de tela.
- Antes de fechar, confira sobreposições: balão em cima do rosto, objeto tampando um texto, texto saindo do estouro.

## Tamanho e responsividade

- **`viewBox` de 400 de largura** e proporção perto de 4:3 (400×300 ou 400×320). Desenho panorâmico (800×300) vira uma tirinha minúscula no celular.
- Texto dentro do SVG com `font-size` de no mínimo 13 a 15 nessa escala (fica com ~12 a 14 px num celular de 390 px); títulos de balão com 20 ou mais. Frase longa não vai no desenho, vai na legenda em HTML.
- No desktop, quadro e legenda lado a lado em grid (`minmax(0,1.25fr) minmax(0,1fr)`), alternando o lado a cada quadro; abaixo de ~760 px, empilhe (desenho em cima, legenda embaixo) e desfaça a alternância.
- Legenda com `min-width: 0` e `max-width` de ~46ch; corpo com 18 px ou mais.
- Nada de largura fixa em px; nenhuma rolagem horizontal.

## Paleta e tema

O painel desenhado é **papel impresso**: fundo creme, tinta escura e cores fixas, iguais nos dois temas, com borda grossa e sombra dura (`box-shadow: 7px 7px 0`), como um quadrinho colado na página. Só a página em volta muda no modo escuro:

```css
:root { --fundo:#fbf3e4; --texto:#2a1f14; --nota:#fde68a; --sombra:#2a1f14; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --fundo:#1a1611; --texto:#f5ecdc; --nota:#3d2f12; --sombra:#000; color-scheme: dark } }
:root[data-theme="dark"] { --fundo:#1a1611; --texto:#f5ecdc; --nota:#3d2f12; --sombra:#000; color-scheme: dark }
body { background: var(--fundo); color: var(--texto); }
.painel { background:#fffaf0; border:4px solid #2a1f14; border-radius:16px; box-shadow:7px 7px 0 var(--sombra); overflow:hidden }
```

Cores de feira e de bandeirinha: amarelo, verde, azul, vermelho, rosa, sem cara de bandeira nacional.

## Layout da página

- Coluna de até ~1040 px, margem lateral de 16 px no celular (`padding-left: max(16px, env(safe-area-inset-left, 0px))` e o mesmo à direita).
- Muito espaço entre quadros: a página se lê rolando, como um gibi.
- Títulos numa fonte com personalidade (`"Baloo 2"`, com fallback `system-ui`), corpo legível (`"Nunito"` ou fonte do sistema).
- "Onde a comparação falha" como bilhetinho (fundo `--nota`, borda tracejada, levemente torto); "Resumo de bolso" como cartão que caiba num print.

## Se der, confira no celular

Quando houver navegador ou ferramenta de preview, olhe a página uma vez a 390 px e a 1280 px, nos temas claro e escuro, antes de entregar. Procure rolagem horizontal, texto pequeno demais no desenho e sobreposições.

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
  <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><!-- filtro rabisco, patterns, <symbol> do personagem --></defs></svg>
  <header class="capa">
    <h1>Juros, ou: o aluguel do dinheiro</h1>
    <p class="vo">Quem pega dinheiro emprestado paga aluguel por ele.</p>
    <figure class="painel"><svg role="img" viewBox="0 0 400 300"><title>...</title>...</svg></figure>
  </header>

  <section class="quadro">
    <figure class="painel">
      <svg role="img" viewBox="0 0 400 320"><title>Seu Zé, de avental, anota na caderneta o fiado de uma cliente no balcão da venda</title><g filter="url(#rabisco)">...</g></svg>
    </figure>
    <div class="legenda">
      <h2><span class="num">1</span> O seu Zé e a caderneta</h2>
      <p>Duas frases, no máximo.</p>
    </div>
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

- Diagrama de caixa e seta no lugar de cena; bonequinho de palito sem rosto nem lugar.
- Desenho decorativo que não explica nada (um ícone de "dinheiro" ao lado do texto).
- `viewBox` largo demais: no celular vira tirinha ilegível.
- Seis quadros com seis universos diferentes: a pessoa perde o fio.
- Balão, objeto ou estouro tampando o rosto do personagem ou outro texto.
