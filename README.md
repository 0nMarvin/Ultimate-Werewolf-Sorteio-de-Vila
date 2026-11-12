# Ultimate Werewolf · Gerador de Vila e Assistente do Narrador

Site estático (HTML + JavaScript puro), **sem servidor e sem instalação**. Ele monta a vila de uma partida de Ultimate Werewolf (6 a 68 jogadores) e ajuda o narrador durante a noite: roteiro de chamados, anotações, placar e relatório. Tudo roda no navegador e funciona direto no GitHub Pages.

https://0nmarvin.github.io/Ultimate-Werewolf-Sorteio-de-Vila/

---

## O que o app faz

O app tem três abas na barra inferior.

**Vila** — monta a vila.
- Define jogadores, máximo de aldeões, perfil do grupo e saldo alvo, e sorteia os papéis.
- 📌 *Fixar tudo* transforma o resultado em papéis fixos; *Limpar vila* esvazia.
- A lista pode ser vista **por categoria**, **por time** (vila, lobos, vampiros, culto) ou **só os papéis específicos**.

**Papéis** — controle manual e filtros.
- *Remover grupos* tira do jogo vampiros, maçons, lobos especiais ou o Líder de Culto.
- Você fixa papéis com os botões − / +, e papéis fixados nunca são trocados pelo sorteio.
- Os máximos por categoria ficam nas configurações extras.

**Narrador** — durante a partida, com três subabas. Você pode **deslizar para o lado** para trocar entre elas.
- **Roteiro:** os chamados da noite atual (navegue com ‹ ›), na ordem certa, com a fala do narrador. Cada chamado tem:
  - caixa "Chamado" e botão "Eliminado" / "Voltou";
  - "⚡ Poder usado" para poderes de uso único;
  - 📝 para anotar alvos (quem morre, quem é protegido...). O nome anotado fica visível, em tom suave, no card.
- **Jogadores:** quem recebeu cada papel, em duas zonas, *Vila* e *Antagonistas*. Arraste o ⠿ para mudar alguém de lado (ex.: Amaldiçoado que virou lobo). O 💀 marca quem morreu e o ❤️ traz de volta.
- **Diário:** anotações por noite e o relatório de encerramento.

No topo fica o **placar**, com a contagem de jogadores vivos por time e a barra de equilíbrio da vila.

---

## Estrutura dos arquivos

| Arquivo | Para que serve |
|---|---|
| `index.html` | Interface: HTML, CSS e o JavaScript das telas (abas, roteiro, jogadores, diário, placar). |
| `engine.js` | "Motor": sorteio da vila, cálculo de equilíbrio, geração do roteiro. Não mexe na tela. |
| `roles-data.js` | **Lista de papéis** (nomes, pesos, falas, regras). Tem um guia de escrita no comentário do topo. |
| `.nojekyll` | Diz ao GitHub Pages para servir os arquivos como estão. Mantenha. |
| `README.md` | Este arquivo. |

---

## Publicar no GitHub Pages

1. Crie um repositório e envie todos os arquivos desta pasta para a raiz dele (inclusive `.nojekyll`).
2. No GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, escolha a branch `main` e a pasta `/ (root)`.
3. Aguarde cerca de 1 minuto. O site fica em `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/`.
4. Depois de cada alteração, faça commit e push. Se a página parecer antiga, recarregue com **Ctrl+F5**.

Para testar localmente, abra o `index.html` direto no navegador (não precisa de servidor).

---

## Como o sorteio funciona

- O número de **inimigos** é fixo pelo número de jogadores, pela fórmula da planilha original: `ceil((jogadores − 4,5) / 3,5)`, no mínimo 1. O que varia é a composição (Lobisomem, Filhote, Feiticeira, Lobo Alfa, Lacaio, Vampiros...).
- **Aldeões:** sorteia de 0 até o máximo informado.
- **Investigadores:** de 1 até o máximo da categoria. A Vidente é só uma das opções.
- **Protetores, Caóticos e Extras:** de 0 até o máximo de cada categoria.
- **Maçons:** nenhum, ou um grupo de 2 a 3.
- Se a soma não completar os jogadores, o app acrescenta papéis das categorias que ainda não chegaram ao máximo. Se ainda faltar gente, ele passa do máximo, sempre na categoria que menos passou até agora. Quando isso acontece, aparece um aviso.
- Dependências fixas: Feiticeira e Vidente Aprendiz só entram se a Vidente estiver na vila.
- Entre 500 tentativas, vence a vila mais próxima do **saldo alvo** (soma dos pesos `adj`).

---

## Onde alterar cada coisa

| Quero... | Onde mexer |
|---|---|
| Criar, remover ou editar um papel (nome, peso, falas, regras) | `roles-data.js`. Leia o comentário no topo do arquivo. |
| Mudar o máximo padrão de cada categoria por tamanho de vila | `engine.js`, constante `PADROES`. |
| Mudar a fórmula de quantidade de inimigos | `engine.js`, função `nInimigos` (e a mesma conta em `balanco`). |
| Mudar o que é "equilibrada", "levemente" ou "muito" | `engine.js`, `LIMIAR_EQUILIBRIO` e `LIMIAR_FORTE`. |
| Definir quais papéis contam como inimigos | `engine.js`, constante `INIMIGOS`. |
| Criar um grupo removível novo (como "Vampiros") | `engine.js`, `FILTROS`, e a tag correspondente nos papéis. |
| Criar uma categoria nova | `engine.js`, `CATEGORIAS`, e `LIMITAVEIS`/`PADROES` se ela tiver limite. |
| Tirar um papel da lista de chamados | `engine.js`, `SEM_CHAMADA`, ou remova o bloco `noite` do papel. |
| Dar ao papel o botão 📝 de anotar alvos | `index.html`, `EF_ROLE`. Os tipos de anotação estão em `EFEITOS`. |
| Papel com vários poderes de uso único (como a Bruxa) | `index.html`, constante `MULTI`. |
| Mudar os nomes dos times | `index.html`, constante `GT`. |
| Mudar cores | `index.html`, variáveis CSS em `:root` (`--bg`, `--acc`, `--bad`...). |
| Mudar textos e legendas das noites | `engine.js`, `QUANDO`, e os textos no `index.html`. |

---

## Dados salvos

Tudo é guardado no `localStorage` do navegador. Os dados ficam **só naquele navegador e aparelho** e não vão para nenhum servidor.

| Chave | O que guarda |
|---|---|
| `uw2` | Vila: papéis fixos, sorteados, limites e grupos removidos. |
| `uw3` | Partida: nomes dos jogadores, mortos, lado de cada um, anotações, poderes usados e noite atual. |
| `uw4` | Interface: aba aberta, visão da Vila, chamados feitos e campos do sorteio. |
| `uw5` | Configurações dos poderes múltiplos (ex.: Bruxa). |

- **Nova partida:** use *Limpar anotações da partida* no Diário, que limpa só o que a partida anotou. Para limpar a vila, use *Limpar vila*.
- **Zerar tudo:** limpe os dados do site nas configurações do navegador (ou apague as chaves acima no DevTools, aba *Application → Local Storage*).
- **Mudou o formato dos dados:** se alterar a estrutura de algo salvo, use um nome de chave novo (por exemplo `uw6`) para não conflitar com dados antigos.

---

## Dicas de depuração

- **Página em branco depois de editar:** quase sempre é vírgula faltando ou sobrando (ou aspas simples) em `roles-data.js`. Abra o Console (**F12**) para ver a linha do erro.
- **Mudança não aparece no site publicado:** recarregue com Ctrl+F5 e espere o GitHub Pages terminar de publicar (cerca de 1 minuto).
- **Papel novo não aparece no sorteio:** confira o `grupo` e as `tags`. Se o grupo estiver removido na aba Papéis, o papel é excluído do sorteio.
- **Papel novo não é chamado no roteiro:** ele precisa do bloco `noite` (ou `ident`) com `ordem`, `quando` e `fala`.

---

## Observações

- O sorteio e o equilíbrio seguem a planilha original, que só admite de **6 a 68 jogadores**.
- Os papéis e as falas foram escritos a partir das regras do jogo. Papéis marcados com `conferir: true` mostram um aviso para checar o texto na sua carta.
