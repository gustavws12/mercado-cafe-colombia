# -*- coding: utf-8 -*-
"""Mercado del café en Colombia, 1996-2026: precio interno por kilo deflactado, producción anual en kilogramos, valor real de la cosecha y mapa de producción por municipio.
Fuentes: Federación Nacional de Cafeteros (precio interno base de compra, producción registrada, valor de la cosecha, área), IPC (OCDE vía FRED + DANE),
Evaluaciones Agropecuarias Municipales del Ministerio de Agricultura (datos.gov.co) y Marco Geoestadístico Nacional del DANE."""
import numpy as np, pandas as pd, geopandas as gpd, json, os, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
RAIZ = os.path.dirname(os.path.abspath(__file__)); D = f"{RAIZ}/datos"; OUT = f"{RAIZ}/resultados"; os.makedirs(OUT, exist_ok=True)
AZUL, NARANJA, AQUA, AMAR, GRIS, GRISC, TXT, TXT2, SURF, CAFE = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#9a9893", "#d9d8d4", "#0b0b0b", "#52514e", "#fcfcfb", "#7a4a2a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRISC, "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": "#e8e7e3"})
X = f"{D}/fnc_precios_area_produccion_nov2026.xlsx"; INI = "1996-01"
def serie(hoja, nombre):
    s = pd.read_excel(X, sheet_name=hoja, header=None).iloc[6:, 3:5]; s.columns = ["mes", nombre]; s["mes"] = pd.to_datetime(s.mes, errors="coerce"); s[nombre] = pd.to_numeric(s[nombre], errors="coerce"); s = s.dropna()
    return s.set_index(s.mes.dt.to_period("M"))[nombre]
precio = serie("2. Precio Interno Mensual", "precio_carga"); prod = serie("8. Producción mensual", "sacos_miles")
# IPC: FRED (hasta 2025-04) empalmado con la serie DANE usada en proyectos anteriores (misma base); el último valor se mantiene para los meses sin dato
i1 = pd.read_csv(f"{D}/ipc_fred_1990_2025.csv"); i1.columns = ["f", "ipc"]; i1 = i1.set_index(pd.PeriodIndex(i1.f.str[:7], freq="M")).ipc
i2 = pd.read_csv(f"{D}/ipc_indice_2012_2026.csv"); i2 = i2.set_index(pd.PeriodIndex(i2.fecha, freq="M")).ipc
ipc = pd.concat([i1[i1.index < "2012-01"], i2]); ult = ipc.index.max(); BASE = ipc.iloc[-1]
m = pd.DataFrame({"precio_carga": precio, "sacos_miles": prod}).loc[INI:]; m["ipc"] = ipc.reindex(m.index).ffill(); m["defl"] = BASE / m.ipc
KG_CARGA = 125.0; VERDE_A_PERG = 1 / 0.8          # 1 kg de café verde equivale a 1,25 kg de pergamino seco
m["precio_kg"] = m.precio_carga / KG_CARGA; m["precio_kg_real"] = m.precio_kg * m.defl
m["kg_verde"] = m.sacos_miles * 1000 * 60; m["kg_pergamino"] = m.kg_verde * VERDE_A_PERG
m["valor_nominal"] = m.kg_pergamino * m.precio_kg; m["valor_real"] = m.valor_nominal * m.defl
m.index.name = "mes"; m.round(2).to_csv(f"{OUT}/cafe_mensual_1996_2026.csv")
a = m.groupby(m.index.year).agg(meses_precio=("precio_carga", "count"), meses_prod=("sacos_miles", "count"), precio_kg=("precio_kg", "mean"), precio_kg_real=("precio_kg_real", "mean"), sacos_miles=("sacos_miles", "sum"), kg_verde=("kg_verde", "sum"), kg_pergamino=("kg_pergamino", "sum"), valor_nominal=("valor_nominal", "sum"), valor_real=("valor_real", "sum"))
a["precio_kg_real_ponderado"] = a.valor_real / a.kg_pergamino
vc = pd.read_excel(X, sheet_name="9. Valor cosecha", header=None).iloc[6:, 1:3]; vc.columns = ["ano", "valor_fnc_millones"]; vc = vc.apply(pd.to_numeric, errors="coerce").dropna(); vc = vc.set_index(vc.ano.astype(int)).valor_fnc_millones
a["valor_fnc_nominal"] = vc.reindex(a.index) * 1e6; a["razon_calculado_fnc"] = a.valor_nominal / a.valor_fnc_nominal
ipc_a = ipc.groupby(ipc.index.year).mean(); a["valor_fnc_real"] = a.valor_fnc_nominal * BASE / ipc_a.reindex(a.index)
a.index.name = "ano"; a.round(3).to_csv(f"{OUT}/cafe_anual_1996_2026.csv")
pd.set_option("display.width", 250); print("IPC base:", ult, round(BASE, 2)); print(a[["meses_prod", "precio_kg", "precio_kg_real", "sacos_miles", "kg_verde", "valor_real", "valor_fnc_real", "razon_calculado_fnc"]].assign(kg_verde=lambda z: (z.kg_verde / 1e6).round(0), valor_real=lambda z: (z.valor_real / 1e12).round(2), valor_fnc_real=lambda z: (z.valor_fnc_real / 1e12).round(2)).round(2).to_string())
# ---------- municipios (EVA) ----------
e1 = pd.read_csv(f"{D}/eva_cafe_2007_2018.csv", dtype=str).rename(columns={"c_d_mun": "cod", "a_o": "ano", "producci_n_t": "prod_t", "rea_cosechada_ha": "area_ha", "departamento": "dep", "municipio": "mun"})
e2 = pd.read_csv(f"{D}/eva_cafe_2019_2025.csv", dtype=str).rename(columns={"c_digo_dane_municipio": "cod", "a_o": "ano", "producci_n": "prod_t", "rea_cosechada": "area_ha", "departamento": "dep", "municipio": "mun"})
e = pd.concat([e1[["cod", "dep", "mun", "ano", "prod_t", "area_ha"]], e2[["cod", "dep", "mun", "ano", "prod_t", "area_ha"]]]); e["cod"] = e.cod.str.zfill(5); e["ano"] = e.ano.astype(int)
for c in ["prod_t", "area_ha"]: e[c] = pd.to_numeric(e[c], errors="coerce").fillna(0)
e["dep"] = e.dep.str.upper(); e.to_csv(f"{OUT}/eva_cafe_municipal_2007_2025.csv", index=False)
r = e[e.ano >= 2021].groupby("cod").agg(prod_t=("prod_t", "sum"), area_ha=("area_ha", "sum"), dep=("dep", "last"), mun=("mun", "last")).reset_index(); r[["prod_t", "area_ha"]] /= 5; r["part_pct"] = r.prod_t / r.prod_t.sum() * 100
r = r.sort_values("prod_t", ascending=False); r["acum_pct"] = r.part_pct.cumsum(); r.round(2).to_csv(f"{OUT}/produccion_municipal_promedio_2021_2025.csv", index=False)
dp = r.groupby("dep").agg(prod_t=("prod_t", "sum"), area_ha=("area_ha", "sum"), municipios=("cod", "count")).sort_values("prod_t", ascending=False); dp["part_pct"] = dp.prod_t / dp.prod_t.sum() * 100; dp.round(1).to_csv(f"{OUT}/produccion_departamental_promedio_2021_2025.csv")
print(dp.head(12).round(1).to_string()); print(r.head(15)[["dep", "mun", "prod_t", "part_pct"]].round(2).to_string(index=False)); print("municipios productores:", (r.prod_t > 0).sum(), "| top 50 concentran", round(r.head(50).part_pct.sum(), 1), "% | top 100:", round(r.head(100).part_pct.sum(), 1))
d07 = e[e.ano.between(2007, 2011)].groupby("dep").prod_t.sum() / 5; cmpd = pd.DataFrame({"2007_2011": d07, "2021_2025": dp.prod_t}).fillna(0); cmpd["cambio_pct"] = (cmpd["2021_2025"] / cmpd["2007_2011"] - 1) * 100; cmpd.sort_values("2021_2025", ascending=False).round(1).to_csv(f"{OUT}/cambio_departamental.csv"); print(cmpd.sort_values("2021_2025", ascending=False).head(10).round(1).to_string())
comp = a[a.meses_prod == 12]; u = comp.iloc[-1]; mx = a.precio_kg_real.idxmax(); mn = a.precio_kg_real.idxmin(); ultm = m.dropna(subset=["precio_carga"]).iloc[-1]
res = dict(ipc_base=str(ult), precio_kg_real_ultimo_mes=dict(mes=str(m.dropna(subset=["precio_carga"]).index[-1]), nominal=float(ultm.precio_kg), real=float(ultm.precio_kg_real)), precio_kg_real_max=dict(ano=int(mx), valor=float(a.precio_kg_real[mx])), precio_kg_real_min=dict(ano=int(mn), valor=float(a.precio_kg_real[mn])), precio_kg_real_promedio_1996_2025=float(a.precio_kg_real.loc[:2025].mean()),
    ultimo_ano_completo=int(comp.index[-1]), kg_verde_ultimo=float(u.kg_verde), valor_real_ultimo=float(u.valor_real), valor_real_max=dict(ano=int(comp.valor_real.idxmax()), valor=float(comp.valor_real.max())), valor_real_min=dict(ano=int(comp.valor_real.idxmin()), valor=float(comp.valor_real.min())),
    prod_max=dict(ano=int(comp.kg_verde.idxmax()), kg=float(comp.kg_verde.max())), prod_min=dict(ano=int(comp.kg_verde.idxmin()), kg=float(comp.kg_verde.min())), valor_real_acumulado_1996_2025=float(comp.valor_real.loc[:2025].sum()), municipios_productores=int((r.prod_t > 0).sum()), top50_pct=float(r.head(50).part_pct.sum()))
json.dump(res, open(f"{OUT}/cafe_resumen.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(res, indent=1, ensure_ascii=False))
# ---------- Figura 1: precio, producción y valor ----------
mil = lambda v: f"{v:,.0f}".replace(",", "."); x = m.index.to_timestamp(); A = a[a.meses_prod == 12]; P26 = a.loc[[2026]] if 2026 in a.index and a.meses_prod[2026] < 12 else None
fig, axs = plt.subplots(3, 1, figsize=(13.4, 12.6), dpi=140); fig.subplots_adjust(left=0.08, right=0.975, top=0.885, bottom=0.075, hspace=0.42)
ax = axs[0]; ax.plot(x, m.precio_kg_real, color=CAFE, lw=1.6, label="Precio interno por kilo de pergamino seco, pesos de 2026"); ax.plot(x, m.precio_kg, color=GRIS, lw=1.1, label="Precio nominal"); ax.axhline(res["precio_kg_real_promedio_1996_2025"], color=TXT2, lw=.8, ls="--")
ax.text(x[2], res["precio_kg_real_promedio_1996_2025"] * 1.03, f"Promedio real 1996-2025: {mil(res['precio_kg_real_promedio_1996_2025'])} pesos", fontsize=9.5, color=TXT2)
pk = m.precio_kg_real.idxmax(); ax.annotate(f"{pk.strftime('%b %Y')}: {mil(m.precio_kg_real.max())}", (pk.to_timestamp(), m.precio_kg_real.max()), xytext=(-150, -4), textcoords="offset points", fontsize=9.5, color=CAFE)
ax.annotate(f"{m.dropna(subset=['precio_carga']).index[-1].strftime('%b %Y')}: {mil(ultm.precio_kg_real)}", (x[-1], ultm.precio_kg_real), xytext=(-40, -22), textcoords="offset points", fontsize=9.5, color=CAFE)
ax.set_ylabel("Pesos por kilo"); ax.legend(frameon=False, fontsize=9.5, loc="upper left"); ax.set_ylim(0, None); ax.set_title("1. Precio interno del café por kilo", loc="left", fontsize=12, color=TXT, pad=8)
ax = axs[1]; ax.bar(A.index, A.kg_verde / 1e6, color=AQUA, width=.72)
if P26 is not None: ax.bar(P26.index, P26.kg_verde / 1e6, color=AQUA, alpha=.35, width=.72); ax.text(2026, P26.kg_verde.iloc[0] / 1e6 + 12, f"{int(P26.meses_prod.iloc[0])} meses", ha="center", fontsize=8.5, color=TXT2)
for yv in [A.kg_verde.idxmax(), A.kg_verde.idxmin(), A.index[-1]]: ax.text(yv, A.kg_verde[yv] / 1e6 + 12, mil(A.kg_verde[yv] / 1e6), ha="center", fontsize=9, color=TXT)
ax.set_ylabel("Millones de kilogramos"); ax.set_xlim(1995.3, 2026.7); ax.grid(axis="x", visible=False); ax.set_title("2. Producción anual registrada, en millones de kilogramos de café verde", loc="left", fontsize=12, color=TXT, pad=8)
ax = axs[2]; ax.bar(A.index, A.valor_real / 1e12, color=NARANJA, width=.72, label="Valor de la cosecha en pesos de 2026 (producción × precio interno mensual)")
if P26 is not None: ax.bar(P26.index, P26.valor_real / 1e12, color=NARANJA, alpha=.35, width=.72)
ax.plot(A.index, A.valor_fnc_real / 1e12, color=TXT, lw=1.3, marker="o", ms=3, label="Valor de la cosecha publicado por la Federación, deflactado")
for yv in [A.valor_real.idxmax(), A.valor_real.idxmin(), A.index[-1]]: ax.text(yv, A.valor_real[yv] / 1e12 + .5, f"{A.valor_real[yv] / 1e12:.1f}".replace(".", ","), ha="center", fontsize=9, color=TXT)
ax.set_ylabel("Billones de pesos de 2026"); ax.set_xlim(1995.3, 2026.7); ax.grid(axis="x", visible=False); ax.legend(frameon=False, fontsize=9.5, loc="upper left"); ax.set_title("3. Valor real de la cosecha", loc="left", fontsize=12, color=TXT, pad=8)
fig.suptitle("Treinta años del café colombiano: 2025 fue el mejor año en precio y en valor, y 2026 ya devolvió una cuarta parte", x=0.012, y=0.975, ha="left", fontsize=15.5, color=TXT)
fig.text(0.012, 0.935, "Precio interno base de compra por kilo, producción registrada y valor de la cosecha, 1996-2026. Valores deflactados con el IPC a pesos de " + ("septiembre" if ult.month == 9 else str(ult)) + " de 2026.", fontsize=10.5, color=TXT2)
fig.text(0.012, 0.012, "Fuente: Elaboración propia con Federación Nacional de Cafeteros (precio interno base de compra por carga de 125 kg de pergamino seco, producción registrada en sacos de 60 kg de café verde, valor de la cosecha)\ne IPC (OCDE y DANE). El valor se calcula mes a mes convirtiendo el café verde a pergamino (1 kg verde = 1,25 kg pergamino). 2026 es parcial. Gustavo A Romero.", fontsize=8.5, color=TXT2)
fig.savefig(f"{RAIZ}/fig1_precio_produccion_valor.png"); plt.close(fig)
# ---------- Figura 2: mapa de calor municipal ----------
g = gpd.read_file(f"{D}/mpios_simplificado.geojson"); g["cod"] = g.mpio_cdpmp.astype(str).str.zfill(5); g = g.merge(r[["cod", "prod_t", "area_ha", "part_pct"]], on="cod", how="left"); g["prod_t"] = g.prod_t.fillna(0)
mp = g.copy(); mp["geometry"] = mp.buffer(0.012); dep = mp.dissolve("dpto_cnmbr").reset_index()[["dpto_cnmbr", "geometry"]]; dep["geometry"] = dep.buffer(-0.012)
cmap = LinearSegmentedColormap.from_list("c", ["#f3f2ee", "#f6e3c5", "#e8b96a", "#c98234", "#96531f", "#5a2d0c", "#2e1505"]); bounds = [0, 50, 500, 1500, 3000, 6000, 10000, 1e9]; norm = BoundaryNorm(bounds, cmap.N)
fig = plt.figure(figsize=(19.2, 10.4), dpi=100); ax = fig.add_axes([0.0, 0.155, 0.52, 0.72]); ax.set_axis_off()
g.plot(column="prod_t", cmap=cmap, norm=norm, ax=ax, edgecolor="none"); dep.boundary.plot(ax=ax, color="#6b6a66", linewidth=0.45); ax.set_xlim(-79.4, -71.2); ax.set_ylim(0.2, 11.6)
for _, q in r.head(6).iterrows():
    pt = g[g.cod == q.cod].geometry.iloc[0].representative_point(); ax.annotate(q.mun.title(), (pt.x, pt.y), xytext=(6, 2), textcoords="offset points", fontsize=9, color=TXT, path_effects=[pe.withStroke(linewidth=2.5, foreground=SURF)])
cax = fig.add_axes([0.07, 0.135, 0.38, 0.018]); cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=cax, orientation="horizontal", ticks=[0, 50, 500, 1500, 3000, 6000, 10000]); cb.set_ticklabels(["0", "50", "500", "1.500", "3.000", "6.000", "10.000"]); cb.outline.set_visible(False)
cb.set_label("Toneladas de café por año, promedio 2021-2025, por municipio", color=TXT2, fontsize=10)
ax2 = fig.add_axes([0.61, 0.50, 0.37, 0.34]); t = dp.head(10).iloc[::-1]; yy = np.arange(len(t)); ax2.barh(yy, t.prod_t / 1e3, color=CAFE, height=.66)
for yi, (v, pc) in enumerate(zip(t.prod_t / 1e3, t.part_pct)): ax2.text(v + 1.5, yi, f"{v:.0f} mil t · {pc:.0f} %", va="center", fontsize=9.5, color=TXT2)
ax2.set_yticks(yy); ax2.set_yticklabels([n.title().replace(" Del ", " del ").replace(" De ", " de ") for n in t.index]); ax2.grid(axis="y", visible=False); ax2.set_xlim(0, t.prod_t.max() / 1e3 * 1.3); ax2.set_xlabel("Miles de toneladas por año"); ax2.set_title(f"Diez departamentos concentran el {dp.head(10).part_pct.sum():.0f} % de la producción", loc="left", fontsize=12, color=TXT, pad=8)
ax3 = fig.add_axes([0.61, 0.14, 0.37, 0.27]); c2 = cmpd.sort_values("2021_2025", ascending=False).head(10).iloc[::-1]; yy = np.arange(len(c2)); ax3.barh(yy, c2.cambio_pct, color=[AQUA if v >= 0 else NARANJA for v in c2.cambio_pct], height=.66)
for yi, v in enumerate(c2.cambio_pct): ax3.text(v + (2 if v >= 0 else -2), yi, f"{v:+.0f} %", va="center", ha="left" if v >= 0 else "right", fontsize=9.5, color=TXT2)
ax3.set_yticks(yy); ax3.set_yticklabels([n.title().replace(" Del ", " del ").replace(" De ", " de ") for n in c2.index]); ax3.grid(axis="y", visible=False); ax3.axvline(0, color=TXT2, lw=.8); lim = max(abs(c2.cambio_pct.min()), c2.cambio_pct.max()) * 1.35; ax3.set_xlim(-lim, lim)
ax3.set_title("Cambio de la producción, 2007-2011 a 2021-2025", loc="left", fontsize=12, color=TXT, pad=8)
fig.text(0.012, 0.955, "Dónde se produce el café en Colombia: el mapa se corrió al sur", fontsize=22, color=TXT, va="center")
fig.text(0.012, 0.905, f"Producción de café por municipio, promedio anual 2021-2025. {res['municipios_productores']} municipios producen café; los 50 primeros concentran el {res['top50_pct']:.0f} % de la cosecha.", fontsize=12, color=TXT2, va="center")
fig.text(0.012, 0.03, "Fuente: Elaboración propia con las Evaluaciones Agropecuarias Municipales del Ministerio de Agricultura (datos.gov.co, 2007-2025) y el Marco Geoestadístico Nacional del DANE.\nLas evaluaciones municipales son estimaciones por consenso y su total nacional no coincide exactamente con la producción registrada por la Federación de Cafeteros. Gustavo A Romero.", fontsize=9.5, color=TXT2)
fig.savefig(f"{RAIZ}/fig2_mapa_produccion_municipal.png"); print("ok")
