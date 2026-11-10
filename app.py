"""Ultimate Werewolf - Gerador de Vila (back-end Flask).
Rodar:  pip install flask && python app.py   ->  http://localhost:5000
"""
import json, math, os, random
from flask import Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE, "static"))
ROLES = {r["name"]: r for r in json.load(open(os.path.join(BASE, "data", "roles.json"), encoding="utf-8"))}

FILTROS = [  # tag -> rótulo do botão
    {"tag": "vampiros", "label": "Vampiros"},
    {"tag": "macons", "label": "Maçons"},
    {"tag": "lobos_especiais", "label": "Lobos especiais"},
    {"tag": "culto", "label": "Líder de Culto"},
]
CATEGORIAS = [("vila", "Aldeões"), ("info", "Investigadores"), ("prot", "Protetores"), ("caos", "Caóticos"),
              ("extra", "Extras"), ("macons", "Maçons"), ("lobos", "Lobisomens"), ("vampiros", "Vampiros"),
              ("culto", "Culto")]
LIMITAVEIS = ["info", "prot", "caos", "extra", "macons"]
# Máximo padrão por categoria: (a partir de N jogadores, máximo). O sorteio escolhe de 0 até esse valor
# (investigadores: de 1). Se faltar gente, ele completa e, se preciso, estoura o máximo. Edite à vontade.
PADROES = {
    "info":   [(6, 1), (10, 2), (18, 3), (30, 4), (45, 5), (60, 6)],
    "prot":   [(6, 1), (10, 2), (20, 3), (32, 4), (48, 5)],
    "caos":   [(6, 1), (12, 2), (22, 3), (34, 4), (50, 5)],
    "extra":  [(6, 2), (10, 3), (16, 4), (24, 5), (34, 6), (46, 7)],
    "macons": [(6, 0), (12, 2), (26, 3)],
}


def padroes(n):
    return {c: max((v for m, v in t if n >= m), default=t[0][1]) for c, t in PADROES.items()}


INIMIGOS = {"Werewolf", "Wolf Cub", "Sorcerer", "Vampire", "Minion", "Alpha Wolf"}  # "Bad Guys"
LIMIAR_EQUILIBRIO, LIMIAR_FORTE = 3, 10


def limpar(sel):
    """Mantém só papéis válidos, com quantidade entre 1 e o máximo."""
    out = {}
    for nome, q in (sel or {}).items():
        if nome in ROLES:
            q = max(0, min(int(q), ROLES[nome]["max"]))
            if q:
                out[nome] = q
    return out


def balanco(sel):
    total = sum(ROLES[n]["adj"] * q for n, q in sel.items())
    jogadores = sum(sel.values())
    inimigos = sum(q for n, q in sel.items() if n in INIMIGOS)
    esperados = max(1, math.ceil((jogadores - 4.5) / 3.5)) if jogadores else 0
    a = abs(total)
    if a <= LIMIAR_EQUILIBRIO:
        status, texto = "equilibrada", "Vila equilibrada"
    else:
        forca = "levemente" if a <= LIMIAR_FORTE else "muito"
        lado = "a vila" if total > 0 else "os inimigos"
        status = "vila" if total > 0 else "inimigos"
        texto = f"Favorece {forca} {lado}"
    avisos = []
    if jogadores and not 6 <= jogadores <= 68:
        avisos.append("A planilha original só admite de 6 a 68 jogadores.")
    if sel.get("Mason") == 1:
        avisos.append("Nunca deve haver apenas 1 Maçom.")
    if "Lone Wolf" in sel and sel.get("Werewolf", 0) < 2:
        avisos.append("Lobo Solitário exige pelo menos 2 Lobisomens.")
    if "Sorcerer" in sel and "Seer" not in sel:
        avisos.append("A Feiticeira procura a Vidente: a vila precisa ter uma Vidente.")
    if "Apprentice Seer" in sel and "Seer" not in sel:
        avisos.append("O Vidente Aprendiz precisa da Vidente na vila.")
    if jogadores and inimigos != esperados:
        avisos.append(f"Pela fórmula da planilha, {jogadores} jogadores teriam cerca de {esperados} inimigos (você tem {inimigos}).")
    return {"total": total, "jogadores": jogadores, "inimigos": inimigos, "esperados": esperados,
            "status": status, "texto": texto, "avisos": avisos}


QUANDO = {"first": "Só na 1ª noite", "every": "Toda noite", "once": "Uma vez no jogo",
          "n3": "Só na 3ª noite", "ident": "1ª noite · só identificar", "trigger": "Quando acontecer"}


def roteiro(sel):
    passos = {}

    def passo(n, no, acao):
        chave = (no["ordem"], no["fala"])  # papéis com a mesma fala acordam juntos (ex.: lobos)
        p = passos.setdefault(chave, {"ordem": no["ordem"], "fala": no["fala"], "quando": no["quando"],
                                      "papeis": [], "nomes": [], "acoes": [], "conferir": False})
        p["nomes"].append(n)
        p["papeis"].append(n if sel[n] == 1 else f"{n} ×{sel[n]}")
        p["acoes"].append(acao)
        p["conferir"] = p["conferir"] or ROLES[n]["conferir"]

    for n in sel:
        r = ROLES[n]
        if "ident" in r:
            passo(n, {"ordem": r["ident"]["ordem"], "fala": r["ident"]["fala"], "quando": "ident"}, r["ident"]["nota"])
        if "noite" in r:
            passo(n, r["noite"], r["acao"])
    lista = sorted(passos.values(), key=lambda p: (p["ordem"], p["fala"]))
    for p in lista:
        p["quando_txt"] = QUANDO[p["quando"]]
        p["acao"] = p["acoes"][0]
        del p["acoes"]
    primeira = [p for p in lista if p["quando"] not in ("trigger", "n3")]
    seguintes = [p for p in lista if p["quando"] not in ("first", "ident")]
    sem_acao = [n for n in sel if "noite" not in ROLES[n] and "ident" not in ROLES[n]]
    return {"primeira": primeira, "seguintes": seguintes, "sem_acao": sem_acao}


ESPECIAIS = ["info", "prot", "caos", "extra"]   # categorias sorteadas entre 0 (investigadores: 1) e o máximo


def gerar(n, alvo, vmax, fixos, off, limites=None, tentativas=500):
    """Sorteia a vila.
    - Aldeões: sorteia de 0 até vmax.
    - Investigadores: de 1 até o máximo (nem sempre a Vidente). Protetores, caóticos, extras: de 0 até o máximo.
    - Se faltar gente, completa com papéis das categorias que ainda não chegaram ao máximo (aldeões inclusos).
      Se ainda faltar, estoura o máximo, sempre na categoria que menos estourou até agora.
    - Fixos ficam. Entre as tentativas, vence a vila mais próxima do saldo-alvo."""
    fx = limpar(fixos)
    nfix = sum(fx.values())
    vmax = max(0, min(vmax, ROLES["Villager"]["max"]))
    if nfix > n:
        raise ValueError(f"Você fixou {nfix} cartas, mais que os {n} jogadores.")
    if fx.get("Villager", 0) > vmax:
        raise ValueError("Você fixou mais aldeões que o máximo permitido.")
    lim = padroes(n)
    for c, val in (limites or {}).items():
        if c in lim and val is not None:
            lim[c] = max(0, int(val))
    usados = {c: sum(q for k, q in fx.items() if ROLES[k]["grupo"] == c) for c in LIMITAVEIS}
    ok = lambda r: not any(t in off for t in r["tags"])
    n_mal = max(1, math.ceil((n - 4.5) / 3.5))          # nº de inimigos (fórmula da planilha)
    mal_fixo = sum(q for k, q in fx.items() if k in INIMIGOS)
    pools = {c: [r["name"] for r in ROLES.values() if r["grupo"] == c and ok(r)] for c in ESPECIAIS}
    melhor = None
    for _ in range(tentativas):
        v = dict(fx)
        cnt = dict(usados)
        over = {c: 0 for c in ESPECIAIS}
        livre = n - nfix

        def add(nome, q=1):
            nonlocal livre
            q = min(q, ROLES[nome]["max"] - v.get(nome, 0), livre)
            if q > 0:
                v[nome] = v.get(nome, 0) + q
                livre -= q
            return max(q, 0)

        def disponiveis(c):   # Aprendiz só entra se a Vidente já estiver na vila
            return [x for x in pools[c] if x not in v and (x != "Apprentice Seer" or "Seer" in v)]

        def sortear_cat(c, k):
            for _ in range(k):
                d = disponiveis(c)
                if livre <= 0 or not d:
                    break
                add(random.choice(d))
                cnt[c] += 1

        # 1) Investigadores: de 1 até o máximo (a Vidente é só mais uma opção)
        cap = max(0, lim["info"] - usados["info"])
        k = random.randint(1 if (cap >= 1 and usados["info"] == 0) else 0, cap)
        sortear_cat("info", max(0, min(k, livre - max(0, n_mal - mal_fixo))))
        tem_seer = "Seer" in v

        # 2) Inimigos (fórmula da planilha)
        mal = sum(q for k_, q in v.items() if k_ in INIMIGOS)
        falta = max(0, min(n_mal - mal, livre))
        reserva = 0 if v.get("Werewolf") else 1          # sempre ao menos 1 Lobisomem
        if falta > reserva + 1 and ok(ROLES["Vampire"]) and "Vampire" not in v and random.random() < .35:
            falta -= add("Vampire", random.randint(1, min(3, falta - reserva)))
        extras = ["Wolf Cub", "Sorcerer", "Alpha Wolf", "Minion"]
        random.shuffle(extras)
        for e in extras:
            if e == "Sorcerer" and not tem_seer:          # Feiticeira só com Vidente na vila
                continue
            if falta > reserva and ok(ROLES[e]) and e not in v and random.random() < .4:
                falta -= add(e)
        falta -= add("Werewolf", falta)
        if falta > 0 and ok(ROLES["Vampire"]):            # vilas grandes: faltam lobos, entram vampiros
            add("Vampire", falta)
        if not v.get("Werewolf") and livre:
            add("Werewolf")
        if v.get("Werewolf", 0) >= 2 and "Lone Wolf" not in v and ok(ROLES["Lone Wolf"]) and random.random() < .2:
            add("Lone Wolf")

        # 3) Maçons: 0 ou um grupo de 2-3, dentro do máximo
        cap_m = lim["macons"] - usados["macons"]
        if "Mason" not in v and ok(ROLES["Mason"]) and cap_m >= 2 and livre >= 2 and random.random() < .5:
            add("Mason", random.randint(2, min(3, cap_m, livre)))

        # 4) Protetores, caóticos, extras: de 0 até o máximo de cada um
        cats = ["prot", "caos", "extra"]
        random.shuffle(cats)
        for c in cats:
            sortear_cat(c, random.randint(0, max(0, lim[c] - usados[c])))

        # 5) Aldeões: de 0 até o máximo
        add("Villager", random.randint(0, vmax) - v.get("Villager", 0))

        # 6) Completar: primeiro quem ainda não chegou ao máximo; depois estourar o máximo
        while livre > 0:
            cand = [c for c in ESPECIAIS if cnt[c] < lim[c] and disponiveis(c)]
            if v.get("Villager", 0) < vmax:
                cand.append("Villager")
            if cand:
                c = random.choice(cand)
                if c == "Villager":
                    add("Villager")
                else:
                    add(random.choice(disponiveis(c)))
                    cnt[c] += 1
                continue
            cand = [c for c in ESPECIAIS if disponiveis(c)]
            if cand:
                m = min(over[c] for c in cand)             # prefere a categoria que menos estourou
                c = random.choice([c for c in cand if over[c] == m])
                add(random.choice(disponiveis(c)))
                cnt[c] += 1
                over[c] += 1
                continue
            antes = livre                                  # último recurso: aldeões além do máximo, depois lobos/vampiros
            add("Villager", livre)
            add("Werewolf", livre)
            if livre and ok(ROLES["Vampire"]):
                add("Vampire", livre)
            if livre == antes:
                break
        if livre:
            continue
        total = sum(ROLES[k_]["adj"] * q for k_, q in v.items())
        d = abs(total - alvo)
        if melhor is None or d < melhor[0]:
            melhor = (d, v, over)
            if d == 0:
                break
    if melhor is None:
        raise ValueError("Não foi possível montar uma vila com esses números e filtros. "
                         "Não há cartas suficientes para esse número de jogadores com os filtros atuais; "
                         "tente reativar algum grupo removido ou reduzir os fixos.")
    _, v, over = melhor
    gerados = {k: q - fx.get(k, 0) for k, q in v.items() if q > fx.get(k, 0)}
    return v, gerados, over


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/roles")
def api_roles():
    return jsonify(roles=list(ROLES.values()), filtros=FILTROS, limitaveis=LIMITAVEIS,
                   categorias=[{"id": i, "label": l} for i, l in CATEGORIAS])


@app.get("/api/padroes")
def api_padroes():
    n = max(6, min(68, request.args.get("n", 12, type=int)))
    return jsonify(padroes=padroes(n))


@app.post("/api/vila")
def api_vila():
    sel = limpar((request.get_json(silent=True) or {}).get("sel"))
    return jsonify(sel=sel, balanco=balanco(sel), roteiro=roteiro(sel))


@app.post("/api/gerar")
def api_gerar():
    d = request.get_json(silent=True) or {}
    try:
        n = max(6, min(68, int(d.get("n", 12))))
        alvo = max(-200, min(200, int(d.get("alvo", 0))))
        vmax = max(0, min(15, int(d.get("vmax", 15))))
        sel, gerados, over = gerar(n, alvo, vmax, d.get("sel"), set(d.get("off") or []), d.get("limites"))
    except (ValueError, TypeError) as e:
        return jsonify(erro=str(e)), 400
    rot = dict(CATEGORIAS)
    est = [f"+{q} em {rot[c]}" for c, q in over.items() if q]
    aviso = f"Para completar {n} jogadores, os máximos foram ampliados: {', '.join(est)}." if est else ""
    return jsonify(sel=sel, gerados=gerados, balanco=balanco(sel), roteiro=roteiro(sel), aviso=aviso)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
