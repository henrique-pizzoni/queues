# -*- coding: utf-8 -*-
"""
Testes unitários para queue_solver.py

Os casos de teste são baseados nas listas de exercícios (com gabarito) das pastas:
  - "Lista de exercícios Modelo MMs.pdf"
  - "Lista de exercícios Modelo MG1 e com prioridades.pdf"
  - "Lista de exercícios Modelo MMsk.pdf"
  - "Lista de exercícios Modelo MMsN.pdf"

Cada teste referencia, no docstring, a lista e o número do exercício de onde
saíram os parâmetros e o gabarito.

Para executar:
    python -m unittest test_queue_solver.py -v
"""

import unittest

from queue_solver import (
    MM1, MMs, MG1, MM1K, MM1N,
    PriorityNonPreemptive, PriorityPreemptive,
    reverse_rho_wq, reverse_w_lq, reverse_mu_wq,
    prob_mm1, prob_mms_exata, prob_mms_acumulada, mms_metrics,
)


# ----------------------------------------------------------------------------
# M/M/1 (fila única, servidor único)
# ----------------------------------------------------------------------------
class TestMM1(unittest.TestCase):
    def test_caminhoes_descarga(self):
        """Lista M/M/s, ex. 5: λ=3/h, μ=4/h (atend. 15 min)."""
        r = MM1(lam=3, mu=4).calcular(t=2, n=6, op_n="=")
        self.assertAlmostEqual(r["Ocupação (ρ)"], 0.75, places=4)
        self.assertAlmostEqual(r["Lq"], 2.25, places=4)
        self.assertAlmostEqual(r["L"], 3.0, places=4)
        self.assertAlmostEqual(r["Wq"], 0.75, places=4)
        self.assertAlmostEqual(r["W"], 1.0, places=4)
        # P(6 no sistema) = 0,0445
        self.assertAlmostEqual(r["Prob. n = 6"], 0.0445, places=4)
        # P(W > 2 h) = 0,1353
        self.assertAlmostEqual(r["Prob. W > 2"], 0.1353, places=4)
        # P(Wq > 2 h) ... a lista pede P(Wq>1,5h)=0,1673; testado abaixo.

    def test_caminhoes_wq_gt(self):
        """Lista M/M/s, ex. 5h: P(Wq > 1,5 h) = 0,1673."""
        r = MM1(lam=3, mu=4).calcular(t=1.5)
        self.assertAlmostEqual(r["Prob. Wq > 1.5"], 0.1673, places=4)

    def test_cooperativa_agricola(self):
        """Lista M/M/s, ex. 6: μ=5/h, λ=4/h (Wq alvo de 0,8 h)."""
        r = MM1(lam=4, mu=5).calcular(t=1)
        self.assertAlmostEqual(r["Ocupação (ρ)"], 0.8, places=4)
        self.assertAlmostEqual(r["Lq"], 3.2, places=4)
        self.assertAlmostEqual(r["L"], 4.0, places=4)
        self.assertAlmostEqual(r["W"], 1.0, places=4)
        self.assertAlmostEqual(r["Wq"], 0.8, places=4)
        # P(W > 1 h) = 0,3679
        self.assertAlmostEqual(r["Prob. W > 1"], 0.3679, places=4)

    def test_cooperativa_wq(self):
        """Lista M/M/s, ex. 6f: P(Wq > 0,8 h) = 0,3595."""
        r = MM1(lam=4, mu=5).calcular(t=0.8)
        self.assertAlmostEqual(r["Prob. Wq > 0.8"], 0.3595, places=4)

    def test_hospital_um_medico(self):
        """Lista M/M/s, ex. 7 (s=1): λ=2/h, μ=3/h (atend. 20 min)."""
        r = MM1(lam=2, mu=3).calcular(t=1, n=2, op_n=">")
        self.assertAlmostEqual(r["Ocupação (ρ)"], 2 / 3, places=4)
        self.assertAlmostEqual(r["P0"], 1 / 3, places=4)
        self.assertAlmostEqual(r["L"], 2.0, places=4)
        self.assertAlmostEqual(r["Lq"], 4 / 3, places=4)
        self.assertAlmostEqual(r["W"], 1.0, places=4)
        self.assertAlmostEqual(r["Wq"], 2 / 3, places=4)
        # P(mais de 2 no sistema) = 0,2962 (gabarito truncado em 4 casas)
        self.assertAlmostEqual(r["Prob. n > 2"], 0.2962, places=3)
        # P(W > 1 h) = 0,3679
        self.assertAlmostEqual(r["Prob. W > 1"], 0.3679, places=4)

    def test_hospital_um_medico_wq(self):
        """Lista M/M/s, ex. 7h (s=1): P(Wq > 1/2 h) = 0,404."""
        r = MM1(lam=2, mu=3).calcular(t=0.5)
        self.assertAlmostEqual(r["Prob. Wq > 0.5"], 0.404, places=3)

    def test_aeroporto_uma_pista(self):
        """Lista M/M/s, ex. 14a: λ=10/h, μ=20/h (atend. 3 min)."""
        r = MM1(lam=10, mu=20).calcular(t=0.5, n=5, op_n="<=")
        self.assertAlmostEqual(r["Lq"], 0.5, places=4)
        # Critério 2: P(nº na fila <= 4) = P(n <= 5) = 0,984
        self.assertAlmostEqual(r["Prob. n <= 5"], 0.984375, places=4)
        # Critério 3: P(Wq > 0,5 h) pequeno -> P(Wq <= 0,5) = 0,9966
        self.assertAlmostEqual(1 - r["Prob. Wq > 0.5"], 0.9966, places=4)

    def test_aeroporto_aumento_demanda(self):
        """Lista M/M/s, ex. 14b: λ=15/h, μ=20/h."""
        r = MM1(lam=15, mu=20).calcular(t=0.5, n=5, op_n="<=")
        self.assertAlmostEqual(r["Lq"], 2.25, places=4)
        self.assertAlmostEqual(r["Prob. n <= 5"], 0.822021, places=4)
        self.assertAlmostEqual(1 - r["Prob. Wq > 0.5"], 0.9384, places=4)

    def test_sistema_instavel(self):
        """λ >= μ deve retornar erro de instabilidade."""
        r = MM1(lam=5, mu=4).calcular()
        self.assertIn("Erro", r)


# ----------------------------------------------------------------------------
# M/M/s (fila única, múltiplos servidores)
# ----------------------------------------------------------------------------
class TestMMs(unittest.TestCase):
    def test_hospital_dois_medicos(self):
        """Lista M/M/s, ex. 7 (s=2): λ=2/h, μ=3/h, s=2."""
        r = MMs(lam=2, mu=3, s=2).calcular(t=1, n=2, op_n=">")
        self.assertAlmostEqual(r["Ocupação (ρ)"], 1 / 3, places=4)
        self.assertAlmostEqual(r["P0"], 0.5, places=4)
        self.assertAlmostEqual(r["L"], 0.75, places=4)
        self.assertAlmostEqual(r["Lq"], 1 / 12, places=4)
        self.assertAlmostEqual(r["Wq"], 1 / 24, places=4)
        self.assertAlmostEqual(r["W"], 3 / 8, places=4)
        # P(mais de 2 no sistema) = 0,0556
        self.assertAlmostEqual(r["Prob. n > 2"], 0.0556, places=4)
        # P(W > 1 h) = 0,0655
        self.assertAlmostEqual(r["Prob. W > 1"], 0.0655, places=4)

    def test_hospital_dois_medicos_wq(self):
        """Lista M/M/s, ex. 7h (s=2): P(Wq > 1/2 h) = 0,023."""
        r = MMs(lam=2, mu=3, s=2).calcular(t=0.5)
        self.assertAlmostEqual(r["Prob. Wq > 0.5"], 0.023, places=3)

    def test_banco_quatro_caixas_hoje(self):
        """Lista M/M/s, ex. 15a: λ=2/min, μ=1/min, s=4 -> Lq=0,1739."""
        r = MMs(lam=2, mu=1, s=4).calcular()
        self.assertAlmostEqual(r["Lq"], 0.1739, places=4)

    def test_banco_quatro_caixas_futuro(self):
        """Lista M/M/s, ex. 15b: λ=3/min, μ=1/min, s=4 -> Lq=1,5283."""
        r = MMs(lam=3, mu=1, s=4).calcular()
        self.assertAlmostEqual(r["Lq"], 1.5283, places=4)

    def test_aeroporto_segunda_pista(self):
        """Lista M/M/s, ex. 14c: λ=25/h, μ=20/h, s=2 -> Lq=0,8013."""
        r = MMs(lam=25, mu=20, s=2).calcular()
        self.assertAlmostEqual(r["Lq"], 0.8013, places=4)

    def test_sac_dois_atendentes_reduz_espera(self):
        """Lista M/M/s, ex. 9: λ=5/h, μ=7/h. Com s=2, Wq < 2 min (1/30 h)."""
        r = MMs(lam=5, mu=7, s=2).calcular()
        self.assertLess(r["Wq"], 2 / 60)

    def test_sistema_instavel(self):
        """λ >= s*μ deve retornar erro de instabilidade."""
        r = MMs(lam=10, mu=2, s=2).calcular()
        self.assertIn("Erro", r)


# ----------------------------------------------------------------------------
# M/G/1 (tempo de atendimento genérico)
# ----------------------------------------------------------------------------
class TestMG1(unittest.TestCase):
    def test_variacao_de_sigma(self):
        """Lista M/G/1, ex. 1: λ=0,2, μ=0,25, vários σ (passa σ²)."""
        casos = {
            # sigma : (Lq, L, Wq, W)
            4: (3.2, 4.0, 16.0, 20.0),
            3: (2.5, 3.3, 12.5, 16.5),
            2: (2.0, 2.8, 10.0, 14.0),
            1: (1.7, 2.5, 8.5, 12.5),
            0: (1.6, 2.4, 8.0, 12.0),
        }
        for sigma, (lq, l, wq, w) in casos.items():
            r = MG1(lam=0.2, mu=0.25, sigma2=sigma ** 2).calcular()
            self.assertAlmostEqual(r["Lq"], lq, places=3, msg=f"σ={sigma} Lq")
            self.assertAlmostEqual(r["L"], l, places=3, msg=f"σ={sigma} L")
            self.assertAlmostEqual(r["Wq"], wq, places=3, msg=f"σ={sigma} Wq")
            self.assertAlmostEqual(r["W"], w, places=3, msg=f"σ={sigma} W")

    def test_atendimento_deterministico(self):
        """Lista M/G/1, ex. 2: λ=3/h, μ=4/h, atend. determinístico (σ²=0)."""
        r = MG1(lam=3, mu=4, sigma2=0).calcular()
        self.assertAlmostEqual(r["Lq"], 1.125, places=4)
        self.assertAlmostEqual(r["L"], 1.875, places=4)
        self.assertAlmostEqual(r["Wq"], 0.375, places=4)
        self.assertAlmostEqual(r["W"], 0.625, places=4)
        self.assertAlmostEqual(r["Ocupação (ρ)"], 0.75, places=4)

    def test_sistema_instavel(self):
        r = MG1(lam=5, mu=4, sigma2=1).calcular()
        self.assertIn("Erro", r)


# ----------------------------------------------------------------------------
# M/M/1/K (capacidade finita)
# ----------------------------------------------------------------------------
class TestMM1K(unittest.TestCase):
    def test_agencia_bancaria_k5(self):
        """Lista M/M/sk, ex. 1: λ=2/min, μ=4/min (atend. 0,25 min), K=5."""
        r = MM1K(lam=2, mu=4, k=5).calcular()
        self.assertAlmostEqual(r["P0"], 0.5079, places=4)
        self.assertAlmostEqual(r["L"], 0.9048, places=4)
        self.assertAlmostEqual(r["Lq"], 0.4127, places=4)
        self.assertAlmostEqual(r["W"], 0.4597, places=4)
        self.assertAlmostEqual(r["Wq"], 0.2097, places=4)

    def test_laboratorio_radiologia_k4(self):
        """Lista M/M/sk, ex. 2: λ=1/h, μ=4/3/h (atend. 45 min), K=4."""
        r = MM1K(lam=1, mu=4 / 3, k=4).calcular()
        self.assertAlmostEqual(r["L"], 1.4443, places=4)
        # P(lab cheio) = Pk = 0,1037
        self.assertAlmostEqual(r["Pk (Prob. Rejeição)"], 0.1037, places=4)
        self.assertAlmostEqual(r["Wq"], 0.8614, places=4)

    def test_aeroporto_pista_unica_k4(self):
        """Lista M/M/sk, ex. 3: λ=0,25/min, μ=1/3/min (atend. 3 min), K=4."""
        r = MM1K(lam=0.25, mu=1 / 3, k=4).calcular()
        self.assertAlmostEqual(r["Lq"], 0.7721, places=4)
        self.assertAlmostEqual(r["Wq"], 3.4457, places=4)
        # P(> 2 na fila) = P(sistema cheio) = Pk = 0,1037
        self.assertAlmostEqual(r["Pk (Prob. Rejeição)"], 0.1037, places=4)

    def test_prob_n_no_sistema(self):
        """Lista M/M/sk, ex. 1d: λ=2/min, μ=4/min, K=5 -> P(n=4)=0,03175.
        Slide M/M/1/K, ex. 2d: λ=3/min, μ=4/min, K=5 -> P(n=4)=0,09623."""
        r = MM1K(lam=2, mu=4, k=5).calcular(n=4, op_n="=")
        self.assertAlmostEqual(r["Prob. n = 4"], 0.03175, places=5)
        r = MM1K(lam=3, mu=4, k=5).calcular(n=4, op_n="=")
        self.assertAlmostEqual(r["Prob. n = 4"], 0.09623, places=5)

    def test_prob_acima_da_capacidade_e_zero(self):
        """Num sistema de capacidade K, P(n > K) = 0 e P(n <= K) = 1."""
        r = MM1K(lam=3, mu=4, k=5).calcular(n=5, op_n=">")
        self.assertAlmostEqual(r["Prob. n > 5"], 0.0, places=10)
        r = MM1K(lam=3, mu=4, k=5).calcular(n=5, op_n="<=")
        self.assertAlmostEqual(r["Prob. n <= 5"], 1.0, places=10)

    # ------------------------------------------------------------------
    # Casos particulares com s > 1 (multi-servidor). ATENÇÃO: a capacidade
    # total K do sistema é mantida ao adicionar servidores (vide slide, que
    # pede "P5 para 1 e 2 atendentes"). Logo o aeroporto/lab com s=2 usa o
    # MESMO K=4 da versão de 1 servidor, e não K=5.
    # ------------------------------------------------------------------
    def test_aeroporto_duas_pistas_s2(self):
        """Lista M/M/sk, ex. 4: λ=0,25/min, μ=1/3/min, s=2, K=4."""
        r = MM1K(lam=0.25, mu=1 / 3, k=4, s=2).calcular(n=4, op_n=">")
        self.assertAlmostEqual(r["Lq"], 0.0848, places=4)
        self.assertAlmostEqual(r["Wq"], 0.3455, places=4)
        # P(> 2 na fila) = P(sistema cheio, n>4) = Pk = 0,0182
        self.assertAlmostEqual(r["Pk (Prob. Rejeição)"], 0.0182, places=4)

    def test_laboratorio_dois_equipamentos_s2(self):
        """Lista M/M/sk, ex. 5: λ=1/h, μ=4/3/h, s=2, K=4."""
        r = MM1K(lam=1, mu=4 / 3, k=4, s=2).calcular()
        self.assertAlmostEqual(r["L"], 0.8212, places=4)
        self.assertAlmostEqual(r["Pk (Prob. Rejeição)"], 0.0182, places=4)
        self.assertAlmostEqual(r["Wq"], 0.0864, places=4)

    def test_inspecao_gases_tres_boxes_s3(self):
        """Slide M/M/s>1/K, ex. 2: 3 boxes (s=3), 4 esperando (K=7),
        λ=1/min, μ=1/6/min (atend. 6 min)."""
        r = MM1K(lam=1, mu=1 / 6, k=7, s=3).calcular()
        self.assertAlmostEqual(r["P0"], 0.00088, places=5)
        self.assertAlmostEqual(r["L"], 6.0631, places=4)
        self.assertAlmostEqual(r["Lq"], 3.0920, places=4)
        self.assertAlmostEqual(r["W"], 12.2442, places=4)
        # gabarito arredonda Wq p/ 6,2439; valor exato é W - 1/μ = 6,24425
        self.assertAlmostEqual(r["Wq"], 6.2442, places=3)
        # Carros/hora rejeitados = λ·60·Pk = 30,29
        self.assertAlmostEqual(1 * 60 * r["Pk (Prob. Rejeição)"], 30.29, places=2)


# ----------------------------------------------------------------------------
# M/M/1/N (população finita - modelo de reparo de máquinas, 1 servidor)
# ----------------------------------------------------------------------------
class TestMM1N(unittest.TestCase):
    def test_industria_metal_mecanica(self):
        """Lista M/M/sN, ex. 1: N=10, λ=1/200/h, μ=0,1/h (reparo 10 h)."""
        r = MM1N(lam=1 / 200, mu=0.1, n=10).calcular()
        self.assertAlmostEqual(r["P0"], 0.5380, places=4)
        self.assertAlmostEqual(r["Lq"], 0.2972, places=4)
        self.assertAlmostEqual(r["L"], 0.7593, places=4)
        self.assertAlmostEqual(r["Wq"], 6.4330, places=3)
        self.assertAlmostEqual(r["W"], 16.4330, places=3)

    def test_mineradora_seis_trens(self):
        """Lista M/M/sN, ex. 2: N=6, λ=1/30/h, μ=0,15/h (reparo 6h40min)."""
        r = MM1N(lam=1 / 30, mu=0.15, n=6).calcular()
        self.assertAlmostEqual(r["L"], 2.1937, places=3)
        self.assertAlmostEqual(r["W"], 17.2906, places=3)
        self.assertAlmostEqual(r["Lq"], 1.3479, places=3)
        self.assertAlmostEqual(r["Wq"], 10.6239, places=3)

    def test_duas_maquinas_um_tecnico(self):
        """Lista M/M/sN, ex. 3: N=2, λ=0,1/h, μ=0,125/h (reparo 8h)."""
        r = MM1N(lam=0.1, mu=0.125, n=2).calcular()
        self.assertAlmostEqual(r["P0"], 0.2577, places=4)
        self.assertAlmostEqual(r["L"], 1.072, places=3)
        self.assertAlmostEqual(r["Lq"], 0.330, places=3)
        self.assertAlmostEqual(r["W"], 11.556, places=3)
        self.assertAlmostEqual(r["Wq"], 3.556, places=3)

    def test_forrester_tres_maquinas(self):
        """Lista M/M/sN, ex. 4: N=3, λ=1/9/h, μ=0,5/h (reparo 2h)."""
        r = MM1N(lam=1 / 9, mu=0.5, n=3).calcular()
        self.assertAlmostEqual(r["L"], 0.7181, places=4)
        self.assertAlmostEqual(r["W"], 2.832, places=3)

    def test_prob_n_trens(self):
        """Lista M/M/sN, ex. 2c: N=6, λ=1/30/h, μ=0,15/h -> P(4 trens)=0,1353."""
        r = MM1N(lam=1 / 30, mu=0.15, n=6).calcular(n=4, op_n="=")
        self.assertAlmostEqual(r["Prob. n = 4"], 0.1353, places=4)

    # ------------------------------------------------------------------
    # Casos particulares com s > 1 (segundo técnico/mecânico disponível)
    # ------------------------------------------------------------------
    def test_forrester_segundo_tecnico_s2(self):
        """Lista M/M/sN, ex. 4d: N=3, λ=1/9/h, μ=0,5/h, s=2 -> L=0,5528."""
        r = MM1N(lam=1 / 9, mu=0.5, n=3, s=2).calcular()
        self.assertAlmostEqual(r["L"], 0.5528, places=4)

    def test_4m_company_dois_tecnicos_s2(self):
        """Lista M/M/sN, ex. 6: N=4, λ=1/100/h, μ=0,1/h (reparo 10h), s=2."""
        r = MM1N(lam=0.01, mu=0.1, n=4, s=2).calcular()
        self.assertAlmostEqual(r["P0"], 0.6820, places=4)
        self.assertAlmostEqual(r["L"], 0.3677, places=4)
        self.assertAlmostEqual(r["Lq"], 0.0045, places=4)
        self.assertAlmostEqual(r["W"], 10.1239, places=4)
        self.assertAlmostEqual(r["Wq"], 0.1239, places=4)


# ----------------------------------------------------------------------------
# Prioridades SEM interrupção (não-preemptiva)
# ----------------------------------------------------------------------------
class TestPriorityNonPreemptive(unittest.TestCase):
    def test_southeast_airlines(self):
        """Lista M/G/1+prioridades, ex. 4: μ=20/h, λ1=2, λ2=10, s=1."""
        r = PriorityNonPreemptive(lambdas=[2, 10], mu=20, s=1).calcular()
        self.assertAlmostEqual(r["Ocupação (ρ)"], 0.6, places=4)
        c1, c2 = r["classes"]
        # Classe 1 (primeira classe)
        self.assertAlmostEqual(c1["W"], 0.083333, places=4)
        self.assertAlmostEqual(c1["Wq"], 0.033333, places=4)
        self.assertAlmostEqual(c1["L"], 0.166667, places=4)
        self.assertAlmostEqual(c1["Lq"], 0.066667, places=4)
        # Classe 2 (econômica)
        self.assertAlmostEqual(c2["W"], 0.133333, places=4)
        self.assertAlmostEqual(c2["Wq"], 0.083333, places=4)
        self.assertAlmostEqual(c2["L"], 1.333333, places=4)
        # Razão Wq1/Wq2 = 0,4
        self.assertAlmostEqual(c1["Wq"] / c2["Wq"], 0.4, places=4)

    def test_duas_classes_um_servidor_rapido(self):
        """Lista M/G/1+prioridades, ex. 5 (s=1): λ1=2, λ2=3, μ=6."""
        r = PriorityNonPreemptive(lambdas=[2, 3], mu=6, s=1).calcular()
        c1, c2 = r["classes"]
        self.assertAlmostEqual(c1["W"], 0.375, places=3)
        self.assertAlmostEqual(c1["Wq"], 0.208, places=3)
        self.assertAlmostEqual(c2["W"], 1.417, places=3)
        self.assertAlmostEqual(c2["Wq"], 1.25, places=3)
        self.assertAlmostEqual(c2["Lq"], 3.75, places=3)
        self.assertAlmostEqual(c2["L"], 4.25, places=3)

    def test_duas_classes_dois_servidores_lentos(self):
        """Lista M/G/1+prioridades, ex. 5 (s=2): λ1=2, λ2=3, μ=3, s=2."""
        r = PriorityNonPreemptive(lambdas=[2, 3], mu=3, s=2).calcular()
        c1, c2 = r["classes"]
        self.assertAlmostEqual(c1["Lq"], 0.379, places=3)
        self.assertAlmostEqual(c1["L"], 1.045, places=3)
        self.assertAlmostEqual(c1["Wq"], 0.189, places=3)
        self.assertAlmostEqual(c1["W"], 0.523, places=3)
        self.assertAlmostEqual(c2["Lq"], 3.409, places=3)
        self.assertAlmostEqual(c2["L"], 4.409, places=3)
        self.assertAlmostEqual(c2["Wq"], 1.136, places=3)
        self.assertAlmostEqual(c2["W"], 1.47, places=2)

    def test_ferramentaria_tres_tipos(self):
        """Lista M/G/1+prioridades, ex. 6b: λ=[2,4,2], μ=10/dia, s=1."""
        r = PriorityNonPreemptive(lambdas=[2, 4, 2], mu=10, s=1).calcular()
        w = [c["W"] for c in r["classes"]]
        self.assertAlmostEqual(w[0], 0.2, places=4)
        self.assertAlmostEqual(w[1], 0.35, places=4)
        self.assertAlmostEqual(w[2], 1.1, places=4)

    def test_sistema_instavel(self):
        r = PriorityNonPreemptive(lambdas=[5, 5], mu=4, s=1).calcular()
        self.assertIn("Erro", r)


# ----------------------------------------------------------------------------
# Prioridades COM interrupção (preemptiva)
# ----------------------------------------------------------------------------
class TestPriorityPreemptive(unittest.TestCase):
    def test_ferramentaria_tres_tipos(self):
        """Lista M/G/1+prioridades, ex. 6c: λ=[2,4,2], μ=10/dia, s=1."""
        r = PriorityPreemptive(lambdas=[2, 4, 2], mu=10, s=1).calcular()
        w = [c["W"] for c in r["classes"]]
        self.assertAlmostEqual(w[0], 0.125, places=4)
        self.assertAlmostEqual(w[1], 0.3125, places=4)
        self.assertAlmostEqual(w[2], 1.25, places=4)

    def test_sistema_instavel(self):
        r = PriorityPreemptive(lambdas=[5, 5], mu=4, s=1).calcular()
        self.assertIn("Erro", r)


# ----------------------------------------------------------------------------
# Funções de engenharia reversa (Módulo Investigador) + integração com M/M/1
# ----------------------------------------------------------------------------
class TestReverse(unittest.TestCase):
    def test_reverse_rho_wq_round_trip(self):
        """ρ e Wq de um M/M/1(λ=3, μ=4) devem recuperar λ=3, μ=4."""
        lam, mu = reverse_rho_wq(rho=0.75, wq=0.75)
        self.assertAlmostEqual(lam, 3.0, places=6)
        self.assertAlmostEqual(mu, 4.0, places=6)

    def test_reverse_w_lq_round_trip(self):
        """W e Lq de um M/M/1(λ=3, μ=4) devem recuperar λ=3, μ=4."""
        lam, mu = reverse_w_lq(w=1.0, lq=2.25)
        self.assertAlmostEqual(lam, 3.0, places=6)
        self.assertAlmostEqual(mu, 4.0, places=6)

    def test_reverse_mu_wq_round_trip(self):
        """μ e Wq de um M/M/1(λ=3, μ=4) devem recuperar λ=3."""
        lam, mu = reverse_mu_wq(mu=4.0, wq=0.75)
        self.assertAlmostEqual(lam, 3.0, places=6)
        self.assertAlmostEqual(mu, 4.0, places=6)

    def test_confeitaria_reverse_rho_wq(self):
        """Lista M/M/s, ex. 10a: ρ=0,75 e Wq=2,5 min -> L=3, W=10/3 min."""
        lam, mu = reverse_rho_wq(rho=0.75, wq=2.5)
        r = MM1(lam, mu).calcular()
        self.assertAlmostEqual(r["L"], 3.0, places=4)
        self.assertAlmostEqual(r["W"], 10 / 3, places=4)

    def test_clientes_reverse_w_lq(self):
        """Lista M/M/s, ex. 3: W=0,5 h e Lq=3,2 -> P(n<6)=0,7378."""
        lam, mu = reverse_w_lq(w=0.5, lq=3.2)
        self.assertAlmostEqual(lam, 8.0, places=4)
        self.assertAlmostEqual(mu, 10.0, places=4)
        r = MM1(lam, mu).calcular(n=6, op_n="<")
        # gabarito truncado em 4 casas (0,7378); valor exato 0,73786
        self.assertAlmostEqual(r["Prob. n < 6"], 0.7378, places=3)

    def test_reverse_w_lq_sem_solucao(self):
        """Delta negativo (Lq inválido) deve retornar (None, None)."""
        lam, mu = reverse_w_lq(w=1.0, lq=-2.0)
        self.assertIsNone(lam)
        self.assertIsNone(mu)


# ----------------------------------------------------------------------------
# Funções auxiliares de probabilidade
# ----------------------------------------------------------------------------
class TestHelpers(unittest.TestCase):
    def test_prob_mm1_operadores(self):
        rho = 0.75
        self.assertAlmostEqual(prob_mm1(rho, 6, "="), (1 - rho) * rho ** 6, places=10)
        self.assertAlmostEqual(prob_mm1(rho, 2, ">"), rho ** 3, places=10)
        self.assertAlmostEqual(prob_mm1(rho, 2, ">="), rho ** 2, places=10)
        self.assertAlmostEqual(prob_mm1(rho, 5, "<="), 1 - rho ** 6, places=10)
        self.assertAlmostEqual(prob_mm1(rho, 6, "<"), 1 - rho ** 6, places=10)
        # As probabilidades complementares devem somar 1.
        self.assertAlmostEqual(
            prob_mm1(rho, 3, "<=") + prob_mm1(rho, 3, ">"), 1.0, places=10
        )

    def test_mms_metrics_consistencia(self):
        """mms_metrics deve satisfazer as relações de Little (L=λW, Lq=λWq)."""
        rho, p0, Lq, Wq, W, L = mms_metrics(lam=2, mu=3, s=2)
        self.assertAlmostEqual(L, 2 * W, places=10)
        self.assertAlmostEqual(Lq, 2 * Wq, places=10)
        self.assertAlmostEqual(W, Wq + 1 / 3, places=10)
        self.assertAlmostEqual(p0, 0.5, places=10)

    def test_prob_mms_acumulada_soma_um(self):
        """P(n<=k) + P(n>k) = 1 para o M/M/s."""
        _, p0, _, _, _, _ = mms_metrics(lam=2, mu=3, s=2)
        menor = prob_mms_acumulada(2, 3, 2, p0, 3, "<=")
        maior = prob_mms_acumulada(2, 3, 2, p0, 3, ">")
        self.assertAlmostEqual(menor + maior, 1.0, places=10)

    def test_prob_mms_exata_vs_mm1(self):
        """Para s=1, prob_mms_exata reduz à fórmula M/M/1."""
        lam, mu = 2, 3
        rho = lam / mu
        p0 = 1 - rho
        for i in range(5):
            self.assertAlmostEqual(
                prob_mms_exata(lam, mu, 1, p0, i),
                (1 - rho) * rho ** i,
                places=10,
            )




class TestExerciciosAdicionais(unittest.TestCase):

    def test_industria_metal_mecanica_custo_total(self):
        """
        Lista M/M/sN, ex. 1
        Custo diário:
        CT = 219,192
        """
        r = MM1N(lam=1/200, mu=0.1, n=10).calcular()

        L = r["L"]

        custo_paradas = L * 30 * 8
        custo_manutencao = (1 - r["P0"]) * 10 * 8

        ct = custo_paradas + custo_manutencao

        self.assertAlmostEqual(ct, 219.1862, places=3)

    def test_duas_maquinas_tecnico_ocupado(self):
        """
        Lista M/M/sN, ex. 3 letra C
        Proporção do tempo que o técnico está ocupado.
        Resultado esperado = 0,7423
        """
        r = MM1N(lam=0.1, mu=0.125, n=2).calcular()

        ocupacao = 1 - r["P0"]

        self.assertAlmostEqual(ocupacao, 0.7423, places=4)

    def test_duas_maquinas_operando(self):
        """
        Lista M/M/sN, ex. 3 letra D
        Proporção de tempo que uma máquina está operando.
        Resultado esperado = 0,464
        """
        r = MM1N(lam=0.1, mu=0.125, n=2).calcular()

        disponibilidade = (2 - r["L"]) / 2

        self.assertAlmostEqual(disponibilidade, 0.464, places=3)

    def test_industria_metal_mecanica_maquinas_operando(self):
        """
        Lista M/M/sN, ex. 1
        Disponibilidade média das máquinas.
        """
        r = MM1N(lam=1/200, mu=0.1, n=10).calcular()

        disponibilidade = (10 - r["L"]) / 10

        self.assertAlmostEqual(disponibilidade, 0.92407, places=4)

    def test_industria_metal_mecanica_tecnico_ocupado(self):
        """
        Lista M/M/sN, ex. 1
        Utilização do técnico.
        """
        r = MM1N(lam=1/200, mu=0.1, n=10).calcular()

        ocupacao = 1 - r["P0"]

        self.assertAlmostEqual(ocupacao, 0.4620, places=4)

    def test_duas_maquinas_consistencia_disponibilidade(self):
        """
        Lista M/M/sN, ex. 3

        Disponibilidade calculada por:
            (N - L)/N

        Deve coincidir com o gabarito.
        """
        r = MM1N(lam=0.1, mu=0.125, n=2).calcular()

        disponibilidade = (2 - r["L"]) / 2

        self.assertAlmostEqual(disponibilidade, 0.464, places=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)        