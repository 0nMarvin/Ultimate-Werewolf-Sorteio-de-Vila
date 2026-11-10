# Ultimate Werewolf · Gerador de Vila (mobile)

Flask (Python) + HTML/JS puro. Baseado nos valores da planilha "Laz's Ultimate Werewolf – Random Village Generator v1.02".

    pip install -r requirements.txt
    python app.py            # abre em http://localhost:5000 (use o IP da máquina no celular, mesma rede Wi-Fi)

Para publicar: qualquer host Python (Render, Railway, PythonAnywhere) com `python app.py` ou `gunicorn app:app`.

## Onde editar
`data/roles.json`: valor de balanceamento (`adj`), grupo, tags dos filtros e, em `noite`, a ordem da chamada (`ordem`, menor = primeiro),
quando age (`first`, `every`, `once`, `n3`, `trigger`) e a `fala` do narrador. Cole ali o texto exato da sua carta/livro de regras.
Papéis com `"conferir": true` mostram um aviso no app: texto/regra escritos de forma resumida, a confirmar.
Limiares do balanceamento: `LIMIAR_EQUILIBRIO` e `LIMIAR_FORTE` em `app.py`.

Sorteio: aldeões de 0 até o máximo; investigadores de 1 até o máximo; protetores, caóticos e extras de 0 até o máximo da categoria. Se faltar gente, completa; se ainda faltar, estoura o máximo na categoria que menos estourou.
