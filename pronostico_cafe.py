# -*- coding: utf-8 -*-
"""Pronóstico del café colombiano para el cierre de 2026 y 2027: precio interno real por kilo, producción y valor de la cosecha.
Precio: AR sobre el logaritmo del precio real mensual (reversión a la media), comparado con caminata aleatoria. Producción: SARIMA sobre el logaritmo.
Simulación conjunta de 5.000 trayectorias; validación hacia atrás con origen en octubre de cada año (2014-2024)."""
import numpy as np, pandas as pd, json, os, warnings, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
warnings.filterwarnings("ignore"); from statsmodels.tsa.statespace.sarimax import SARIMAX
RAIZ = os.path.dirname(os.path.abspath(__file__)); OUT = f"{RAIZ}/resultados"
AZUL, NARANJA, AQUA, AMAR, GRIS, GRISC, TXT, TXT2, SURF, CAFE = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#9a9893", "#d9d8d4", "#0b0b0b", "#52514e", "#fcfcfb", "#7a4a2a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRISC, "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": "#e8e7e3"})
m = pd.read_csv(f"{OUT}/cafe_mensual_1996_2026.csv"); m.index = pd.PeriodIndex(m.mes, freq="M"); m = m.dropna(subset=["precio_kg_real", "kg_verde"])
NS, INFL27 = 5000, 0.055; rng = np.random.default_rng(20261117)
def ajustar(y_p, y_q):
    mp = SARIMAX(np.log(y_p), order=(2, 0, 0), trend="c").fit(disp=False); mq = SARIMAX(np.log(y_q), order=(1, 0, 1), seasonal_order=(0, 1, 1, 12)).fit(disp=False); return mp, mq
def simular(mp, mq, h, ns):
    np.random.seed(20261117); sp = np.exp(np.asarray(mp.simulate(h, anchor="end", repetitions=ns)).reshape(h, ns)); sq = np.exp(np.asarray(mq.simulate(h, anchor="end", repetitions=ns)).reshape(h, ns)); return sp, sq
# ---------- validación hacia atrás: origen en octubre, se pronostica el año siguiente completo ----------
bt = []
for y in range(2014, 2025):
    tr = m.loc[:f"{y}-10"]; mp, mq = ajustar(tr.precio_kg_real, tr.kg_verde); fp = np.exp(mp.forecast(14)); fq = np.exp(mq.forecast(14)); ob = m.loc[f"{y+1}-01":f"{y+1}-12"]
    bt.append(dict(origen=f"{y}-10", ano=y + 1, precio_obs=ob.precio_kg_real.mean(), precio_ar=float(fp[2:].mean()), precio_ingenuo=float(tr.precio_kg_real.iloc[-1]) * ob.ipc.iloc[-1] / ob.ipc.iloc[-1], prod_obs=ob.kg_verde.sum() / 1e6, prod_sarima=float(fq[2:].sum()) / 1e6, prod_ingenuo=tr.kg_verde.iloc[-12:].sum() / 1e6))
bt = pd.DataFrame(bt)
# los precios reales del ejercicio están en pesos de sep-2026 en toda la muestra, así que el pronóstico ingenuo es el último precio real observado
for c in ["precio_ar", "precio_ingenuo"]: bt["ea_" + c] = (bt[c] / bt.precio_obs - 1).abs() * 100
for c in ["prod_sarima", "prod_ingenuo"]: bt["ea_" + c] = (bt[c] / bt.prod_obs - 1).abs() * 100
bt.round(2).to_csv(f"{OUT}/validacion_pronostico.csv", index=False); print(bt[["ano", "precio_obs", "precio_ar", "precio_ingenuo", "prod_obs", "prod_sarima", "prod_ingenuo"]].round(0).to_string(index=False))
val = {k: round(float(bt[k].mean()), 1) for k in bt.columns if k.startswith("ea_")}; print("error absoluto medio %:", val)
# ---------- pronóstico ----------
mp, mq = ajustar(m.precio_kg_real, m.kg_verde); print(mp.params.round(4).to_dict()); phi = mp.params.filter(like="ar.").sum(); mu = float(np.exp(mp.params["intercept"] / (1 - phi))); print("media de largo plazo del precio real:", round(mu), "| persistencia:", round(float(phi), 4), "| vida media (meses):", round(float(np.log(.5) / np.log(phi)), 1))
H = 14; sp, sq = simular(mp, mq, H, NS); idx = pd.period_range(m.index[-1] + 1, periods=H, freq="M")
q = lambda a, p: np.quantile(a, p, axis=1)
f = pd.DataFrame({"mes": idx.astype(str), "precio_p10": q(sp, .1), "precio_p50": q(sp, .5), "precio_p90": q(sp, .9), "prod_p10": q(sq, .1) / 1e6, "prod_p50": q(sq, .5) / 1e6, "prod_p90": q(sq, .9) / 1e6}); f.round(1).to_csv(f"{OUT}/pronostico_mensual_2026_2027.csv", index=False)
o26 = m.loc["2026-01":]; val_m = sp * (sq / 0.8)                                                  # pesos de sep-2026
def resumen(v): return dict(p10=float(np.quantile(v, .1)), p50=float(np.quantile(v, .5)), p90=float(np.quantile(v, .9)), media=float(v.mean()))
p26 = (o26.precio_kg_real.sum() + sp[:2].sum(0)) / 12; q26 = (o26.kg_verde.sum() + sq[:2].sum(0)) / 1e6; v26 = (o26.valor_real.sum() + val_m[:2].sum(0)) / 1e12
p27 = sp[2:].mean(0); q27 = sq[2:].sum(0) / 1e6; v27 = val_m[2:].sum(0) / 1e12; dic26 = sp[1]; dic27 = sp[-1]
a = pd.read_csv(f"{OUT}/cafe_anual_1996_2026.csv", index_col=0); r25 = a.loc[2025]
res = dict(supuestos=dict(simulaciones=NS, inflacion_2027=INFL27, modelo_precio="AR(2) con constante sobre log del precio real mensual 1996-2026", modelo_produccion="SARIMA(1,0,1)(0,1,1)12 sobre log de la producción mensual", media_largo_plazo_precio_real=mu, vida_media_meses=float(np.log(.5) / np.log(phi))),
    validacion_error_absoluto_medio_pct=val, observado_2025=dict(precio_kg_real=float(r25.precio_kg_real), produccion_millones_kg=float(r25.kg_verde / 1e6), valor_real_billones=float(r25.valor_real / 1e12)),
    cierre_2026=dict(precio_kg_real_promedio_ano=resumen(p26), precio_kg_real_diciembre=resumen(dic26), produccion_millones_kg=resumen(q26), valor_real_billones=resumen(v26)),
    ano_2027=dict(precio_kg_real_promedio_ano=resumen(p27), precio_kg_real_diciembre=resumen(dic27), precio_kg_nominal_promedio_ano=resumen(p27 * (1 + INFL27 * 0.75)), produccion_millones_kg=resumen(q27), valor_real_billones=resumen(v27),
        prob_precio_mayor_2025=float((p27 > r25.precio_kg_real).mean()), prob_precio_mayor_promedio_historico=float((p27 > 12159).mean()), prob_valor_mayor_2024=float((v27 > a.loc[2024].valor_real / 1e12).mean()), prob_valor_menor_15=float((v27 < 15).mean())))
json.dump(res, open(f"{OUT}/pronostico_cafe_resumen.json", "w"), indent=1, ensure_ascii=False); print(json.dumps({k: res[k] for k in ["cierre_2026", "ano_2027"]}, indent=1, ensure_ascii=False))
# ---------- Figura 3 ----------
mil = lambda v: f"{v:,.0f}".replace(",", "."); h = m.loc["2015-01":]; xh = h.index.to_timestamp(); xf = idx.to_timestamp()
fig = plt.figure(figsize=(19.2, 9.6), dpi=100); gs = fig.add_gridspec(2, 2, left=0.055, right=0.985, top=0.80, bottom=0.13, hspace=0.42, wspace=0.16, width_ratios=[1.35, 1])
ax = fig.add_subplot(gs[:, 0]); ax.plot(xh, h.precio_kg_real, color=CAFE, lw=1.8, label="Precio interno real por kilo de pergamino"); ax.fill_between(xf, f.precio_p10, f.precio_p90, color=NARANJA, alpha=.22, label="Pronóstico: banda de 80 %"); ax.plot(xf, f.precio_p50, color=NARANJA, lw=2.2, label="Pronóstico: mediana")
ax.axhline(12159, color=TXT2, lw=.8, ls="--"); ax.text(xh[1], 12159 * 1.025, "Promedio real 1996-2025: 12.159", fontsize=9.5, color=TXT2)
ax.annotate(f"Dic 2026: {mil(res['cierre_2026']['precio_kg_real_diciembre']['p50'])}", (xf[1], f.precio_p50[1]), xytext=(-70, -40), textcoords="offset points", fontsize=10, color=NARANJA, arrowprops=dict(arrowstyle="-", color=NARANJA, lw=.8))
ax.annotate(f"Dic 2027: {mil(f.precio_p50.iloc[-1])}\n({mil(f.precio_p10.iloc[-1])} a {mil(f.precio_p90.iloc[-1])})", (xf[-1], f.precio_p50.iloc[-1]), xytext=(-120, 55), textcoords="offset points", fontsize=10, color=NARANJA, arrowprops=dict(arrowstyle="-", color=NARANJA, lw=.8))
ax.set_ylim(0, 30000); ax.set_ylabel("Pesos de 2026 por kilo"); ax.legend(frameon=False, fontsize=10, loc="upper left"); ax.set_title("Precio interno real por kilo, 2015-2027", loc="left", fontsize=12.5, color=TXT, pad=8)
A = a[a.meses_prod == 12].loc[2015:]
for k, (col, lab, obs, f26, f27, fmt) in enumerate([(AQUA, "Producción anual (millones de kg de café verde)", A.kg_verde / 1e6, resumen(q26), resumen(q27), "{:.0f}"), (NARANJA, "Valor real de la cosecha (billones de pesos de 2026)", A.valor_real / 1e12, resumen(v26), resumen(v27), "{:.1f}")]):
    ax2 = fig.add_subplot(gs[k, 1]); ax2.bar(A.index, obs, color=col, width=.7)
    for yy, ff in [(2026, f26), (2027, f27)]:
        ax2.bar(yy, ff["p50"], color=col, alpha=.4, width=.7); ax2.errorbar(yy, ff["p50"], yerr=[[ff["p50"] - ff["p10"]], [ff["p90"] - ff["p50"]]], color=TXT, lw=1.2, capsize=4); ax2.text(yy, ff["p90"] + obs.max() * .03, fmt.format(ff["p50"]).replace(".", ","), ha="center", fontsize=10, color=TXT)
    ax2.text(2025, obs[2025] + obs.max() * .03, fmt.format(obs[2025]).replace(".", ","), ha="center", fontsize=10, color=TXT); ax2.set_xticks(range(2015, 2028)); ax2.set_xticklabels([str(y)[2:] for y in range(2015, 2028)]); ax2.grid(axis="x", visible=False); ax2.set_ylim(0, obs.max() * 1.22); ax2.set_title(lab, loc="left", fontsize=12.5, color=TXT, pad=8)
fig.text(0.012, 0.955, "Café: 2025 no se repite, pero el pronóstico para 2027 sigue por encima de la historia", fontsize=21, color=TXT, va="center")
p7 = res["ano_2027"]; sub = ("Pronóstico del precio interno, la producción y el valor de la cosecha para el cierre de 2026 y 2027, en pesos de septiembre de 2026. Las barras claras son pronóstico, con banda de 80 %.\n"
       f"Para 2027 la mediana es un precio de {mil(p7['precio_kg_real_promedio_ano']['p50'])} pesos por kilo, una cosecha de {mil(p7['produccion_millones_kg']['p50'])} millones de kilos y un valor de " + f"{p7['valor_real_billones']['p50']:.1f}".replace(".", ",") + " billones: menos que en 2025, más que en cualquier año anterior a 2021.")
fig.text(0.012, 0.895, sub, fontsize=12, color=TXT2, va="center")
fig.text(0.012, 0.035, f"Fuente: Elaboración propia con Federación Nacional de Cafeteros (precio interno base de compra y producción registrada) e IPC (OCDE y DANE). Precio: modelo autorregresivo sobre el logaritmo del precio real; producción: SARIMA; {mil(NS)} simulaciones.\nEn la validación 2015-2025, con origen en octubre, el error absoluto medio del precio a un año fue {val['ea_precio_ar']:.0f} % y el de la producción {val['ea_prod_sarima']:.0f} %. El modelo no incorpora el precio internacional, la tasa de cambio ni el clima. Gustavo A Romero.".replace(".0 %", " %"), fontsize=9.5, color=TXT2)
fig.savefig(f"{RAIZ}/fig3_pronostico_2026_2027.png"); print("ok")
