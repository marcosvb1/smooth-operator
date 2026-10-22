# Repertório de comparações brasileiras

Cenas do dia a dia agrupadas pelo tipo de mecanismo que elas explicam. Escolha pelo **mecanismo**, não pelo assunto: "fila do banco" serve para filas de servidor, para fila do SUS e para fila de impressão, porque o mecanismo é o mesmo.

Cada linha traz a cena, o que ela explica bem e onde costuma quebrar. Toda comparação quebra em algum ponto: descubra onde antes de usar. Invente cenas novas sempre que encaixarem melhor; esta lista é ponto de partida.

## Filas, espera e capacidade

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Fila do banco com senha (preferencial, normal) | filas com prioridade, escalonamento | na fila real dá para negociar; no sistema a regra é cega |
| Padaria às 7h: um balconista, vinte pessoas | gargalo, capacidade, por que contratar mais ajuda até certo ponto | o pão acaba; o pedido ao servidor não |
| Ônibus lotado na hora do rush | congestionamento de rede, limite de capacidade | no ônibus sempre cabe mais um; no servidor, não |
| Catraca do metrô | controle de acesso, *rate limiting* | a catraca não sabe quem você é; o sistema pode saber |
| Restaurante por quilo vs. rodízio | pagar pelo uso vs. preço fixo (nuvem, planos) | no rodízio a barriga é o limite; na nuvem, a conta |

## Dinheiro, juros e economia

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Aluguel de casa | juros como "aluguel do dinheiro" | dinheiro não estraga com o uso |
| Fiado na venda do seu Zé, anotado na caderneta | crédito, confiança, *score*, livro-razão | o seu Zé esquece; o banco não |
| Vaquinha do churrasco | rateio, orçamento compartilhado, quem não pagou | na vaquinha todo mundo se conhece |
| Pão de queijo que custava X e hoje custa Y (use preços reais com o ano, ou diga que é exemplo) | inflação, poder de compra | inflação é média de muitos preços, não de um |
| Feira no fim do dia, xepa mais barata | oferta e demanda, preço dinâmico | a xepa é mais barata porque a fruta está passando, não só pela demanda |
| Carnê da loja de eletro / parcelado em 10x "sem juros" | parcelamento, juros embutidos, valor do dinheiro no tempo | às vezes o "sem juros" é mesmo sem juros, e o custo está no preço à vista |
| Pix vs. TED vs. boleto | sistemas de pagamento, liquidação instantânea vs. compensação | quase sem falha: é o próprio sistema, não uma comparação |

## Comunicação, redes e informação

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Grupo da família no WhatsApp | *broadcast*, mensagem para muitos, corrente e desinformação | no grupo dá para responder; num *broadcast* técnico, nem sempre |
| Telefone sem fio na festa junina | ruído, perda de informação a cada repasse | no jogo ninguém confere; na rede existe checagem (*checksum*) |
| Correios: endereço, CEP, carteiro; nome do destinatário → endereço como numa lista telefônica | pacotes de rede, roteamento, IP; a lista telefônica é o DNS | carta não se divide em pedaços |
| Ligar pra tia em Portugal (aquele delay) | latência | a tia ainda pode estar só pensando; a latência é só a viagem |
| Cartório com firma reconhecida | assinatura digital, certificado, autenticidade | o cartório confere a pessoa; a assinatura digital confere a matemática |
| Walkie-talkie ou rádio PX de caminhoneiro: todo mundo no mesmo canal, um fala por vez | canal compartilhado, colisão, interferência | no rádio, quem grita mais alto ganha; na rede há regras de vez |

## Organização, regras e sistemas

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Escalação do time e o técnico | orquestração, papéis, estratégia | o jogador desobedece; o programa, não |
| Juiz e VAR | segunda opinião com replay, revisão por outra instância | o VAR só revê lances que alguém chamou |
| Síndico e assembleia do condomínio | governança, votação, consenso | na *blockchain* não há síndico nem assembleia: o consenso é sem autoridade central |
| Escola de samba: alas, bateria, enredo, desfile cronometrado | sistema com muitas partes sincronizadas, *deadline* | o desfile acontece uma vez por ano; o sistema roda todo dia |
| Receita de bolo da vó | algoritmo, passo a passo, ordem importa | a vó improvisa; o computador não |
| Cozinha de restaurante: chef, auxiliares, pedidos na comanda | divisão de trabalho, filas, paralelismo | cozinheiro cansa; processo não |
| Gaveta de bagunça da cozinha vs. caixa de ferramentas organizada | estrutura de dados, indexação, busca | a gaveta é pequena; o banco de dados tem milhões de itens |

## Memória, armazenamento e aprendizado

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Geladeira (perto, pouco espaço) vs. despensa (longe, muito espaço) | cache vs. disco, memória RAM | a geladeira não esvazia quando falta luz; a RAM, sim |
| Caderno de receitas da família passado de geração em geração | backup, versionamento, herança | o caderno tem uma cópia só; backup bom tem várias |
| Decorar o gabarito da prova em vez de aprender a matéria | memorização vs. entendimento (*overfitting*) | o aluno sabe que decorou; o modelo, não |
| Criança aprendendo a falar ouvindo a família | aprendizado de máquina por exemplos | a criança entende o mundo; o modelo aprende padrões |
| Cursinho que treina para o Enem com provas antigas | treino com dados históricos, generalização | a prova muda pouco; o mundo real muda muito |

## Segurança e risco

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Golpe do falso parente no WhatsApp | engenharia social, *phishing* | o golpe por e-mail costuma ser em massa, não pessoal |
| Cadeado, portão, cachorro e alarme na mesma casa | defesa em camadas | ladrão de casa não é automatizado; ataque digital é |
| Chave do portão escondida debaixo do tapete | senha fraca, segredo previsível | só o vizinho tenta o tapete; na internet, robôs tentam milhões de senhas |
| Seguro do carro | risco, prêmio, franquia | o seguro paga depois; segurança evita antes |
| Vacina | treinar a defesa antes do ataque | analogia biológica: use com cuidado em temas técnicos |

## Ciência e natureza

| Cena | Explica bem | Onde quebra |
| --- | --- | --- |
| Panela de pressão | pressão e ponto de ebulição | quase sem falha: é o próprio fenômeno |
| Chimarrão que esfria na cuia | troca de calor, equilíbrio térmico | quase sem falha: é o próprio fenômeno |
| Chuva da tarde em Belém | ciclo da água, convecção, previsibilidade | nem todo dia chove na hora certa |
| Enchente na rua sem bueiro | escoamento, capacidade de drenagem, gargalo | a água não volta sozinha para tentar de novo; a requisição, sim |
| Açaí batido: separa se deixar parado | mistura, densidade, decantação | quase sem falha: é o próprio fenômeno |

## Lugares e sotaques para variar

Use para não deixar tudo no Sudeste: feira de Caruaru, Ver-o-Peso, Mercado Central de BH, rodoviária de Brasília, praia em Fortaleza, CTG no Sul, Parintins (boi Garantido e Caprichoso), São João de Campina Grande, Círio de Nazaré. Comidas: tacacá, acarajé, pão de queijo, chimarrão, coxinha, pastel de feira, cuscuz, baião de dois, pequi (com cuidado).

## Evite

- Estereótipos do tipo "o povo de tal lugar é assim", e os de gênero, classe ou religião.
- Personagens, marcas e mascotes protegidos desenhados ou citados como protagonistas (Turma da Mônica, Chaves, personagens de novela): cite a cena, não o personagem.
- Política partidária e futebol de um time só: use "o seu time", não "o Flamengo".
- Referências que exigem ter vivido uma época específica, a menos que a pessoa tenha dado esse sinal.
