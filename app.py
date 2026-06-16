import streamlit as st
import pandas as pd
from queue_solver import (
    MM1, MMs, MG1, MM1K, MM1N, PriorityNonPreemptive, PriorityPreemptive,
    reverse_rho_wq, reverse_w_lq, reverse_mu_wq
)

st.set_page_config(page_title="Hub de Teoria das Filas", layout="wide")
st.title("Hub Dinâmico de Teoria das Filas 🚀")

tab1, tab2 = st.tabs(["🧮 Calculadora Direta", "🔍 Módulo Investigador"])

with tab1:
    st.markdown("Selecione a arquitetura do sistema abaixo para calcular os cenários onde conhece λ e μ.")
    
    col_param, col_calc = st.columns([1, 2])

    with col_param:
        st.subheader("Configuração do Modelo")
        opcoes_modelos = [
            "M/M/1 (Básico)", 
            "M/M/s (Múltiplos Servidores)", 
            "M/G/1 (Tempo Genérico)", 
            "M/M/1/K (Capacidade Finita)", 
            "M/M/1/N (População Finita)",
            "Prioridades (Sem Interrupção)",
            "Prioridades (Com Interrupção)"
        ]
        modelo_selecionado = st.selectbox("Tipo de Fila", opcoes_modelos)
        
        st.markdown("---")
        mu = st.number_input("Taxa de Atendimento (μ)", min_value=0.001, value=15.0, step=0.1)
        
        lam, s, sigma2, k, pop_n, lambdas_prioridade = None, None, None, None, None, []
        
        # Se for um modelo normal, pede um único λ
        if "Prioridade" not in modelo_selecionado:
            lam = st.number_input("Taxa de Chegada Total (λ)", min_value=0.001, value=10.0, step=0.1)
        
        # Lógica de inputs específicos por modelo
        if modelo_selecionado == "M/M/s (Múltiplos Servidores)":
            s = st.number_input("Número de Servidores (s)", min_value=2, value=2, step=1)
            
        elif modelo_selecionado == "M/G/1 (Tempo Genérico)":
            sigma2 = st.number_input("Variância do Atendimento (σ²)", min_value=0.0, value=0.05, format="%.4f")
            
        elif modelo_selecionado == "M/M/1/K (Capacidade Finita)":
            k = st.number_input("Capacidade Máxima do Sistema (K)", min_value=1, value=5, step=1)
            
        elif modelo_selecionado == "M/M/1/N (População Finita)":
            pop_n = st.number_input("Tamanho da População (N)", min_value=1, value=10, step=1)
            
        elif "Prioridade" in modelo_selecionado:
            s = st.number_input("Número de Servidores (s)", min_value=1, value=1, step=1)
            num_classes = st.number_input("Número de Classes de Prioridade", min_value=2, max_value=5, value=3, step=1)
            
            st.write("**Taxas de Chegada por Classe (Ordem: 1 é a mais alta)**")
            for i in range(num_classes):
                lam_i = st.number_input(f"Taxa de Chegada Classe {i+1} (λ{i+1})", min_value=0.001, value=5.0, step=0.1)
                lambdas_prioridade.append(lam_i)

        # Campos de Probabilidade para modelos que suportam
        if "Prioridade" not in modelo_selecionado and modelo_selecionado not in ["M/G/1 (Tempo Genérico)", "M/M/1/K (Capacidade Finita)", "M/M/1/N (População Finita)"]:
            st.markdown("---")
            st.write("**Parâmetros de Probabilidade**")
            c_op, c_n = st.columns([1, 1])
            with c_op:
                op_n = st.selectbox("Operador", ["=", ">", ">=", "<", "<="])
            with c_n:
                n = st.number_input("Clientes (n)", min_value=0, value=3, step=1)
            t = st.number_input("Valor de tempo 't'", min_value=0.0, value=1.0, step=0.1)
        else:
            n, t, op_n = 0, 0.0, "="

    with col_calc:
        st.subheader("Painel de Métricas")
        
        # Roteamento e Instanciação do Motor
        solver = None
        if modelo_selecionado == "M/M/1 (Básico)":
            solver = MM1(lam, mu)
        elif modelo_selecionado == "M/M/s (Múltiplos Servidores)":
            solver = MMs(lam, mu, s)
        elif modelo_selecionado == "M/G/1 (Tempo Genérico)":
            solver = MG1(lam, mu, sigma2)
        elif modelo_selecionado == "M/M/1/K (Capacidade Finita)":
            solver = MM1K(lam, mu, k)
        elif modelo_selecionado == "M/M/1/N (População Finita)":
            solver = MM1N(lam, mu, pop_n)
        elif modelo_selecionado == "Prioridades (Sem Interrupção)":
            solver = PriorityNonPreemptive(lambdas_prioridade, mu, s)
        elif modelo_selecionado == "Prioridades (Com Interrupção)":
            solver = PriorityPreemptive(lambdas_prioridade, mu, s)
            
        resultados = solver.calcular(t=t, n=n, op_n=op_n)
        
        if "Erro" in resultados:
            st.error(resultados["Erro"])
        else:
            st.success(f"Cálculos realizados usando o motor: **{solver.__class__.__name__}**")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Taxa de Ocupação Sistémica (ρ)", f"{resultados.get('Ocupação (ρ)', 0):.4f}")
            if "P0" in resultados: c2.metric("Prob. Vazio (P0)", f"{resultados['P0']:.4f}")
            if "Pk (Prob. Rejeição)" in resultados: c3.metric("Prob. Rejeição (Pk)", f"{resultados['Pk (Prob. Rejeição)']:.4f}")
                
            st.markdown("---")
            c4, c5 = st.columns(2)
            with c4:
                st.info("📍 **Métricas Globais (Média de Todas as Classes)**")
                st.metric("Nº Médio no Sistema (L)", f"{resultados.get('L', 0):.4f}")
                st.metric("Nº Médio na Fila (Lq)", f"{resultados.get('Lq', 0):.4f}")
                
            with c5:
                st.warning("⏱️ **Tempos Globais de Espera**")
                st.metric("Tempo Médio no Sist. (W)", f"{resultados.get('W', 0):.4f}")
                st.metric("Tempo Médio na Fila (Wq)", f"{resultados.get('Wq', 0):.4f}")

            # Renderização Específica para Filas com Prioridade
            if resultados.get("is_priority"):
                st.markdown("---")
                st.success("🏆 **Métricas Específicas por Classe de Prioridade**")
                df = pd.DataFrame(resultados["classes"])
                st.dataframe(df, use_container_width=True, hide_index=True)

            # Renderização de Probabilidades Extras
            prob_n_key = [k for k in resultados.keys() if "Prob. n" in k]
            prob_w_key = [k for k in resultados.keys() if "Prob. W >" in k]
            if prob_n_key or prob_w_key:
                st.markdown("---")
                st.success("🎲 **Probabilidades Específicas**")
                cp1, cp2, cp3 = st.columns(3)
                if prob_n_key: cp1.metric(prob_n_key[0], f"{resultados[prob_n_key[0]]:.4f}")
                if prob_w_key: cp2.metric(prob_w_key[0], f"{resultados[prob_w_key[0]]:.4f}")
                prob_wq_key = [k for k in resultados.keys() if "Prob. Wq >" in k]
                if prob_wq_key: cp3.metric(prob_wq_key[0], f"{resultados[prob_wq_key[0]]:.4f}")
with tab2:
    st.markdown("Use esta aba para cenários M/M/1 onde λ e μ **não são fornecidos diretamente** (Engenharia Reversa).")
    
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
            
            res_rev = MM1(lam_rev, mu_rev).calcular()
            
            st.write(f"**L:** {res_rev['L']:.4f} | **Lq:** {res_rev['Lq']:.4f}")
            st.write(f"**W:** {res_rev['W']:.4f} | **Wq:** {res_rev['Wq']:.4f}")
        else:
            st.error("Valores inseridos não geram um sistema válido.")