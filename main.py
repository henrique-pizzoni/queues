import streamlit as st
import math

# --- Funções Auxiliares de Probabilidade ---
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
    if operador == "=":
        return prob_mms_exata(lam, mu, s, p0, n)
    elif operador in ["<", "<="]:
        limite = n if operador == "<=" else n - 1
        if limite < 0: return 0.0
        return sum(prob_mms_exata(lam, mu, s, p0, i) for i in range(limite + 1))
    elif operador in [">", ">="]:
        limite = n if operador == ">" else n - 1
        if limite < 0: return 1.0
        p_menor_igual = sum(prob_mms_exata(lam, mu, s, p0, i) for i in range(limite + 1))
        return 1.0 - p_menor_igual
    return 0.0

# --- Funções de Cálculo Padrão ---
def calc_mm1(lam, mu, t=0.0, n=0, op_n="="):
    if mu == 0 or lam >= mu:
        return {"Erro": "Sistema instável (λ >= μ) ou divisão por zero."}
    
    rho = lam / mu
    p0 = 1 - rho
    pn_calc = prob_mm1(rho, n, op_n)
    
    L = lam / (mu - lam)
    Lq = (lam ** 2) / (mu * (mu - lam))
    W = 1 / (mu - lam)
    Wq = lam / (mu * (mu - lam))
    
    p_w_gt_t = math.exp(-mu * (1 - rho) * t)
    p_wq_gt_t = rho * math.exp(-mu * (1 - rho) * t)
    
    return {
        "Taxa de Ocupação (ρ)": rho, "Prob. Sistema Vazio (P0)": p0, 
        f"Prob. n {op_n} {n}": pn_calc,
        "Nº Médio no Sistema (L)": L, "Nº Médio na Fila (Lq)": Lq, 
        "Tempo Médio no Sist. (W)": W, "Tempo Médio na Fila (Wq)": Wq, 
        f"Prob. de W > {t}": p_w_gt_t, f"Prob. de Wq > {t}": p_wq_gt_t
    }

def calc_mms(lam, mu, s, t=0.0, n=0, op_n="="):
    if mu == 0 or lam >= (s * mu):
        return {"Erro": "Sistema instável (λ >= s*μ) ou divisão por zero."}
    
    rho = lam / (s * mu)
    
    sum_p0 = sum(((lam / mu) ** i) / math.factorial(i) for i in range(s))
    last_term = (((lam / mu) ** s) / math.factorial(s)) * (1 / (1 - rho))
    p0 = 1 / (sum_p0 + last_term)
    
    pn_calc = prob_mms_acumulada(lam, mu, s, p0, n, op_n)
        
    Lq = (p0 * ((lam / mu) ** s) * rho) / (math.factorial(s) * ((1 - rho) ** 2))
    Wq = Lq / lam
    W = Wq + (1 / mu)
    L = lam * W
    
    p_wq_0 = sum((((lam / mu) ** i) / math.factorial(i)) * p0 for i in range(s))
    p_wq_gt_t = (1 - p_wq_0) * math.exp(-s * mu * (1 - rho) * t)
    
    denom = s - 1 - (lam / mu)
    if abs(denom) < 1e-9:
        term = mu * t
    else:
        term = (1 - math.exp(-mu * t * denom)) / denom
        
    p_w_gt_t = math.exp(-mu * t) * (1 + ((p0 * ((lam / mu) ** s)) / (math.factorial(s) * (1 - rho))) * term)
    
    return {
        "Taxa de Ocupação (ρ)": rho, "Prob. Sistema Vazio (P0)": p0, 
        f"Prob. n {op_n} {n}": pn_calc,
        "Nº Médio no Sistema (L)": L, "Nº Médio na Fila (Lq)": Lq, 
        "Tempo Médio no Sist. (W)": W, "Tempo Médio na Fila (Wq)": Wq, 
        f"Prob. de W > {t}": p_w_gt_t, f"Prob. de Wq > {t}": p_wq_gt_t
    }

# --- Funções de Engenharia Reversa (M/M/1) ---
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

# --- Interface ---
st.set_page_config(page_title="Super Calculadora de Filas", layout="wide")
st.title("Super Calculadora de Teoria das Filas 📊")

tab1, tab2 = st.tabs(["🧮 Calculadora Direta", "🔍 Módulo Investigador (Descobrir λ e μ)"])

with tab1:
    st.markdown("Use esta aba quando você **já sabe** a Taxa de Chegada (λ) e a Taxa de Atendimento (μ).")
    
    col_param, col_calc = st.columns([1, 2])
    with col_param:
        modelo = st.radio("Selecione o Modelo:", ["M/M/1", "M/M/s"])
        lam = st.number_input("Taxa de Chegada (λ)", min_value=0.001, value=10.0, step=0.1, key="lam_dir")
        mu = st.number_input("Taxa de Atendimento (μ)", min_value=0.001, value=15.0, step=0.1, key="mu_dir")
        s = st.number_input("Servidores (s)", min_value=2, value=2, step=1) if modelo == "M/M/s" else 1
        
        st.markdown("---")
        st.write("**Parâmetros de Probabilidade**")
        
        c_op, c_n = st.columns([1, 1])
        with c_op:
            op_n = st.selectbox("Operador", ["=", ">", ">=", "<", "<="])
        with c_n:
            n = st.number_input("Clientes (n)", min_value=0, value=3, step=1)
            
        t = st.number_input("Valor de tempo 't' (para Probabilidades > t)", min_value=0.0, value=1.0, step=0.1)

    with col_calc:
        resultados = calc_mm1(lam, mu, t, n, op_n) if modelo == "M/M/1" else calc_mms(lam, mu, s, t, n, op_n)
        
        if "Erro" in resultados:
            st.error(resultados["Erro"])
        else:
            st.subheader("Resultados Completos")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ocupação (ρ)", f"{resultados['Taxa de Ocupação (ρ)']:.4f}")
            c2.metric("Nº no Sist. (L)", f"{resultados['Nº Médio no Sistema (L)']:.4f}")
            c3.metric("Tempo no Sist. (W)", f"{resultados['Tempo Médio no Sist. (W)']:.4f}")
            
            c4, c5, c6 = st.columns(3)
            c4.metric("Prob. Vazio (P0)", f"{resultados['Prob. Sistema Vazio (P0)']:.4f}")
            c5.metric("Nº na Fila (Lq)", f"{resultados['Nº Médio na Fila (Lq)']:.4f}")
            c6.metric("Tempo na Fila (Wq)", f"{resultados['Tempo Médio na Fila (Wq)']:.4f}")
            
            st.markdown("---")
            c7, c8, c9 = st.columns(3)
            
            # Pega o nome da chave dinamicamente baseada no operador escolhido
            chave_prob_n = list(resultados.keys())[2] 
            
            c7.metric(chave_prob_n, f"{resultados[chave_prob_n]:.4f}")
            c8.metric(list(resultados.keys())[7], f"{resultados[list(resultados.keys())[7]]:.4f}")
            c9.metric(list(resultados.keys())[8], f"{resultados[list(resultados.keys())[8]]:.4f}")

with tab2:
    st.markdown("Use esta aba para exercícios onde λ e μ **não são fornecidos diretamente**.")
    
    cenario = st.selectbox(
        "O que o exercício informa?", 
        [
            "Taxa de Ocupação (ρ) e Tempo na Fila (Wq)", 
            "Tempo no Sistema (W) e Nº na Fila (Lq)",
            "Taxa de Atendimento (μ) e Tempo na Fila (Wq)"
        ]
    )
    
    col_input, col_res = st.columns(2)
    
    with col_input:
        lam_rev, mu_rev = 0, 0
        if "Ocupação (ρ)" in cenario:
            rho_in = st.number_input("Taxa de Ocupação (ρ) Ex: 0.8", min_value=0.01, max_value=0.99, value=0.8)
            wq_in = st.number_input("Tempo na Fila (Wq)", min_value=0.01, value=0.25)
            lam_rev, mu_rev = reverse_rho_wq(rho_in, wq_in)
            
        elif "Tempo no Sistema (W)" in cenario:
            w_in = st.number_input("Tempo no Sistema (W)", min_value=0.01, value=0.5)
            lq_in = st.number_input("Nº Médio na Fila (Lq)", min_value=0.01, value=3.2)
            lam_rev, mu_rev = reverse_w_lq(w_in, lq_in)
            
        elif "Taxa de Atendimento (μ)" in cenario:
            mu_in = st.number_input("Taxa de Atendimento (μ)", min_value=0.01, value=5.0)
            wq_in2 = st.number_input("Tempo na Fila (Wq) Máximo", min_value=0.01, value=0.8)
            lam_rev, mu_rev = reverse_mu_wq(mu_in, wq_in2)

    with col_res:
        if lam_rev and mu_rev:
            st.success("✅ Parâmetros Encontrados!")
            st.metric("Taxa de Chegada Calculada (λ)", f"{lam_rev:.4f}")
            st.metric("Taxa de Atendimento Calculada (μ)", f"{mu_rev:.4f}")
            
            res_rev = calc_mm1(lam_rev, mu_rev)
            st.write(f"**L:** {res_rev['Nº Médio no Sistema (L)']:.4f} | **Lq:** {res_rev['Nº Médio na Fila (Lq)']:.4f}")
            st.write(f"**W:** {res_rev['Tempo Médio no Sist. (W)']:.4f} | **Wq:** {res_rev['Tempo Médio na Fila (Wq)']:.4f}")
        else:
            st.error("Valores inseridos não geram um sistema válido.")