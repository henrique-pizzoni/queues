"""Gera o passo a passo (fórmula simbólica + substituição numérica) de cada modelo.

Cada função recebe os parâmetros de entrada e o dicionário de resultados já calculado
por `queue_solver` e devolve uma lista de passos:

    {"titulo": str, "formula": <LaTeX>, "substituicao": <LaTeX com números e resultado>}

A camada de cálculo continua em `queue_solver.py`; aqui só formatamos para exibição.
"""


def _f(x, d=4):
    """Formata um número no padrão brasileiro para uso dentro de LaTeX (vírgula decimal)."""
    return f"{x:.{d}f}".replace(".", "{,}")


def _i(x):
    return str(int(round(x)))


# --- M/M/1 ---------------------------------------------------------------
def passos_mm1(p, r):
    lam, mu = p["lam"], p["mu"]
    rho = r["Ocupação (ρ)"]
    passos = [
        {
            "titulo": "Taxa de ocupação (ρ)",
            "formula": r"\rho = \frac{\lambda}{\mu}",
            "substituicao": rf"\rho = \frac{{{_f(lam,2)}}}{{{_f(mu,2)}}} = {_f(rho)}",
        },
        {
            "titulo": "Probabilidade de sistema vazio (P₀)",
            "formula": r"P_0 = 1 - \rho",
            "substituicao": rf"P_0 = 1 - {_f(rho)} = {_f(r['P0'])}",
        },
        {
            "titulo": "Nº médio no sistema (L)",
            "formula": r"L = \frac{\lambda}{\mu - \lambda}",
            "substituicao": rf"L = \frac{{{_f(lam,2)}}}{{{_f(mu,2)}-{_f(lam,2)}}} = {_f(r['L'])}",
        },
        {
            "titulo": "Nº médio na fila (Lq)",
            "formula": r"L_q = \frac{\lambda^2}{\mu(\mu - \lambda)}",
            "substituicao": rf"L_q = \frac{{{_f(lam,2)}^2}}{{{_f(mu,2)}({_f(mu,2)}-{_f(lam,2)})}} = {_f(r['Lq'])}",
        },
        {
            "titulo": "Tempo médio no sistema (W)",
            "formula": r"W = \frac{1}{\mu - \lambda}",
            "substituicao": rf"W = \frac{{1}}{{{_f(mu,2)}-{_f(lam,2)}}} = {_f(r['W'])}",
        },
        {
            "titulo": "Tempo médio na fila (Wq)",
            "formula": r"W_q = \frac{\lambda}{\mu(\mu - \lambda)}",
            "substituicao": rf"W_q = \frac{{{_f(lam,2)}}}{{{_f(mu,2)}({_f(mu,2)}-{_f(lam,2)})}} = {_f(r['Wq'])}",
        },
    ]
    _add_prob_n(passos, p, r, rho)
    _add_prob_tempo_mm1(passos, p, r, mu, rho)
    return passos


def _add_prob_n(passos, p, r, rho):
    op, n = p["op_n"], p["n"]
    chave = next((k for k in r if k.startswith("Prob. n")), None)
    if chave is None:
        return
    formulas = {
        "=": (r"P(n = %d) = (1-\rho)\rho^{%d}" % (n, n)),
        ">": (r"P(n > %d) = \rho^{%d}" % (n, n + 1)),
        ">=": (r"P(n \geq %d) = \rho^{%d}" % (n, n)),
        "<": (r"P(n < %d) = 1 - \rho^{%d}" % (n, n)),
        "<=": (r"P(n \leq %d) = 1 - \rho^{%d}" % (n, n + 1)),
    }
    passos.append({
        "titulo": f"Probabilidade P(n {op} {n})",
        "formula": formulas.get(op, ""),
        "substituicao": rf"= {_f(r[chave])}",
    })


def _add_prob_tempo_mm1(passos, p, r, mu, rho):
    t = p["t"]
    cw = next((k for k in r if k.startswith("Prob. W >")), None)
    cwq = next((k for k in r if k.startswith("Prob. Wq >")), None)
    if cw:
        passos.append({
            "titulo": f"Probabilidade P(W > {_f(t,2)})",
            "formula": r"P(W > t) = e^{-\mu(1-\rho)t}",
            "substituicao": rf"= e^{{-{_f(mu,2)}(1-{_f(rho)}){_f(t,2)}}} = {_f(r[cw])}",
        })
    if cwq:
        passos.append({
            "titulo": f"Probabilidade P(Wq > {_f(t,2)})",
            "formula": r"P(W_q > t) = \rho\, e^{-\mu(1-\rho)t}",
            "substituicao": rf"= {_f(rho)}\cdot e^{{-{_f(mu,2)}(1-{_f(rho)}){_f(t,2)}}} = {_f(r[cwq])}",
        })


# --- M/M/s ---------------------------------------------------------------
def passos_mms(p, r):
    lam, mu, s = p["lam"], p["mu"], p["s"]
    rho = r["Ocupação (ρ)"]
    passos = [
        {
            "titulo": "Taxa de ocupação (ρ)",
            "formula": r"\rho = \frac{\lambda}{s\,\mu}",
            "substituicao": rf"\rho = \frac{{{_f(lam,2)}}}{{{s}\cdot{_f(mu,2)}}} = {_f(rho)}",
        },
        {
            "titulo": "Probabilidade de sistema vazio (P₀)",
            "formula": r"P_0 = \left[\sum_{n=0}^{s-1}\frac{(\lambda/\mu)^n}{n!} + \frac{(\lambda/\mu)^s}{s!}\cdot\frac{1}{1-\rho}\right]^{-1}",
            "substituicao": rf"P_0 = {_f(r['P0'])}",
        },
        {
            "titulo": "Nº médio na fila (Lq)",
            "formula": r"L_q = \frac{P_0\,(\lambda/\mu)^s\,\rho}{s!\,(1-\rho)^2}",
            "substituicao": rf"L_q = \frac{{{_f(r['P0'])}\cdot({_f(lam/mu)})^{{{s}}}\cdot{_f(rho)}}}{{{s}!\,(1-{_f(rho)})^2}} = {_f(r['Lq'])}",
        },
        {
            "titulo": "Tempo médio na fila (Wq)",
            "formula": r"W_q = \frac{L_q}{\lambda}",
            "substituicao": rf"W_q = \frac{{{_f(r['Lq'])}}}{{{_f(lam,2)}}} = {_f(r['Wq'])}",
        },
        {
            "titulo": "Tempo médio no sistema (W)",
            "formula": r"W = W_q + \frac{1}{\mu}",
            "substituicao": rf"W = {_f(r['Wq'])} + \frac{{1}}{{{_f(mu,2)}}} = {_f(r['W'])}",
        },
        {
            "titulo": "Nº médio no sistema (L)",
            "formula": r"L = \lambda W",
            "substituicao": rf"L = {_f(lam,2)}\cdot{_f(r['W'])} = {_f(r['L'])}",
        },
    ]
    _add_prob_n_mms(passos, p, r)
    cw = next((k for k in r if k.startswith("Prob. W >")), None)
    cwq = next((k for k in r if k.startswith("Prob. Wq >")), None)
    if cw:
        passos.append({
            "titulo": f"Probabilidade P(W > {_f(p['t'],2)})",
            "formula": r"P(W>t)=e^{-\mu t}\left[1+\frac{P_0(\lambda/\mu)^s}{s!(1-\rho)}\cdot\frac{1-e^{-\mu t(s-1-\lambda/\mu)}}{s-1-\lambda/\mu}\right]",
            "substituicao": rf"= {_f(r[cw])}",
        })
    if cwq:
        passos.append({
            "titulo": f"Probabilidade P(Wq > {_f(p['t'],2)})",
            "formula": r"P(W_q>t)=\left[1-P(W_q=0)\right]e^{-s\mu(1-\rho)t}",
            "substituicao": rf"= {_f(r[cwq])}",
        })
    return passos


def _add_prob_n_mms(passos, p, r):
    op, n = p["op_n"], p["n"]
    chave = next((k for k in r if k.startswith("Prob. n")), None)
    if chave is None:
        return
    passos.append({
        "titulo": f"Probabilidade P(n {op} {n})",
        "formula": r"P_n=\frac{(\lambda/\mu)^n}{n!}P_0\ (n\le s),\quad P_n=\frac{(\lambda/\mu)^n}{s!\,s^{\,n-s}}P_0\ (n\ge s)",
        "substituicao": rf"P(n\,{op}\,{n}) = {_f(r[chave])}",
    })


# --- M/G/1 ---------------------------------------------------------------
def passos_mg1(p, r):
    lam, mu, sigma2 = p["lam"], p["mu"], p["sigma2"]
    rho = r["Ocupação (ρ)"]
    return [
        {
            "titulo": "Taxa de ocupação (ρ)",
            "formula": r"\rho = \frac{\lambda}{\mu}",
            "substituicao": rf"\rho = \frac{{{_f(lam,2)}}}{{{_f(mu,2)}}} = {_f(rho)}",
        },
        {
            "titulo": "Nº médio na fila (Lq) — Pollaczek-Khintchine",
            "formula": r"L_q = \frac{\lambda^2\sigma^2 + \rho^2}{2(1-\rho)}",
            "substituicao": rf"L_q = \frac{{{_f(lam,2)}^2\cdot{_f(sigma2,5)} + {_f(rho)}^2}}{{2(1-{_f(rho)})}} = {_f(r['Lq'])}",
        },
        {
            "titulo": "Nº médio no sistema (L)",
            "formula": r"L = \rho + L_q",
            "substituicao": rf"L = {_f(rho)} + {_f(r['Lq'])} = {_f(r['L'])}",
        },
        {
            "titulo": "Tempo médio na fila (Wq)",
            "formula": r"W_q = \frac{L_q}{\lambda}",
            "substituicao": rf"W_q = \frac{{{_f(r['Lq'])}}}{{{_f(lam,2)}}} = {_f(r['Wq'])}",
        },
        {
            "titulo": "Tempo médio no sistema (W)",
            "formula": r"W = W_q + \frac{1}{\mu}",
            "substituicao": rf"W = {_f(r['Wq'])} + \frac{{1}}{{{_f(mu,2)}}} = {_f(r['W'])}",
        },
    ]


# --- M/M/1/K -------------------------------------------------------------
def passos_mm1k(p, r):
    lam, mu, k = p["lam"], p["mu"], p["k"]
    rho = lam / mu
    pk = r.get("Pk (Prob. Rejeição)", 0.0)
    lam_bar = lam * (1 - pk)
    return [
        {
            "titulo": "Taxa de ocupação (ρ = λ/μ)",
            "formula": r"\rho = \frac{\lambda}{\mu}",
            "substituicao": rf"\rho = \frac{{{_f(lam,2)}}}{{{_f(mu,2)}}} = {_f(rho)}",
        },
        {
            "titulo": "Probabilidade de sistema vazio (P₀)",
            "formula": r"P_0 = \frac{1-\rho}{1-\rho^{K+1}}",
            "substituicao": rf"P_0 = \frac{{1-{_f(rho)}}}{{1-{_f(rho)}^{{{k}+1}}}} = {_f(r['P0'])}",
        },
        {
            "titulo": "Probabilidade de rejeição (P_K)",
            "formula": r"P_K = P_0\,\rho^{K}",
            "substituicao": rf"P_K = {_f(r['P0'])}\cdot{_f(rho)}^{{{k}}} = {_f(pk)}",
        },
        {
            "titulo": "Nº médio no sistema (L)",
            "formula": r"L = \frac{\rho}{1-\rho} - \frac{(K+1)\rho^{K+1}}{1-\rho^{K+1}}",
            "substituicao": rf"L = {_f(r['L'])}",
        },
        {
            "titulo": "Taxa efetiva de chegada (λ̄)",
            "formula": r"\bar{\lambda} = \lambda(1 - P_K)",
            "substituicao": rf"\bar{{\lambda}} = {_f(lam,2)}(1-{_f(pk)}) = {_f(lam_bar)}",
        },
        {
            "titulo": "Nº médio na fila (Lq)",
            "formula": r"L_q = L - (1 - P_0)",
            "substituicao": rf"L_q = {_f(r['L'])} - (1-{_f(r['P0'])}) = {_f(r['Lq'])}",
        },
        {
            "titulo": "Tempo médio no sistema (W)",
            "formula": r"W = \frac{L}{\bar{\lambda}}",
            "substituicao": rf"W = \frac{{{_f(r['L'])}}}{{{_f(lam_bar)}}} = {_f(r['W'])}",
        },
        {
            "titulo": "Tempo médio na fila (Wq)",
            "formula": r"W_q = \frac{L_q}{\bar{\lambda}}",
            "substituicao": rf"W_q = \frac{{{_f(r['Lq'])}}}{{{_f(lam_bar)}}} = {_f(r['Wq'])}",
        },
    ]


# --- M/M/1/N (população finita) ------------------------------------------
def passos_mm1n(p, r):
    lam, mu, N = p["lam"], p["mu"], p["pop_n"]
    lam_bar = lam * (N - r["L"])
    return [
        {
            "titulo": "Probabilidade de sistema vazio (P₀)",
            "formula": r"P_0 = \left[\sum_{n=0}^{N}\frac{N!}{(N-n)!}\left(\frac{\lambda}{\mu}\right)^n\right]^{-1}",
            "substituicao": rf"P_0 = {_f(r['P0'])}",
        },
        {
            "titulo": "Nº médio no sistema (L)",
            "formula": r"L = N - \frac{\mu}{\lambda}(1 - P_0)",
            "substituicao": rf"L = {N} - \frac{{{_f(mu,2)}}}{{{_f(lam,2)}}}(1-{_f(r['P0'])}) = {_f(r['L'])}",
        },
        {
            "titulo": "Nº médio na fila (Lq)",
            "formula": r"L_q = N - \frac{\lambda+\mu}{\lambda}(1 - P_0)",
            "substituicao": rf"L_q = {N} - \frac{{{_f(lam,2)}+{_f(mu,2)}}}{{{_f(lam,2)}}}(1-{_f(r['P0'])}) = {_f(r['Lq'])}",
        },
        {
            "titulo": "Taxa efetiva de chegada (λ̄)",
            "formula": r"\bar{\lambda} = \lambda(N - L)",
            "substituicao": rf"\bar{{\lambda}} = {_f(lam,2)}({N}-{_f(r['L'])}) = {_f(lam_bar)}",
        },
        {
            "titulo": "Tempo médio no sistema (W)",
            "formula": r"W = \frac{L}{\bar{\lambda}}",
            "substituicao": rf"W = \frac{{{_f(r['L'])}}}{{{_f(lam_bar)}}} = {_f(r['W'])}",
        },
        {
            "titulo": "Tempo médio na fila (Wq)",
            "formula": r"W_q = \frac{L_q}{\bar{\lambda}}",
            "substituicao": rf"W_q = \frac{{{_f(r['Lq'])}}}{{{_f(lam_bar)}}} = {_f(r['Wq'])}",
        },
    ]


# --- Prioridades ---------------------------------------------------------
def passos_prioridade(p, r, preemptivo):
    mu, s = p["mu"], p["s"]
    if preemptivo:
        if s == 1:
            wk_formula = r"W_k = \dfrac{1/\mu}{\left(1-\frac{A_{k-1}}{s\mu}\right)\left(1-\frac{A_k}{s\mu}\right)}"
        else:
            wk_formula = r"\bar{W}_k = W_{M/M/s}(A_k,\mu,s),\qquad W_k = \frac{A_k\bar{W}_k - A_{k-1}\bar{W}_{k-1}}{\lambda_k}"
        intro = "Prioridade **com** interrupção (preemptiva)."
    else:
        wk_formula = (
            r"W_k = \frac{1}{\Big(s!\,\frac{s\mu-\lambda}{r^s}\sum_{j=0}^{s-1}\frac{r^j}{j!}+s\mu\Big)"
            r"\left(1-\frac{A_{k-1}}{s\mu}\right)\left(1-\frac{A_k}{s\mu}\right)} + \frac{1}{\mu}"
        )
        intro = "Prioridade **sem** interrupção (não preemptiva)."

    passos = [
        {
            "titulo": "Tempo médio no sistema por classe (W_k)",
            "formula": wk_formula,
            "substituicao": rf"A_k = \sum_{{i=1}}^{{k}}\lambda_i,\quad \mu={_f(mu,2)},\quad s={s}",
        },
        {
            "titulo": "Relações por classe (Little)",
            "formula": r"W_{q,k} = W_k - \frac{1}{\mu},\quad L_k = \lambda_k W_k,\quad L_{q,k} = \lambda_k W_{q,k}",
            "substituicao": r"\text{Valores por classe na tabela acima.}",
        },
    ]
    return passos, intro
