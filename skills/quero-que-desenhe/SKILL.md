---
name: quero-que-desenhe
description: "Explica um assunto do zero numa página HTML com desenhos grandes em SVG, pouco texto e comparações do dia a dia brasileiro; em ambiente só texto, desenha em ASCII. Use quando a pessoa pedir uma explicação desenhada ou para leigo, sobre qualquer tema (tecnologia, finanças, ciência, um documento técnico): \"quero que desenhe\", \"desenha pra mim\", \"explica desenhando\", \"me explica como se eu tivesse 5 anos\", \"explica pra leigo\", \"ELI5\", \"faz uma página desenhada explicando X\". Não use para respostas curtas, análise aprofundada, dúvidas de código no meio de uma tarefa, nem quando a pessoa diz \"quer que eu desenhe?\" reclamando que não foi entendida."
---

# Quero que desenhe

"Quer que eu desenhe?" é o que a gente fala quando a explicação não entrou. Esta skill leva a frase ao pé da letra: trata a pessoa como alguém que não sabe nada do assunto e entrega uma página HTML com **desenhos grandes e pouco texto**, usando comparações que qualquer brasileiro reconhece na hora: fila do banco, Pix, feira, pelada de domingo, grupo da família no WhatsApp, ônibus lotado, padaria às 7 da manhã.

A ideia vem da skill `eli5` ("explain like I'm 5"), um prompt de uma linha: *"Explain like I'm someone who knows nothing about this topic, using a HTML artifact with big pictures and few words."* Aqui ela ganha sotaque, método e repertório.

## Princípios

1. **O desenho explica, o texto legenda.** Cada quadro tem um desenho que sozinho já conta a ideia; o texto do lado tem no máximo duas frases curtas. Se precisou de um parágrafo, o desenho está errado.
2. **Uma comparação brasileira por ideia, e ela tem que ser fiel.** A comparação serve ao conceito, não o contrário. Antes de usar, confira se o mecanismo é o mesmo (quem faz o quê, em que ordem, o que acontece quando dá errado). Comparação engraçada e errada é pior que nenhuma.
3. **Diga onde a comparação quebra.** Toda analogia mente em algum ponto. Um quadro final "Onde a comparação falha" evita que a pessoa saia com uma ideia torta.
4. **Zero jargão sem tradução.** Termo técnico só aparece depois que o desenho já mostrou a coisa, e aparece como etiqueta: "isso aqui tem nome: *latência*".
5. **Humor de boteco, respeito de almoço de domingo.** Pode brincar, pode usar gíria leve e meme conhecido. Não pode estereótipo de região, gênero, classe ou religião, nem piada às custas de grupo nenhum. Varie as regiões: o Brasil não é só Rio e São Paulo (tem açaí em Belém, chimarrão no Sul, feira de Caruaru, forró, tacacá, pão de queijo).
6. **Correção primeiro.** Simplificar é cortar detalhe, não inventar. Números, datas e fatos têm que estar certos; se não tiver certeza de um dado, deixe de fora ou diga que é aproximado.

## Fluxo

### 1. Entender o pedido (sem interrogatório)

Descubra o tema e o que a pessoa já sabe a partir da mensagem e do material que ela mandou (documento, print, link, conversa colada: leia tudo). Só pergunte se o tema for ambíguo de verdade ("explica o Copom" é claro; "explica isso" sem anexo não é), e aí faça **uma** pergunta. Na dúvida sobre o nível, assuma zero.

### 2. Achar o fio da meada

Antes de desenhar, escreva para si (não mostre):

- **A frase de almoço**: o assunto inteiro numa frase que qualquer pessoa entenderia na mesa do almoço de domingo. Ex.: "Juros é o aluguel do dinheiro."
- **3 a 6 ideias** que a pessoa precisa para entender, em ordem. Mais que seis vira aula; corte.
- **Uma comparação por ideia**, de preferência do mesmo universo (se começou na feira, fique na feira) para a história ter continuidade. O repertório em [references/repertorio.md](references/repertorio.md) tem cenas prontas por tipo de conceito; use como ponto de partida, não como cardápio fixo.
- **Onde cada comparação quebra.**

### 3. Montar a página

Uma página HTML única, autocontida (CSS e SVG inline, nada externo), que abre em qualquer navegador. Se usar Google Fonts, sempre com fallback do sistema (`font-family: "Baloo 2", system-ui, sans-serif`), porque alguns ambientes bloqueiam fontes externas. Estrutura:

1. **Capa**: título com graça (ex.: "Inflação, ou: por que o pão de queijo ficou caro") + a frase de almoço em destaque + um desenho grande.
2. **Quadros** (3 a 6): cada um com desenho grande (ocupa a maior parte da largura), um título de até 6 palavras e no máximo duas frases. Numere os quadros, como uma história em quadrinhos.
3. **Onde a comparação falha**: lista curta, uma linha por comparação.
4. **Resumo de bolso**: 3 bullets que cabem num print de celular.
5. **Pra ir mais fundo** (opcional): 2 ou 3 perguntas que a pessoa pode fazer em seguida.

Detalhes de desenho e layout em [references/desenho.md](references/desenho.md). Leia antes de escrever o primeiro SVG.

### 4. Entregar

- **Onde existe artifact** (claude.ai, Cowork, ou uma ferramenta que publica páginas): crie o artifact HTML; se a ferramenta devolver um link, mande o link.
- **Onde dá para gravar arquivo** (Claude Code, Cowork): salve como `<tema>-desenhado.html` na pasta de trabalho e diga o caminho.
- **Onde só existe texto** (terminal sem arquivo, chat sem artifact, ou a pessoa pediu "só aqui na conversa"): faça a versão de bolso em Markdown, com os mesmos quadros desenhados em ASCII dentro de blocos de código, cada um com no máximo 12 linhas de altura e 60 colunas de largura, e a legenda curta embaixo.

Depois de entregar a página ou o arquivo, não repita a explicação no chat: uma linha com o link ou caminho e a frase de almoço basta. No modo só texto, a resposta é a própria versão de bolso.

## Exemplo de quadro em ASCII (modo só texto)

Tema: o que é latência.

```
  VOCÊ                                  SERVIDOR
  (o_o)  -- "oi" -->  ~~~~~~~~~~~~~~~>   [####]
   /|\                                   [####]
   / \   <-- "oi" --  <~~~~~~~~~~~~~~~   [####]

         |<------ tempo de ida e volta ------>|
```

**1. A conversa com eco.** É ligar pra tia que está em Portugal: você fala, espera, e só depois ouve a resposta. Esse tempo de espera tem nome: *latência*.

## Antes de entregar, confira

- [ ] Dá para entender a ideia só olhando os desenhos, sem ler nada?
- [ ] Cada comparação é fiel ao mecanismo, e a falha dela está declarada?
- [ ] Nenhum termo técnico apareceu antes de ser mostrado?
- [ ] Nenhum quadro tem mais de duas frases?
- [ ] Os fatos e números estão certos?
- [ ] O humor não pisa em ninguém?
- [ ] A página funciona no celular e no modo escuro?
