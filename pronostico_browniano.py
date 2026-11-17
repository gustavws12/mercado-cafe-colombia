# -*- coding: utf-8 -*-
"""Pronóstico del café con movimiento browniano geométrico (MBG) para el cierre de 2026 y 2027.
Precio: dS = mu S dt + sigma S dW sobre el precio interno real mensual; en logaritmos, caminata aleatoria con deriva: ln S_{t+h} = ln S_t + (mu - sigma^2/2) h + sigma sqrt(h) Z.
Producción: el mismo proceso sobre la producción acumulada de doce meses (que elimina la estacionalidad), de modo que su valor en diciembre es la producción del año.
Deriva y volatilidad estimadas con los incrementos mensuales del logaritmo, 1996-2026. 10.000 trayectorias. Validación hacia atrás con origen en octubre (2014-2024).
Produce además la imagen compuesta de la publicación: mapa de producción + pronóstico."""
import numpy as np, pandas as pd, geopandas as gpd, json, os, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
RAIZ = os.path.dirname(os.path.abspath(__file__)); D = f"{RAIZ}/datos"; OUT = f"{RAIZ}/resultados"
AZUL, NARANJA, AQUA, AMAR, GRIS, GRISC, TXT, TXT2, SURF, CAFE = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#9a9893", "#d9d8d4", "#0b0b0b", "#52514e", "#fcfcfb", "#7a4a2a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRISC, "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": "#e8e7e3"})
m = pd.read_csv(f"{OUT}/cafe_mensual_1996_2026.csv"); m.index = pd.PeriodIndex(m.mes, freq="M"); m = m.dropna(subset=["precio_kg_real", "kg_verde"]); a = pd.read_csv(f"{OUT}/cafe_anual_1996_2026.csv", index_col=0)
m["q12"] = m.kg_verde.rolling(12).sum(); NS, H, INFL27 = 10000, 14, 0.055; rng = np.random.default_rng(20261117)
def pars(s): d = np.log(s.dropna()).diff().dropna(); return float(d.mean()), float(d.std(ddof=1))      # deriva y volatilidad mensual del logaritmo
def tray(s0, mu, sg, h, ns): return s0 * np.exp(np.cumsum(mu + sg * rng.standard_normal((h, ns)), axis=0))
# ---------- validación hacia atrás ----------
bt = []
for y in range(2014, 2025):
    tr = m.loc[:f"{y}-10"]; ob = m.loc[f"{y+1}-01":f"{y+1}-12"]; mu, sg = pars(tr.precio_kg_real); mq, sq_ = pars(tr.q12)
    fp = tr.precio_kg_real.iloc[-1] * np.exp(mu * np.arange(3, 15)); fq = tr.q12.iloc[-1] * np.exp(mq * 14)
    bt.append(dict(ano=y + 1, precio_obs=ob.precio_kg_real.mean(), precio_mbg=float(fp.mean()), precio_ingenuo=float(tr.precio_kg_real.iloc[-1]), prod_obs=ob.kg_verde.sum() / 1e6, prod_mbg=float(fq) / 1e6, prod_ingenuo=tr.q12.iloc[-1] / 1e6,
                   dentro_80_precio=bool(abs(np.log(ob.precio_kg_real.mean() / fp.mean())) <= 1.2816 * sg * np.sqrt(8.5))))
bt = pd.DataFrame(bt)
for c in ["precio_mbg", "precio_ingenuo"]: bt["ea_" + c] = (bt[c] / bt.precio_obs - 1).abs() * 100
for c in ["prod_mbg", "prod_ingenuo"]: bt["ea_" + c] = (bt[c] / bt.prod_obs - 1).abs() * 100
ar = pd.read_csv(f"{OUT}/validacion_pronostico.csv"); bt["precio_ar"] = ar.precio_ar.values; bt["ea_precio_ar"] = ar.ea_precio_ar.values; bt["ea_prod_sarima"] = ar.ea_prod_sarima.values
bt.round(2).to_csv(f"{OUT}/validacion_browniano.csv", index=False); val = {k: round(float(bt[k].mean()), 1) for k in bt.columns if k.startswith("ea_")}; val["cobertura_banda_80_precio"] = float(bt.dentro_80_precio.mean())
print(bt[["ano", "precio_obs", "precio_mbg", "precio_ar", "prod_obs", "prod_mbg", "dentro_80_precio"]].round(0).to_string(index=False)); print(val)
# ---------- pronóstico ----------
mu, sg = pars(m.precio_kg_real); mq, sq_ = pars(m.q12); print(f"precio: deriva mensual {mu:.5f} ({(np.exp(12*mu)-1)*100:.1f} % anual), volatilidad mensual {sg:.4f} ({sg*np.sqrt(12)*100:.0f} % anual) | producción 12m: deriva {mq:.5f}, volatilidad {sq_:.4f}")
sp = tray(m.precio_kg_real.iloc[-1], mu, sg, H, NS); sq = tray(m.q12.iloc[-1], mq, sq_, H, NS); idx = pd.period_range(m.index[-1] + 1, periods=H, freq="M"); q = lambda z, p: np.quantile(z, p, axis=1)
f = pd.DataFrame({"mes": idx.astype(str), "precio_p10": q(sp, .1), "precio_p25": q(sp, .25), "precio_p50": q(sp, .5), "precio_p75": q(sp, .75), "precio_p90": q(sp, .9)}); f.round(1).to_csv(f"{OUT}/pronostico_browniano_mensual.csv", index=False)
o26 = m.loc["2026-01":]; R = lambda v: dict(p10=float(np.quantile(v, .1)), p50=float(np.quantile(v, .5)), p90=float(np.quantile(v, .9)), media=float(v.mean()))
p26 = (o26.precio_kg_real.sum() + sp[:2].sum(0)) / 12; q26 = sq[1] / 1e6; v26 = (o26.valor_real.sum() + np.maximum(sq[1] - o26.kg_verde.sum(), 0) / 0.8 * sp[:2].mean(0)) / 1e12
p27 = sp[2:].mean(0); q27 = sq[-1] / 1e6; v27 = sq[-1] / 0.8 * p27 / 1e12; r25 = a.loc[2025]
res = dict(modelo="movimiento browniano geométrico", simulaciones=NS, precio=dict(ultimo=float(m.precio_kg_real.iloc[-1]), deriva_mensual_log=mu, deriva_anual_pct=float((np.exp(12 * mu) - 1) * 100), volatilidad_mensual=sg, volatilidad_anual_pct=float(sg * np.sqrt(12) * 100)),
    produccion=dict(ultimos_12_meses_millones_kg=float(m.q12.iloc[-1] / 1e6), deriva_mensual_log=mq, volatilidad_mensual=sq_), validacion=val,
    cierre_2026=dict(precio_kg_real_promedio_ano=R(p26), precio_kg_real_diciembre=R(sp[1]), produccion_millones_kg=R(q26), valor_real_billones=R(v26)),
    ano_2027=dict(precio_kg_real_promedio_ano=R(p27), precio_kg_real_diciembre=R(sp[-1]), precio_kg_nominal_promedio_ano=R(p27 * (1 + INFL27 * .75)), produccion_millones_kg=R(q27), valor_real_billones=R(v27),
        prob_precio_mayor_2025=float((p27 > r25.precio_kg_real).mean()), prob_precio_mayor_promedio_historico=float((p27 > 12159).mean()), prob_precio_menor_promedio_historico=float((p27 < 12159).mean()), prob_valor_mayor_2025=float((v27 > r25.valor_real / 1e12).mean()), prob_valor_mayor_2024=float((v27 > a.loc[2024].valor_real / 1e12).mean()), prob_valor_menor_15=float((v27 < 15).mean()), prob_valor_mayor_max_pre2021=float((v27 > 13.29).mean())))
json.dump(res, open(f"{OUT}/pronostico_browniano_resumen.json", "w"), indent=1, ensure_ascii=False); print(json.dumps({k: res[k] for k in ["cierre_2026", "ano_2027"]}, indent=1, ensure_ascii=False))
# ---------- imagen de la publicación: mapa + pronóstico ----------
mil = lambda v: f"{v:,.0f}".replace(",", "."); co = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
r = pd.read_csv(f"{OUT}/produccion_municipal_promedio_2021_2025.csv", dtype={"cod": str}); r["cod"] = r.cod.str.zfill(5); dp = pd.read_csv(f"{OUT}/produccion_departamental_promedio_2021_2025.csv", index_col=0)
g = gpd.read_file(f"{D}/mpios_simplificado.geojson"); g["cod"] = g.mpio_cdpmp.astype(str).str.zfill(5); g = g.merge(r[["cod", "prod_t"]], on="cod", how="left"); g["prod_t"] = g.prod_t.fillna(0)
mp_ = g.copy(); mp_["geometry"] = mp_.buffer(0.012); dep = mp_.dissolve("dpto_cnmbr").reset_index()[["dpto_cnmbr", "geometry"]]; dep["geometry"] = dep.buffer(-0.012)
cmap = LinearSegmentedColormap.from_list("c", ["#f3f2ee", "#f6e3c5", "#e8b96a", "#c98234", "#96531f", "#5a2d0c", "#2e1505"]); bounds = [0, 50, 500, 1500, 3000, 6000, 10000, 1e9]; norm = BoundaryNorm(bounds, cmap.N)
fig = plt.figure(figsize=(19.2, 9.6), dpi=100)
ax = fig.add_axes([0.0, 0.15, 0.36, 0.69]); ax.set_axis_off(); g.plot(column="prod_t", cmap=cmap, norm=norm, ax=ax, edgecolor="none"); dep.boundary.plot(ax=ax, color="#6b6a66", linewidth=0.45); ax.set_xlim(-79.4, -71.4); ax.set_ylim(0.2, 11.6)
for n, off in [("HUILA", (10, -30)), ("ANTIOQUIA", (-62, 22)), ("CAUCA", (-78, -12)), ("TOLIMA", (30, 6)), ("SANTANDER", (14, 10))]:
    pt = dep[dep.dpto_cnmbr == n].geometry.iloc[0].representative_point(); ax.annotate(f"{n.title()} {dp.part_pct[n]:.0f} %", (pt.x, pt.y), xytext=off, textcoords="offset points", fontsize=10.5, color=TXT, path_effects=[pe.withStroke(linewidth=2.8, foreground=SURF)], arrowprops=dict(arrowstyle="-", color=TXT2, lw=.6))
cax = fig.add_axes([0.035, 0.135, 0.29, 0.016]); cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=cax, orientation="horizontal", ticks=[0, 50, 500, 1500, 3000, 6000, 10000]); cb.set_ticklabels(["0", "50", "500", "1.500", "3.000", "6.000", "10.000"]); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=9)
cb.set_label("Toneladas de café por año por municipio, promedio 2021-2025", color=TXT2, fontsize=9.5); fig.text(0.035, 0.855, "Dónde se produce: 642 municipios, el Huila primero", fontsize=12.5, color=TXT)
h = m.loc["2012-01":]; xh = h.index.to_timestamp(); xf = idx.to_timestamp(); ax1 = fig.add_axes([0.415, 0.50, 0.57, 0.33])
ax1.plot(xh, h.precio_kg_real, color=CAFE, lw=1.8, label="Precio interno real por kilo de pergamino"); ax1.fill_between(xf, f.precio_p10, f.precio_p90, color=NARANJA, alpha=.18, label="Movimiento browniano: banda de 80 %"); ax1.fill_between(xf, f.precio_p25, f.precio_p75, color=NARANJA, alpha=.28, label="Banda de 50 %"); ax1.plot(xf, f.precio_p50, color=NARANJA, lw=2.2, label="Mediana")
ax1.axhline(12159, color=TXT2, lw=.8, ls="--"); ax1.text(xh[1], 12159 * 1.04, "Promedio real 1996-2025: 12.159", fontsize=9.5, color=TXT2)
ax1.annotate(f"Dic 2027: {mil(f.precio_p50.iloc[-1])}\n({mil(f.precio_p10.iloc[-1])} a {mil(f.precio_p90.iloc[-1])})", (xf[-1], f.precio_p50.iloc[-1]), xytext=(-190, -105), textcoords="offset points", fontsize=10, color=NARANJA, arrowprops=dict(arrowstyle="-", color=NARANJA, lw=.8))
ax1.set_ylim(0, 31000); ax1.set_ylabel("Pesos de 2026 por kilo"); ax1.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2); ax1.set_title("Precio interno real por kilo y pronóstico con movimiento browniano geométrico", loc="left", fontsize=12.5, color=TXT, pad=8)
A = a[a.meses_prod == 12].loc[2012:]
for k, (col, lab, obs, f26, f27, d) in enumerate([(AQUA, "Producción (millones de kg de café verde)", A.kg_verde / 1e6, R(q26), R(q27), 0), (NARANJA, "Valor real de la cosecha (billones de pesos de 2026)", A.valor_real / 1e12, R(v26), R(v27), 1)]):
    ax2 = fig.add_axes([0.415 + k * 0.295, 0.125, 0.275, 0.27]); ax2.bar(A.index, obs, color=col, width=.7)
    for yy, ff in [(2026, f26), (2027, f27)]:
        ax2.bar(yy, ff["p50"], color=col, alpha=.4, width=.7); ax2.errorbar(yy, ff["p50"], yerr=[[ff["p50"] - ff["p10"]], [ff["p90"] - ff["p50"]]], color=TXT, lw=1.2, capsize=4); ax2.text(yy, ff["p90"] + obs.max() * .03, co(ff["p50"], d), ha="center", fontsize=10, color=TXT)
    ax2.text(2025, obs[2025] + obs.max() * .03, co(obs[2025], d), ha="center", fontsize=10, color=TXT); ax2.set_xticks(range(2012, 2028)); ax2.set_xticklabels([str(y)[2:] for y in range(2012, 2028)], fontsize=9.5); ax2.grid(axis="x", visible=False); ax2.set_ylim(0, obs.max() * 1.25); ax2.set_title(lab, loc="left", fontsize=12, color=TXT, pad=8)
p7 = res["ano_2027"]
fig.text(0.012, 0.955, "Café colombiano: cinco años de bonanza y un 2027 que nadie puede asegurar", fontsize=22, color=TXT, va="center")
fig.text(0.012, 0.905, f"Entre 2021 y 2025 la cosecha valió 93 billones de pesos de hoy, 35 billones más que en los cinco años anteriores. Para 2027 el movimiento browniano da una mediana de {mil(p7['precio_kg_real_promedio_ano']['p50'])} pesos por kilo\ny una cosecha de {co(p7['valor_real_billones']['p50'])} billones, pero con una banda de 80 % que va de {co(p7['valor_real_billones']['p10'])} a {co(p7['valor_real_billones']['p90'])} billones. Las barras claras son pronóstico.", fontsize=12, color=TXT2, va="center")
fig.text(0.012, 0.035, f"Fuente: Elaboración propia con Federación Nacional de Cafeteros (precio interno base de compra y producción registrada), IPC (OCDE y DANE), Evaluaciones Agropecuarias Municipales del Ministerio de Agricultura y MGN del DANE. Pesos de septiembre de 2026.\nMovimiento browniano geométrico con deriva y volatilidad de 1996-2026 (volatilidad anual del precio: {res['precio']['volatilidad_anual_pct']:.0f} %); {mil(NS)} trayectorias. Error absoluto medio del precio a un año en la validación 2015-2025: {val['ea_precio_mbg']:.0f} %. No incorpora Nueva York, la tasa de cambio ni el clima. Gustavo A Romero.", fontsize=9.5, color=TXT2)
fig.savefig(f"{RAIZ}/fig4_publicacion_mapa_pronostico.png"); print("ok")
