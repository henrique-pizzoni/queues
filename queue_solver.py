import math
from abc import ABC, abstractmethod

# --- Helpers de Probabilidade ---
def prob_mm1(rho, n, operador):
    if operador == "=": return (1 - rho) * (rho ** n)
    elif operador == ">": return rho ** (n + 1)
    elif operador == ">=": return rho ** n
    elif operador == "<": return 1 - (rho ** n)
    elif operador == "<=": return 1 - (rho ** (n + 1))
    return 0.0

def prob_lista(probs, n, operador):
    if n >= len(probs):
        return 0.0

    if operador == "=":
        return probs[n]
    elif operador == "<":
        return sum(probs[:n])
    elif operador == "<=":
        return sum(probs[:n + 1])
    elif operador == ">":
        return sum(probs[n + 1:])
    elif operador == ">=":
        return sum(probs[n:])

    return 0.0

def prob_mms_exata(lam, mu, s, p0, i):
    if i <= s:
        return (((lam / mu) ** i) / math.factorial(i)) * p0
    else:
        return (((lam / mu) ** i) / (math.factorial(s) * (s ** (i - s)))) * p0

def prob_mms_acumulada(lam, mu, s, p0, n, operador):
    if operador == "=": return prob_mms_exata(lam, mu, s, p0, n)
    elif operador in ["<", "<="]:
        limite = n if operador == "<=" else n - 1
        if limite < 0: return 0.0
        return sum(prob_mms_exata(lam, mu, s, p0, i) for i in range(limite + 1))
    elif operador in [">", ">="]:
        limite = n if operador == ">" else n - 1
        if limite < 0: return 1.0
        return 1.0 - sum(prob_mms_exata(lam, mu, s, p0, i) for i in range(limite + 1))
    return 0.0

def mms_metrics(lam, mu, s):
    rho = lam / (s * mu)
    sum_p0 = sum(((lam / mu) ** i) / math.factorial(i) for i in range(s))
    last_term = (((lam / mu) ** s) / math.factorial(s)) * (1 / (1 - rho))
    p0 = 1 / (sum_p0 + last_term)
    Lq = (p0 * ((lam / mu) ** s) * rho) / (math.factorial(s) * ((1 - rho) ** 2))
    Wq = Lq / lam
    W = Wq + (1 / mu)
    L = lam * W
    return rho, p0, Lq, Wq, W, L

def _metrics_from_weights(weights, s):
    total = sum(weights)

    probs = [w / total for w in weights]

    L = sum(i * p for i, p in enumerate(probs))

    Lq = sum(max(0, i - s) * p for i, p in enumerate(probs))

    return probs, L, Lq

# --- Classes dos Modelos ---
class QueueModel(ABC):
    @abstractmethod
    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        pass

class MM1(QueueModel):
    def __init__(self, lam: float, mu: float):
        self.lam = lam
        self.mu = mu

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        if self.mu <= 0 or self.lam >= self.mu:
            return {"Erro": "Sistema instável (λ >= μ) ou parâmetros inválidos."}
        
        rho = self.lam / self.mu
        p0 = 1 - rho
        L = self.lam / (self.mu - self.lam)
        Lq = (self.lam ** 2) / (self.mu * (self.mu - self.lam))
        W = 1 / (self.mu - self.lam)
        Wq = self.lam / (self.mu * (self.mu - self.lam))
        
        pn_calc = prob_mm1(rho, n, op_n)
        p_w_gt_t = math.exp(-self.mu * (1 - rho) * t)
        p_wq_gt_t = rho * math.exp(-self.mu * (1 - rho) * t)
        
        return {
            "Ocupação (ρ)": rho, "P0": p0, "L": L, "Lq": Lq, "W": W, "Wq": Wq,
            f"Prob. n {op_n} {n}": pn_calc, f"Prob. W > {t}": p_w_gt_t, f"Prob. Wq > {t}": p_wq_gt_t
        }

class MMs(QueueModel):
    def __init__(self, lam: float, mu: float, s: int):
        self.lam = lam
        self.mu = mu
        self.s = s

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        if self.mu <= 0 or self.lam >= (self.s * self.mu):
            return {"Erro": "Sistema instável (λ >= s*μ)."}

        rho, p0, Lq, Wq, W, L = mms_metrics(self.lam, self.mu, self.s)

        pn_calc = prob_mms_acumulada(self.lam, self.mu, self.s, p0, n, op_n)
        p_wq_0 = sum((((self.lam / self.mu) ** i) / math.factorial(i)) * p0 for i in range(self.s))
        p_wq_gt_t = (1 - p_wq_0) * math.exp(-self.s * self.mu * (1 - rho) * t)
        
        denom = self.s - 1 - (self.lam / self.mu)
        if abs(denom) < 1e-9:
            term = self.mu * t
        else:
            term = (1 - math.exp(-self.mu * t * denom)) / denom
        p_w_gt_t = math.exp(-self.mu * t) * (1 + ((p0 * ((self.lam / self.mu) ** self.s)) / (math.factorial(self.s) * (1 - rho))) * term)
        
        return {
            "Ocupação (ρ)": rho, "P0": p0, "L": L, "Lq": Lq, "W": W, "Wq": Wq,
            f"Prob. n {op_n} {n}": pn_calc, f"Prob. W > {t}": p_w_gt_t, f"Prob. Wq > {t}": p_wq_gt_t
        }

class MG1(QueueModel):
    def __init__(self, lam: float, mu: float, sigma2: float):
        self.lam = lam
        self.mu = mu
        self.sigma2 = sigma2

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        if self.mu <= 0 or self.lam >= self.mu:
            return {"Erro": "Sistema instável (λ >= μ)."}
        
        rho = self.lam / self.mu
        p0 = 1 - rho
        Lq = ((self.lam ** 2) * self.sigma2 + rho ** 2) / (2 * (1 - rho))
        Wq = Lq / self.lam
        W = Wq + (1 / self.mu)
        L = rho + Lq
        
        return {"Ocupação (ρ)": rho, "P0": p0, "L": L, "Lq": Lq, "W": W, "Wq": Wq}

class MM1K(QueueModel):
    def __init__(self, lam: float, mu: float, k: int, s: int = 1):
        self.lam = lam
        self.mu = mu
        self.k = k
        self.s = s

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        if self.mu <= 0 or self.s < 1 or self.k < self.s:
            return {"Erro": "Parâmetros inválidos (exige μ>0, s>=1 e K>=s)."}

        a = self.lam / self.mu
        weights = []
        for i in range(self.k + 1):
            if i <= self.s:
                weights.append((a ** i) / math.factorial(i))
            else:
                weights.append((a ** i) / (math.factorial(self.s) * (self.s ** (i - self.s))))

        probs, L, Lq = _metrics_from_weights(weights, self.s)
        p0 = probs[0]
        pk = probs[self.k]

        lambda_bar = self.lam * (1 - pk)
        if lambda_bar > 0:
            W = L / lambda_bar
            Wq = Lq / lambda_bar
        else:
            W, Wq = 0, 0

        rho = lambda_bar / (self.s * self.mu)
        pn_calc = prob_lista(probs, n, op_n)
        return {
            "Ocupação (ρ)": rho, "P0": p0, "Pk (Prob. Rejeição)": pk,
            "L": L, "Lq": Lq, "W": W, "Wq": Wq,
            f"Prob. n {op_n} {n}": pn_calc,
        }

class MM1N(QueueModel):
    def __init__(self, lam: float, mu: float, n: int, s: int = 1):
        self.lam = lam
        self.mu = mu
        self.n = n
        self.s = s

    def calcular(
        self,
        t=0.0,
        n=0,
        op_n="=",
        custo_maquina_hora=None,
        custo_servidor_hora=None,
        horas_dia=None
    ):
        if self.mu <= 0 or self.s < 1 or self.n < self.s:
            return {"Erro": "Parâmetros inválidos (exige μ>0, s>=1 e N>=s)."}

        a = self.lam / self.mu
        N = self.n

        weights = []

        for i in range(N + 1):

            if i <= self.s:

                peso = math.comb(N, i) * (a ** i)

            else:

                peso = (
                    math.factorial(N)
                    /
                    (
                        math.factorial(N - i)
                        * math.factorial(self.s)
                        * (self.s ** (i - self.s))
                    )
                ) * (a ** i)

            weights.append(peso)

        probs, L, Lq = _metrics_from_weights(weights, self.s)

        p0 = probs[0]

        lambda_bar = self.lam * (N - L)

        if lambda_bar > 0:
            W = L / lambda_bar
            Wq = Lq / lambda_bar
        else:
            W = 0
            Wq = 0

        rho = lambda_bar / (self.s * self.mu)

        servidores_ocupados = L - Lq

        utilizacao_servidor = servidores_ocupados / self.s

        maquinas_operando = N - L

        pn_calc = prob_lista(probs, n, op_n)

        resultados = {
            "Ocupação (ρ)": rho,
            "P0": p0,
            "Pn": probs,
            "L": L,
            "Lq": Lq,
            "W": W,
            "Wq": Wq,
            "Máquinas Operando": maquinas_operando,
            "Servidores Ocupados": servidores_ocupados,
            "Utilização Servidor": utilizacao_servidor,
            f"Prob. n {op_n} {n}": pn_calc
        }

        if (
            custo_maquina_hora is not None
            and custo_servidor_hora is not None
        ):

            custo_hora = (
                L * custo_maquina_hora
                +
                utilizacao_servidor * self.s * custo_servidor_hora
            )

            resultados["Custo Hora"] = custo_hora

            if horas_dia is not None:
                resultados["Custo Diário"] = custo_hora * horas_dia
        return resultados        
class PriorityNonPreemptive(QueueModel):
    def __init__(self, lambdas: list, mu: float, s: int):
        self.lambdas = lambdas
        self.mu = mu
        self.s = s

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        lam_total = sum(self.lambdas)
        if self.mu <= 0 or lam_total >= (self.s * self.mu):
            return {"Erro": "Sistema instável (A soma dos λs é maior que s*μ)."}

        r = lam_total / self.mu
        
        sum_j = sum((r ** j) / math.factorial(j) for j in range(self.s))
        term1 = (math.factorial(self.s) * ((self.s * self.mu) - lam_total) / (r ** self.s)) * sum_j + (self.s * self.mu)
        
        resultados_classes = []
        L_total = Lq_total = 0.0
        a_k_minus_1 = 0.0

        for i, lam_k in enumerate(self.lambdas):
            a_k = a_k_minus_1 + lam_k
            denom = term1 * (1 - (a_k_minus_1 / (self.s * self.mu))) * (1 - (a_k / (self.s * self.mu)))

            w_k = (1 / denom) + (1 / self.mu)
            wq_k = w_k - (1 / self.mu)
            l_k = lam_k * w_k
            lq_k = lam_k * wq_k
            L_total += l_k
            Lq_total += lq_k

            resultados_classes.append({
                "Classe": f"Classe {i + 1}", "λ": lam_k, "W": round(w_k, 5),
                "Wq": round(wq_k, 5), "L": round(l_k, 5), "Lq": round(lq_k, 5)
            })
            a_k_minus_1 = a_k

        W_total = L_total / lam_total
        Wq_total = Lq_total / lam_total

        return {
            "Ocupação (ρ)": lam_total / (self.s * self.mu),
            "L": L_total, "Lq": Lq_total, "W": W_total, "Wq": Wq_total,
            "is_priority": True, "classes": resultados_classes
        }

class PriorityPreemptive(QueueModel):
    def __init__(self, lambdas: list, mu: float, s: int):
        self.lambdas = lambdas
        self.mu = mu
        self.s = s

    def _get_mms_W(self, lam_agg: float) -> float:
        if lam_agg == 0: return 1 / self.mu
        rho = lam_agg / (self.s * self.mu)
        
        sum_p0 = sum(((lam_agg / self.mu) ** i) / math.factorial(i) for i in range(self.s))
        last_term = (((lam_agg / self.mu) ** self.s) / math.factorial(self.s)) * (1 / (1 - rho))
        p0 = 1 / (sum_p0 + last_term)
        
        lq = (p0 * ((lam_agg / self.mu) ** self.s) * rho) / (math.factorial(self.s) * ((1 - rho) ** 2))
        w = (lq / lam_agg) + (1 / self.mu)
        return w

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        lam_total = sum(self.lambdas)
        if self.mu <= 0 or lam_total >= (self.s * self.mu):
            return {"Erro": "Sistema instável (A soma dos λs é maior que s*μ)."}

        resultados_classes = []
        sum_lam_prev = sum_lam_W_prev = 0
        
        for i, lam_k in enumerate(self.lambdas):
            sum_lam_curr = sum_lam_prev + lam_k
            w_agg = self._get_mms_W(sum_lam_curr)
            w_k = ((w_agg * sum_lam_curr) - sum_lam_W_prev) / lam_k
            wq_k = w_k - (1 / self.mu)
            
            l_k = sum_lam_curr * w_k
            lq_k = l_k - (sum_lam_curr / self.mu)
            
            resultados_classes.append({
                "Classe": f"Classe {i + 1}", "λ": lam_k, "W": round(w_k, 5),
                "Wq": round(wq_k, 5), "L": round(l_k, 5), "Lq": round(lq_k, 5)
            })
            
            sum_lam_prev = sum_lam_curr
            sum_lam_W_prev += lam_k * w_k
            
        L_total = sum(c["L"] for c in resultados_classes)
        Lq_total = sum(c["Lq"] for c in resultados_classes)
        W_total = L_total / lam_total
        Wq_total = Lq_total / lam_total

        return {
            "Ocupação (ρ)": lam_total / (self.s * self.mu),
            "L": L_total, "Lq": Lq_total, "W": W_total, "Wq": Wq_total,
            "is_priority": True, "classes": resultados_classes
        }

class PriorityMG1(QueueModel):
    """Modelo M/G/1 com Prioridades (Múltiplos μ e Variâncias) para resolver o Exemplo 2"""
    def __init__(self, lambdas: list, mus: list, variancias: list):
        self.lambdas = lambdas
        self.mus = mus
        self.variancias = variancias

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        rhos = [lam / mu for lam, mu in zip(self.lambdas, self.mus)]
        rho_total = sum(rhos)
        
        if rho_total >= 1:
            return {"Erro": "Sistema instável (A soma das ocupações ρ é ≥ 1)."}

        numerador = sum(
            lam * (var + (1/mu)**2) 
            for lam, mu, var in zip(self.lambdas, self.mus, self.variancias)
        )

        resultados_classes = []
        soma_rho_anterior = 0.0
        
        for i in range(len(self.lambdas)):
            rho_k = rhos[i]
            soma_rho_atual = soma_rho_anterior + rho_k
            
            denominador = 2 * (1 - soma_rho_anterior) * (1 - soma_rho_atual)
            wq_k = numerador / denominador
            w_k = wq_k + (1 / self.mus[i])
            lq_k = self.lambdas[i] * wq_k
            l_k = self.lambdas[i] * w_k
            
            resultados_classes.append({
                "Classe": f"Classe {i + 1}", "λ": self.lambdas[i], "μ": self.mus[i],
                "W": round(w_k, 5), "Wq": round(wq_k, 5),
                "L": round(l_k, 5), "Lq": round(lq_k, 5)
            })
            soma_rho_anterior = soma_rho_atual

        lam_total = sum(self.lambdas)
        L_total = sum(c["L"] for c in resultados_classes)
        Lq_total = sum(c["Lq"] for c in resultados_classes)
        W_total = L_total / lam_total
        Wq_total = Lq_total / lam_total

        return {
            "Ocupação (ρ)": rho_total,
            "L": L_total, "Lq": Lq_total, "W": W_total, "Wq": Wq_total,
            "is_priority": True, "classes": resultados_classes
        }

# --- Funções de Engenharia Reversa (Módulo Investigador) ---
def reverse_rho_wq(rho, wq):
    mu = rho / (wq * (1 - rho))
    lam = rho * mu
    return lam, mu

def reverse_w_lq(w, lq):
    a = w ** 2
    b = -lq * w
    c = -lq
    delta = (b ** 2) - (4 * a * c)
    if delta < 0: return None, None
    lam = (-b + math.sqrt(delta)) / (2 * a)
    mu = lam + (1 / w)
    return lam, mu

def reverse_mu_wq(mu, wq):
    lam = (wq * (mu ** 2)) / (1 + wq * mu)
    return lam, mu

def reverse_lq_lam_md1(lq, lam):
    # Lq = ρ²/(2(1-ρ))  →  ρ² + 2Lq·ρ - 2Lq = 0  →  ρ = -Lq + √(Lq² + 2Lq)
    discriminant = lq ** 2 + 2 * lq
    if discriminant < 0:
        return None, None
    rho = -lq + math.sqrt(discriminant)
    if rho <= 0 or rho >= 1:
        return None, None
    mu = lam / rho
    return lam, mu