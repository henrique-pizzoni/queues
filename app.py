import streamlit as st
import pandas as pd
from queue_solver import (
    MM1, MMs, MG1, MM1K, MM1N, PriorityNonPreemptive, PriorityPreemptive, PriorityMG1,
    reverse_rho_wq, reverse_w_lq, reverse_mu_wq, reverse_lq_lam_md1
)

st.set_page_config(page_title="Hub de Teoria das Filas", layout="wide")
st.title("Hub Dinâmico de Teoria das Filas 🚀")

tab1, tab2, tab3 = st.tabs(["🧮 Calculadora Direta", "🔍 Módulo Investigador", "📚 Glossário de Fórmulas"])

with tab1:
    st.markdown("Selecione a arquitetura do sistema abaixo para calcular os cenários onde conhece λ e μ.")
    
    col_param, col_calc = st.columns([1, 2])

    with col_param:
        st.subheader("Configuração do Modelo")
        opcoes_modelos = [
            "M/M/1 (Básico)", 
            "M/M/s (Múltiplos Servidores)", 
            "M/G/1 (Tempo Genérico)",
            "M/M/s/K (Capacidade Finita)",
            "M/M/s/N (População Finita)",
            "Prioridades (Sem Interrupção)",
            "Prioridades (Com Interrupção)",
            "Prioridades M/G/1 (Variâncias Distintas)"
        ]
        modelo_selecionado = st.selectbox("Tipo de Fila", opcoes_modelos)
        
        st.markdown("---")
        mu = st.number_input("Taxa de Atendimento Global (μ)", min_value=0.001, value=15.0, step=0.1)
        
        lam, s, sigma2, k, pop_n = None, None, None, None, None
        lambdas_prioridade, mus_prioridade, vars_prioridade = [], [], []
        
        # Se for um modelo normal, pede um único λ
        if "Prioridade" not in modelo_selecionado:
            lam = st.number_input("Taxa de Chegada Total (λ)", min_value=0.001, value=10.0, step=0.1)
        
        # Lógica de inputs específicos por modelo
        if modelo_selecionado == "M/M/s (Múltiplos Servidores)":
            s = st.number_input("Número de Servidores (s)", min_value=2, value=2, step=1)
            
        elif modelo_selecionado == "M/G/1 (Tempo Genérico)":
            tipo_sigma = st.radio("Tipo de entrada", ["Variância (σ²)", "Desvio Padrão (σ)"], horizontal=True)
            if tipo_sigma == "Variância (σ²)":
                sigma2 = st.number_input("Variância do Atendimento (σ²)", min_value=0.0, value=0.05, format="%.5f")
            else:
                sigma_val = st.number_input("Desvio Padrão do Atendimento (σ)", min_value=0.0, value=0.22, format="%.5f")
                sigma2 = sigma_val ** 2
            
        elif modelo_selecionado == "M/M/s/K (Capacidade Finita)":
            s = st.number_input("Número de Servidores (s)", min_value=1, value=1, step=1)
            k = st.number_input("Capacidade Máxima do Sistema (K)", min_value=s, value=max(5, s), step=1)

        elif modelo_selecionado == "M/M/s/N (População Finita)":
            s = st.number_input("Número de Servidores (s)", min_value=1, value=1, step=1)
            pop_n = st.number_input("Tamanho da População (N)", min_value=s, value=max(10, s), step=1)
            st.markdown("---")

            usar_custos = st.checkbox(
                "Calcular custos operacionais"
            )

            custo_maquina = None
            custo_servidor = None
            horas_dia = None

            if usar_custos:

                custo_maquina = st.number_input(
                    "Custo Máquina Parada (R$/h)",
                    min_value=0.0,
                    value=30.0
                )

                custo_servidor = st.number_input(
                    "Custo Servidor/Técnico (R$/h)",
                    min_value=0.0,
                    value=10.0
                )

                horas_dia = st.number_input(
                    "Horas por Dia",
                    min_value=1.0,
                    value=8.0
                )
        elif "Prioridade" in modelo_selecionado:
            if modelo_selecionado == "Prioridades M/G/1 (Variâncias Distintas)":
                st.info("Modelo de 1 Servidor onde cada classe possui seu próprio Tempo de Atendimento (μ) e Variância (σ²). O 'μ Global' digitado acima será ignorado.")
                s = 1
            else:
                s = st.number_input("Número de Servidores (s)", min_value=1, value=1, step=1)
                
            num_classes = st.number_input("Número de Classes de Prioridade", min_value=2, max_value=5, value=2, step=1)
            
            st.write("**Parâmetros por Classe (Ordem: 1 é a mais alta)**")
            for i in range(num_classes):
                c1, c2, c3 = st.columns(3)
                lam_i = c1.number_input(f"λ (Classe {i+1})", min_value=0.001, value=5.0, step=0.1, key=f"lam_pri_{i}")
                lambdas_prioridade.append(lam_i)
                
                # Exibe inputs de mu e variância individualizados SOMENTE se for o modelo M/G/1 de prioridades
                if modelo_selecionado == "Prioridades M/G/1 (Variâncias Distintas)":
                    mu_i = c2.number_input(f"μ (Classe {i+1})", min_value=0.001, value=15.0, step=0.1, key=f"mu_pri_{i}")
                    var_i = c3.number_input(f"σ² (Classe {i+1})", min_value=0.0, value=0.05, format="%.5f", key=f"var_pri_{i}")
                    mus_prioridade.append(mu_i)
                    vars_prioridade.append(var_i)

        # Campos de Probabilidade para modelos que suportam
        # K e N têm espaço de estados finito: calculam P(n ...) mas não têm
        # distribuição de tempo de espera (sem campo 't').
        modelos_sem_prob = ["M/G/1 (Tempo Genérico)"]
        modelos_so_prob_n = ["M/M/s/K (Capacidade Finita)", "M/M/s/N (População Finita)"]
        if "Prioridade" not in modelo_selecionado and modelo_selecionado not in modelos_sem_prob:
            st.markdown("---")
            st.write("**Parâmetros de Probabilidade**")
            c_op, c_n = st.columns([1, 1])
            with c_op:
                op_n = st.selectbox("Operador", ["=", ">", ">=", "<", "<="])
            with c_n:
                n = st.number_input("Clientes (n)", min_value=0, value=3, step=1)
            if modelo_selecionado in modelos_so_prob_n:
                t = 0.0
            else:
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
        elif modelo_selecionado == "M/M/s/K (Capacidade Finita)":
            solver = MM1K(lam, mu, k, s)
        elif modelo_selecionado == "M/M/s/N (População Finita)":
            solver = MM1N(lam, mu, pop_n, s)
        elif modelo_selecionado == "Prioridades (Sem Interrupção)":
            solver = PriorityNonPreemptive(lambdas_prioridade, mu, s)
        elif modelo_selecionado == "Prioridades (Com Interrupção)":
            solver = PriorityPreemptive(lambdas_prioridade, mu, s)
        elif modelo_selecionado == "Prioridades M/G/1 (Variâncias Distintas)":
            solver = PriorityMG1(lambdas_prioridade, mus_prioridade, vars_prioridade)
            
        if modelo_selecionado == "M/M/s/N (População Finita)":

            resultados = solver.calcular(
                t=t,
                n=n,
                op_n=op_n,
                custo_maquina_hora=custo_maquina,
                custo_servidor_hora=custo_servidor,
                horas_dia=horas_dia
            )

        else:

            resultados = solver.calcular(
                t=t,
                n=n,
                op_n=op_n
            )
            
        if "Erro" in resultados:
            st.error(resultados["Erro"])
        else:
            st.success(f"Cálculos realizados usando o motor: **{solver.__class__.__name__}**")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Taxa de Ocupação Sistémica (ρ)", f"{resultados.get('Ocupação (ρ)', 0):.5f}")
            if "P0" in resultados: c2.metric("Prob. Vazio (P0)", f"{resultados['P0']:.5f}")
            if "Pk (Prob. Rejeição)" in resultados: c3.metric("Prob. Rejeição (Pk)", f"{resultados['Pk (Prob. Rejeição)']:.5f}")
                
            st.markdown("---")
            c4, c5 = st.columns(2)
            with c4:
                st.info("📍 **Métricas Globais (Média de Todas as Classes)**")
                st.metric("Nº Médio no Sistema (L)", f"{resultados.get('L', 0):.5f}")
                st.metric("Nº Médio na Fila (Lq)", f"{resultados.get('Lq', 0):.5f}")
                if "Custo Hora" in resultados:

                    st.markdown("---")

                    st.success("💰 Custos Operacionais")

                    cc1, cc2 = st.columns(2)

                    cc1.metric(
                        "Custo por Hora",
                        f"R$ {resultados['Custo Hora']:.5f}"
                    )

                    if "Custo Diário" in resultados:

                        cc2.metric(
                            "Custo Diário",
                            f"R$ {resultados['Custo Diário']:.5f}"
                        )
                    
            with c5:
                st.warning("⏱️ **Tempos Globais de Espera**")
                st.metric("Tempo Médio no Sist. (W)", f"{resultados.get('W', 0):.5f}")
                st.metric("Tempo Médio na Fila (Wq)", f"{resultados.get('Wq', 0):.5f}")
                if "Máquinas Operando" in resultados:
                    st.metric(
                        "Máquinas Operando",
                        f"{resultados['Máquinas Operando']:.5f}"
                    )

                if "Utilização Servidor" in resultados:
                    st.metric(
                        "Utilização Servidor",
                        f"{resultados['Utilização Servidor']:.5f}"
                    )

            # Renderização Específica para Filas com Prioridade
            if resultados.get("is_priority"):
                if "Pn" in resultados:

                    st.markdown("---")

                    st.success("📊 Distribuição de Probabilidades")

                    df_prob = pd.DataFrame({
                        "Estado": list(range(len(resultados["Pn"]))),
                        "Probabilidade": resultados["Pn"]
                    })

                    df_prob["Probabilidade"] = df_prob["Probabilidade"].round(5)

                    st.dataframe(
                        df_prob,
                        use_container_width=True,
                        hide_index=True
                    )
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
                if prob_n_key: cp1.metric(prob_n_key[0], f"{resultados[prob_n_key[0]]:.5f}")
                if prob_w_key: cp2.metric(prob_w_key[0], f"{resultados[prob_w_key[0]]:.5f}")
                prob_wq_key = [k for k in resultados.keys() if "Prob. Wq >" in k]
                if prob_wq_key: cp3.metric(prob_wq_key[0], f"{resultados[prob_wq_key[0]]:.5f}")

with tab2:
    st.markdown("Use esta aba para cenários M/M/1 onde λ e μ **não são fornecidos diretamente** (Engenharia Reversa).")
    
    cenario = st.selectbox(
        "O que o exercício informa?",
        [
            "Taxa de Ocupação (ρ) e Tempo na Fila (Wq)",
            "Tempo no Sistema (W) e Nº na Fila (Lq)",
            "Taxa de Atendimento (μ) e Tempo na Fila (Wq)",
            "Lq medido e λ conhecido (M/D/1 — serviço determinístico)"
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

        elif "Lq medido" in cenario:
            st.info("Assume serviço determinístico (σ=0, M/D/1). Dado Lq medido e λ, resolve para μ e demais métricas.")
            lq_md1 = st.number_input("Nº Médio na Fila Medido (Lq)", min_value=0.01, value=2.0)
            lam_md1 = st.number_input("Taxa de Chegada (λ)", min_value=0.01, value=3.0)
            lam_rev, mu_rev = reverse_lq_lam_md1(lq_md1, lam_md1)

    with col_res:
        if lam_rev and mu_rev:
            st.success("✅ Parâmetros Encontrados!")
            st.metric("Taxa de Chegada Calculada (λ)", f"{lam_rev:.5f}")
            st.metric("Taxa de Atendimento Calculada (μ)", f"{mu_rev:.5f}")

            if "Lq medido" in cenario:
                res_rev = MG1(lam_rev, mu_rev, 0.0).calcular()
            else:
                res_rev = MM1(lam_rev, mu_rev).calcular()

            st.write(f"**L:** {res_rev['L']:.5f} | **Lq:** {res_rev['Lq']:.5f}")
            st.write(f"**W:** {res_rev['W']:.5f} | **Wq:** {res_rev['Wq']:.5f}")
        else:
            st.error("Valores inseridos não geram um sistema válido.")

with tab3:
    st.markdown("Referência rápida das principais fórmulas de teoria das filas.")

    # --- Guia de Escolha do Modelo ---
    with st.expander("🧭 Qual modelo usar? — Guia de decisão + frases do enunciado", expanded=True):
        st.markdown("### Passo a passo de identificação")
        st.markdown("""
**1. As chegadas são aleatórias / seguem Poisson?**
> Sim (ou *"taxa média de X clientes/hora"*, *"chegadas aleatórias"*) → todos os modelos M/* se aplicam.

**2. O enunciado menciona população limitada ou capacidade do sistema?**
""")
        col_k, col_n = st.columns(2)
        with col_k:
            st.info("**→ M/M/s/K (capacidade finita)**\n\nFrases-chave no enunciado:")
            st.markdown("""
- *"o sistema suporta no máximo **K** clientes"*
- *"a sala de espera comporta **K − s** pessoas"*
- *"clientes que chegam quando o sistema está cheio **partem**"*
- *"buffer com capacidade K"*
- *"estacionamento com K vagas"*
- *"qual a probabilidade de um cliente ser **rejeitado**?"*
""")
        with col_n:
            st.warning("**→ M/M/s/N (população finita)**\n\nFrases-chave no enunciado:")
            st.markdown("""
- *"uma fábrica com **N máquinas** e s técnicos de reparo"*
- *"apenas **N terminais** compartilham o servidor"*
- *"população **fechada** de N clientes"*
- *"quando uma máquina quebra, chama o técnico"*
- *"a taxa de chegada depende de quantas máquinas estão em operação"*
""")

        st.markdown("**3. Quantos servidores e qual a distribuição do atendimento?**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("**→ M/M/1**\n\n1 servidor, atendimento exponencial")
            st.markdown("""
Frases-chave:
- *"um único atendente/caixa/servidor"*
- *"tempo de atendimento **exponencial** com média 1/μ"*
- *"tempo de atendimento **aleatório**"* (sem dar σ)
- *"distribuição de Poisson"* para chegadas e serviço
- Exercício dá só **λ e μ**, sem variância
""")
        with col2:
            st.success("**→ M/M/s**\n\ns servidores, atendimento exponencial")
            st.markdown("""
Frases-chave:
- *"**dois/três/s** atendentes em paralelo"*
- *"**s** caixas disponíveis"*
- *"cada servidor atende a taxa μ"*
- *"queremos saber **quantos servidores** são necessários"*
- *"clientes escolhem o servidor livre"*
""")
        with col3:
            st.warning("**→ M/G/1**\n\n1 servidor, atendimento genérico")
            st.markdown("""
Frases-chave:
- *"tempo de atendimento com **média** E[S] e **desvio padrão σ**"*
- *"**variância** do atendimento é σ²"*
- *"o atendimento leva **exatamente** X minutos"* → M/D/1 (σ=0)
- *"distribuição **Normal / Erlang / Uniforme**"* no atendimento
- *"o tempo É fixo"* (determinístico)
""")

        st.markdown("**4. Há classes de clientes com prioridade?**")
        col4, col5 = st.columns(2)
        with col4:
            st.error("**→ Prioridade Sem Interrupção**")
            st.markdown("""
Frases-chave:
- *"clientes preferenciais passam à frente, **mas o atendimento atual não é interrompido**"*
- *"1ª classe / 2ª classe sem interromper serviço"*
- *"o servidor termina o cliente atual antes de atender a prioridade"*
- *"fila preferencial em banco/caixa"*
- *"urgências entram na frente mas aguardam o fim do atendimento em curso"*
""")
        with col5:
            st.error("**→ Prioridade Com Interrupção**")
            st.markdown("""
Frases-chave:
- *"chegada de alta prioridade **interrompe** o atendimento em curso"*
- *"atendimento pode ser **preemptado**"*
- *"o cliente interrompido retorna para o início da fila"*
- *"sistema de UTI / emergência"*
- *"escalonamento preemptivo (SO, redes com QoS)"*
- *"o cliente de baixa prioridade **perde o lugar** no servidor"*
""")

        st.markdown("---")
        st.markdown("### Tabela-resumo rápida")
        st.dataframe(pd.DataFrame({
            "Modelo": ["M/M/1", "M/M/s", "M/G/1", "M/D/1", "M/M/s/K", "M/M/s/N", "Prio. Sem Int.", "Prio. Com Int."],
            "O enunciado diz…": [
                "1 servidor, tempo exponencial ou 'aleatório', só λ e μ",
                "s servidores paralelos, tempo exponencial",
                "1 servidor + σ ou σ² fornecidos (distribuição genérica)",
                "1 servidor, tempo FIXO / determinístico (σ=0)",
                "Capacidade máxima K; clientes rejeitados se cheio",
                "N clientes no total; máquinas / terminais / população fechada",
                "Classes de prioridade; atendimento atual NÃO é interrompido",
                "Classes de prioridade; atendimento atual É interrompido",
            ],
            "Parâmetros mínimos": [
                "λ, μ", "λ, μ, s", "λ, μ, σ²", "λ, μ (σ=0)",
                "λ, μ, s, K", "λ, μ, s, N",
                "λ₁…λₖ, μ, s", "λ₁…λₖ, μ, s",
            ],
        }), use_container_width=True, hide_index=True)

    # --- M/M/1 vs M/G/1 ---
    with st.expander("⚖️ M/M/1 vs M/G/1 — Qual a diferença?"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### M/M/1")
            st.markdown("""
- Atendimento **exponencial**: σ² = 1/μ²
- Só precisa de **λ e μ**
- Caso mais simples e mais comum em exercícios
- A fórmula P-K com σ²=1/μ² **reduz exatamente** à fórmula M/M/1:
""")
            st.latex(r"L_q^{MM1} = \frac{\rho^2}{1 - \rho}")
            st.markdown("**Sinais no enunciado:**")
            st.markdown("""
- *"distribuição **exponencial**"*
- *"tempo de serviço **aleatório**"* sem dar σ
- Enunciado fornece apenas λ e μ
""")
        with col2:
            st.markdown("### M/G/1")
            st.markdown("""
- Atendimento com **qualquer distribuição**: precisa de σ² também
- Caso geral — M/M/1 é um caso especial dele
- Quanto **maior σ**, maior a fila (variabilidade prejudica)
- Com σ = 0 (M/D/1), fila é **metade** da M/M/1:
""")
            st.latex(r"L_q^{MD1} = \frac{\rho^2}{2(1 - \rho)} = \frac{1}{2}\,L_q^{MM1}")
            st.markdown("**Sinais no enunciado:**")
            st.markdown("""
- *"variância σ² = X"* ou *"desvio padrão σ = X"*
- *"tempo de atendimento **É** X minutos"* → M/D/1 (σ=0)
- Distribuição Normal, Erlang, Uniforme no serviço
""")

        st.markdown("**Resumo visual — mesmo ρ = 0,8, λ = 4, μ = 5:**")
        rho = 0.8
        lq_mm1 = rho**2 / (1 - rho)
        lq_md1 = rho**2 / (2 * (1 - rho))
        lq_mg1_ex = (16 * 0.1 + rho**2) / (2 * (1 - rho))  # σ²=0.1
        st.dataframe(pd.DataFrame({
            "Modelo": ["M/M/1 (σ²=1/μ²=0,04)", "M/G/1 (σ²=0,10)", "M/D/1 (σ²=0)"],
            "Lq": [f"{lq_mm1:.3f}", f"{lq_mg1_ex:.3f}", f"{lq_md1:.3f}"],
            "Conclusão": ["referência", "pior que M/M/1 (mais variância)", "melhor possível (sem variância)"]
        }), use_container_width=True, hide_index=True)

    # --- M/M/1 vs M/M/s ---
    with st.expander("⚖️ M/M/1 vs M/M/s — Quando adicionar servidores?"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### M/M/1")
            st.markdown("""
- Sistema instável se λ ≥ μ
- Com ρ alto, a fila cresce muito
- **Sinais no enunciado:**
  - *"um único atendente"*
  - *"um caixa"*, *"um servidor"*
  - *"há apenas 1 técnico disponível"*
""")
            st.latex(r"\rho = \frac{\lambda}{\mu} \quad (\rho < 1)")
        with col2:
            st.markdown("### M/M/s")
            st.markdown("""
- Divide a carga — cada servidor opera com ρ = λ/(s·μ)
- Primeiros servidores extras têm impacto não-linear na fila
- **Sinais no enunciado:**
  - *"**dois/três/s** atendentes paralelos"*
  - *"**s** caixas abertas"*
  - *"**múltiplos** servidores idênticos"*
  - *"quantos servidores são necessários para Wq < X?"*
""")
            st.latex(r"\rho = \frac{\lambda}{s \cdot \mu} \quad (\rho < 1)")
        st.info("Cuidado: no M/M/s, ρ < 1 exige λ < s·μ, não apenas λ < μ.")

    # --- Finita vs Infinita ---
    with st.expander("⚖️ M/M/s vs M/M/s/K vs M/M/s/N — capacidade e população"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**M/M/s** (padrão)")
            st.markdown("""
- Fila infinita, população infinita
- Clientes nunca são rejeitados
- **Sinais:** nenhuma restrição de espaço ou população mencionada
""")
        with col2:
            st.markdown("**M/M/s/K** (capacidade finita)")
            st.markdown("""
- Sistema comporta no máximo **K** clientes
- Excedente é **rejeitado / perdido**
- **Sinais no enunciado:**
  - *"sala de espera com capacidade para X pessoas"*
  - *"buffer de K posições"*
  - *"prob. de rejeição / perda?"*
  - *"clientes que chegam e não cabem **vão embora**"*
""")
            st.latex(r"\bar{\lambda} = \lambda(1 - P_K)")
        with col3:
            st.markdown("**M/M/s/N** (população finita)")
            st.markdown("""
- Só existem **N** clientes potenciais
- Taxa efetiva cai conforme mais máquinas estão no sistema
- **Sinais no enunciado:**
  - *"N máquinas, s técnicos de manutenção"*
  - *"N terminais de computador"*
  - *"população fechada de N usuários"*
  - *"quando a máquina quebra, aguarda o técnico"*
""")
            st.latex(r"\bar{\lambda} = \lambda(N - L)")

    # --- Prioridade Sem vs Com Interrupção ---
    with st.expander("⚖️ Prioridade Sem Interrupção vs Com Interrupção"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Sem Interrupção (Non-Preemptive)**")
            st.markdown("""
- Cliente de alta prioridade entra na frente da fila, mas **espera** o atendimento atual terminar
- Mais realista para a maioria dos casos
- **Sinais no enunciado:**
  - *"sem interromper o serviço em andamento"*
  - *"cliente preferencial aguarda o atual ser atendido"*
  - *"fila preferencial de banco, check-in aéreo"*
  - *"não há preempção"*
""")
        with col2:
            st.markdown("**Com Interrupção (Preemptive)**")
            st.markdown("""
- Cliente de alta prioridade **interrompe** o atendimento em curso
- Cliente interrompido volta para o início da fila
- **Sinais no enunciado:**
  - *"chegada de emergência **interrompe** o atendimento atual"*
  - *"atendimento pode ser **preemptado**"*
  - *"sistema de UTI, triagem hospitalar"*
  - *"escalonamento **preemptivo** (SO, redes QoS)"*
  - *"cliente perde o servidor ao chegar um de prioridade maior"*
""")
        st.warning("Para mesmos parâmetros: W₁(com interrupção) < W₁(sem interrupção) < W₁(FCFS), mas W₃(com interrupção) > W₃(sem interrupção).")

    # --- Lei de Little ---
    with st.expander("📐 Lei de Little — vale para QUALQUER modelo", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**No sistema**")
            st.latex(r"L = \lambda \cdot W")
            st.markdown("**Na fila**")
            st.latex(r"L_q = \lambda \cdot W_q")
        with col2:
            st.markdown("**Relação sistema ↔ fila**")
            st.latex(r"W = W_q + \frac{1}{\mu}")
            st.latex(r"L = L_q + \rho \quad \text{(s=1)}")

    # --- Notação ---
    with st.expander("🔤 Notação"):
        st.markdown("""
| Símbolo | Significado |
|---------|-------------|
| λ | Taxa de chegada (clientes/tempo) |
| μ | Taxa de atendimento por servidor |
| s | Número de servidores |
| ρ | Taxa de ocupação (utilização) |
| σ² | Variância do tempo de atendimento |
| L | Nº médio de clientes **no sistema** |
| Lq | Nº médio de clientes **na fila** |
| W | Tempo médio **no sistema** |
| Wq | Tempo médio **na fila** |
| P0 | Probabilidade do sistema estar vazio |
| Pn | Probabilidade de haver n clientes |
""")

    # --- M/M/1 ---
    with st.expander("M/M/1 — 1 servidor, chegadas Poisson, atendimento exponencial"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Ocupação**")
            st.latex(r"\rho = \frac{\lambda}{\mu} \quad (\rho < 1)")
            st.markdown("**Probabilidades**")
            st.latex(r"P_0 = 1 - \rho")
            st.latex(r"P_n = (1 - \rho)\,\rho^n")
        with col2:
            st.markdown("**Métricas**")
            st.latex(r"L = \frac{\lambda}{\mu - \lambda}")
            st.latex(r"L_q = \frac{\lambda^2}{\mu(\mu - \lambda)} = \frac{\rho^2}{1 - \rho}")
            st.latex(r"W = \frac{1}{\mu - \lambda}")
            st.latex(r"W_q = \frac{\lambda}{\mu(\mu - \lambda)}")

    # --- M/M/s ---
    with st.expander("M/M/s — s servidores, chegadas Poisson, atendimento exponencial"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Ocupação por servidor**")
            st.latex(r"\rho = \frac{\lambda}{s \cdot \mu} \quad (\rho < 1)")
            st.markdown("**Probabilidade sistema vazio**")
            st.latex(r"P_0 = \left[\sum_{k=0}^{s-1} \frac{(\lambda/\mu)^k}{k!} + \frac{(\lambda/\mu)^s}{s!} \cdot \frac{1}{1-\rho}\right]^{-1}")
        with col2:
            st.markdown("**Métricas**")
            st.latex(r"L_q = \frac{P_0 \cdot (\lambda/\mu)^s \cdot \rho}{s!\,(1-\rho)^2}")
            st.latex(r"W_q = \frac{L_q}{\lambda}")
            st.latex(r"W = W_q + \frac{1}{\mu}")
            st.latex(r"L = \lambda \cdot W")

    # --- M/G/1 ---
    with st.expander("M/G/1 — 1 servidor, chegadas Poisson, atendimento genérico (Pollaczek-Khinchine)"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fórmula P-K**")
            st.latex(r"L_q = \frac{\lambda^2 \sigma^2 + \rho^2}{2(1 - \rho)}")
            st.markdown("**Casos especiais**")
            st.latex(r"\sigma^2 = \frac{1}{\mu^2} \Rightarrow \text{M/M/1:} \quad L_q = \frac{\rho^2}{1-\rho}")
            st.latex(r"\sigma = 0 \Rightarrow \text{M/D/1:} \quad L_q = \frac{\rho^2}{2(1-\rho)}")
        with col2:
            st.markdown("**Demais métricas**")
            st.latex(r"\rho = \frac{\lambda}{\mu}")
            st.latex(r"W_q = \frac{L_q}{\lambda}")
            st.latex(r"W = W_q + \frac{1}{\mu}")
            st.latex(r"L = \rho + L_q")
            st.info("M/D/1 tem exatamente **metade** do Lq do M/M/1 para o mesmo ρ.")

    # --- M/D/1 Inverso ---
    with st.expander("M/D/1 Inverso — dado Lq medido e λ, encontrar μ"):
        st.markdown("Quando o exercício fornece **Lq medido** e **λ**, assumindo serviço determinístico (σ=0):")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Resolver para ρ**")
            st.latex(r"L_q = \frac{\rho^2}{2(1-\rho)}")
            st.latex(r"\rho^2 + 2L_q\,\rho - 2L_q = 0")
            st.latex(r"\rho = -L_q + \sqrt{L_q^2 + 2L_q}")
        with col2:
            st.markdown("**Obter μ e métricas**")
            st.latex(r"\mu = \frac{\lambda}{\rho}")
            st.latex(r"W_q = \frac{L_q}{\lambda}")
            st.latex(r"W = W_q + \frac{1}{\mu}")
            st.latex(r"L = \lambda \cdot W")

    # --- M/M/s/K ---
    with st.expander("M/M/s/K — capacidade máxima K no sistema"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Pesos de estado**")
            st.latex(r"w_i = \begin{cases} \dfrac{a^i}{i!} & i \leq s \\[8pt] \dfrac{a^i}{s!\, s^{i-s}} & i > s \end{cases} \quad a = \frac{\lambda}{\mu}")
            st.latex(r"P_i = \frac{w_i}{\sum_{j=0}^{K} w_j}")
        with col2:
            st.markdown("**Taxa efetiva e métricas**")
            st.latex(r"P_K = \text{prob. de rejeição}")
            st.latex(r"\bar{\lambda} = \lambda(1 - P_K)")
            st.latex(r"W = \frac{L}{\bar{\lambda}}, \quad W_q = \frac{L_q}{\bar{\lambda}}")

    # --- M/M/s/N ---
    with st.expander("M/M/s/N — população finita de N clientes"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Pesos de estado**")
            st.latex(r"w_i = \begin{cases} \dbinom{N}{i} a^i & i \leq s \\[8pt] \dfrac{N!}{(N-i)!\,s!\,s^{i-s}}\,a^i & i > s \end{cases}")
        with col2:
            st.markdown("**Taxa efetiva e métricas**")
            st.latex(r"\bar{\lambda} = \lambda(N - L)")
            st.latex(r"W = \frac{L}{\bar{\lambda}}, \quad W_q = \frac{L_q}{\bar{\lambda}}")

    # --- Prioridades Sem Interrupção ---
    with st.expander("Prioridades sem Interrupção (Non-Preemptive)"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fator auxiliar (s servidores)**")
            st.latex(r"\text{term}_1 = \frac{s!\,(s\mu - \Lambda)}{(\Lambda/\mu)^s} \sum_{j=0}^{s-1}\frac{(\Lambda/\mu)^j}{j!} + s\mu")
            st.latex(r"A_k = \sum_{i=1}^{k} \lambda_i \quad (A_0 = 0)")
        with col2:
            st.markdown("**Para cada classe k**")
            st.latex(r"W_{q_k} = \frac{1}{\text{term}_1 \left(1 - \frac{A_{k-1}}{s\mu}\right)\left(1 - \frac{A_k}{s\mu}\right)}")
            st.latex(r"W_k = W_{q_k} + \frac{1}{\mu}")
            st.latex(r"L_k = \lambda_k W_k, \quad L_{q_k} = \lambda_k W_{q_k}")

    # --- Prioridades Com Interrupção ---
    with st.expander("Prioridades com Interrupção (Preemptive)"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Sistema agregado até classe k**")
            st.latex(r"\Lambda_k = \sum_{i=1}^{k} \lambda_i")
            st.latex(r"W(\Lambda_k) = \text{tempo médio M/M/s com } \lambda = \Lambda_k")
        with col2:
            st.markdown("**Tempo para classe k**")
            st.latex(r"W_k = \frac{W(\Lambda_k)\,\Lambda_k - \sum_{i=1}^{k-1}\lambda_i W_i}{\lambda_k}")
            st.latex(r"W_{q_k} = W_k - \frac{1}{\mu}")

    # --- Engenharia Reversa ---
    with st.expander("🔁 Engenharia Reversa (Módulo Investigador) — M/M/1"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Dado ρ e Wq**")
            st.latex(r"\mu = \frac{\rho}{W_q(1-\rho)}")
            st.latex(r"\lambda = \rho \cdot \mu")
        with col2:
            st.markdown("**Dado W e Lq**")
            st.latex(r"\lambda^2 W^2 - L_q\lambda W - L_q = 0")
            st.latex(r"\mu = \lambda + \frac{1}{W}")
        with col3:
            st.markdown("**Dado μ e Wq**")
            st.latex(r"\lambda = \frac{W_q \mu^2}{1 + W_q \mu}")