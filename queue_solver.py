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
    """Métricas básicas de um sistema M/M/s estável: retorna (rho, p0, Lq, Wq, W, L)."""
    rho = lam / (s * mu)
    sum_p0 = sum(((lam / mu) ** i) / math.factorial(i) for i in range(s))
    last_term = (((lam / mu) ** s) / math.factorial(s)) * (1 / (1 - rho))
    p0 = 1 / (sum_p0 + last_term)
    Lq = (p0 * ((lam / mu) ** s) * rho) / (math.factorial(s) * ((1 - rho) ** 2))
    Wq = Lq / lam
    W = Wq + (1 / mu)
    L = lam * W
    return rho, p0, Lq, Wq, W, L

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

def _metrics_from_weights(weights, s):
    """Dado os pesos (probabilidades não-normalizadas) de cada estado n=0,1,...,
    retorna (probs, L, Lq) já normalizados. Vale para qualquer nº de servidores s."""
    total = sum(weights)
    probs = [w / total for w in weights]
    L = sum(n * p for n, p in enumerate(probs))
    Lq = sum((n - s) * p for n, p in enumerate(probs) if n > s)
    return probs, L, Lq

class MM1K(QueueModel):
    """M/M/s/K — fila com s servidores e capacidade máxima K (s=1 => M/M/1/K)."""
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
        return {"Ocupação (ρ)": rho, "P0": p0, "Pk (Prob. Rejeição)": pk, "L": L, "Lq": Lq, "W": W, "Wq": Wq}

class MM1N(QueueModel):
    """M/M/s/N — população finita N com s servidores (s=1 => M/M/1/N)."""
    def __init__(self, lam: float, mu: float, n: int, s: int = 1):
        self.lam = lam
        self.mu = mu
        self.n = n
        self.s = s

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        if self.mu <= 0 or self.s < 1 or self.n < self.s:
            return {"Erro": "Parâmetros inválidos (exige μ>0, s>=1 e N>=s)."}

        a = self.lam / self.mu
        N = self.n
        weights = []
        for i in range(N + 1):
            if i <= self.s:
                weights.append(math.comb(N, i) * (a ** i))
            else:
                weights.append(
                    (math.factorial(N) / (math.factorial(N - i) * math.factorial(self.s) * (self.s ** (i - self.s))))
                    * (a ** i)
                )

        probs, L, Lq = _metrics_from_weights(weights, self.s)
        p0 = probs[0]

        lambda_bar = self.lam * (N - L)
        if lambda_bar > 0:
            W = L / lambda_bar
            Wq = Lq / lambda_bar
        else:
            W, Wq = 0, 0

        rho = lambda_bar / (self.s * self.mu)
        return {"Ocupação (ρ)": rho, "P0": p0, "L": L, "Lq": Lq, "W": W, "Wq": Wq}

class PriorityNonPreemptive(QueueModel):
    """Modelo com Prioridades SEM Interrupção"""
    def __init__(self, lambdas: list, mu: float, s: int):
        self.lambdas = lambdas
        self.mu = mu
        self.s = s

    def calcular(self, t=0.0, n=0, op_n="=") -> dict:
        lam_total = sum(self.lambdas)
        if self.mu <= 0 or lam_total >= (self.s * self.mu):
            return {"Erro": "Sistema instável (A soma dos λs é maior que s*μ)."}

        r = lam_total / self.mu
        
        # Denominador do W_k baseado no slide 11
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
                "Classe": f"Classe {i + 1}",
                "λ": lam_k,
                "W": round(w_k, 5),
                "Wq": round(wq_k, 5),
                "L": round(l_k, 5),
                "Lq": round(lq_k, 5)
            })
            a_k_minus_1 = a_k

        W_total = L_total / lam_total
        Wq_total = Lq_total / lam_total

        return {
            "Ocupação (ρ)": lam_total / (self.s * self.mu),
            "L": L_total, "Lq": Lq_total, "W": W_total, "Wq": Wq_total,
            "is_priority": True,
            "classes": resultados_classes
        }

class PriorityPreemptive(QueueModel):
    """Modelo com Prioridades COM Interrupção (Correção Exata para S > 1)"""
    def __init__(self, lambdas: list, mu: float, s: int):
        self.lambdas = lambdas
        self.mu = mu
        self.s = s

    def _get_mms_W(self, lam_agg: float) -> float:
        """Helper interno: Calcula o W de um modelo M/M/s normal dado um lambda misturado"""
        if lam_agg == 0: return 1 / self.mu
        rho = lam_agg / (self.s * self.mu)
        
        # Fórmula clássica do M/M/s
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

        # Método exato para qualquer s (slides 16-17): sob prioridade com interrupção, o
        # subsistema formado pelas classes 1..k é independente das de menor prioridade e se
        # comporta como um M/M/s com chegada acumulada A_k. O tempo médio no sistema dessas
        # classes combinadas, W̄_k, é o W de um M/M/s(A_k, μ, s). Isola-se W_k por classe via:
        #   W_k = (A_k·W̄_k - A_{k-1}·W̄_{k-1}) / λ_k
        # Para s=1 isto reduz à fórmula fechada (1/μ)/[(1-A_{k-1}/sμ)(1-A_k/sμ)].
        resultados_classes = []
        sum_lam_prev = 0
        sum_lam_W_prev = 0
        
        for i, lam_k in enumerate(self.lambdas):
            sum_lam_curr = sum_lam_prev + lam_k
            
            # Passo 1: Descobrir o W médio agregado das classes 1 até k 
            # (Igual ao W_1-2 barra do seu slide)
            w_agg = self._get_mms_W(sum_lam_curr)
            
            # Passo 2: Isolar o W_k usando a média ponderada
            # Equação baseada no W2 do slide: W2 = [ W_agg*(L1+L2) - W1*(L1) ] / L2
            w_k = ((w_agg * sum_lam_curr) - sum_lam_W_prev) / lam_k
            
            wq_k = w_k - (1 / self.mu)
            
            # Passo 3: Peculiaridade do cálculo acumulado de L e Lq do Slide 17
            l_k = sum_lam_curr * w_k
            lq_k = l_k - (sum_lam_curr / self.mu)
            
            resultados_classes.append({
                "Classe": f"Classe {i + 1}",
                "λ": lam_k,
                "W": round(w_k, 5),
                "Wq": round(wq_k, 5),
                "L": round(l_k, 5),     
                "Lq": round(lq_k, 5)    
            })
            
            # Guarda a somatória ponderada para a próxima iteração
            sum_lam_prev = sum_lam_curr
            sum_lam_W_prev += lam_k * w_k
            
        L_total = sum(c["L"] for c in resultados_classes)
        Lq_total = sum(c["Lq"] for c in resultados_classes)
        W_total = L_total / lam_total
        Wq_total = Lq_total / lam_total

        return {
            "Ocupação (ρ)": lam_total / (self.s * self.mu),
            "L": L_total, "Lq": Lq_total, "W": W_total, "Wq": Wq_total,
            "is_priority": True,
            "classes": resultados_classes
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