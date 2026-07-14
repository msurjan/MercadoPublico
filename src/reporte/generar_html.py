"""
Generador del reporte HTML final. Un solo archivo, CSS y JS embebidos,
sin dependencias externas: se abre con doble clic en cualquier navegador,
sin servidor ni conexion a internet una vez generado.
"""
from datetime import datetime

CSS = """
:root {
  --bg: #0d1117;
  --panel: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --text-dim: #8b949e;
  --accent: #58a6ff;
  --ok: #3fb950;
  --mono: 'Consolas', 'SF Mono', monospace;
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--text);
  font-family: 'Segoe UI', system-ui, sans-serif;
  margin: 0; padding: 24px; font-size: 14px;
}
h1 { font-size: 20px; margin: 0 0 4px 0; letter-spacing: 0.5px; }
.subtitulo { color: var(--text-dim); font-family: var(--mono); font-size: 12px; margin-bottom: 24px; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.tab { padding: 10px 18px; cursor: pointer; color: var(--text-dim); border-bottom: 2px solid transparent; font-weight: 600; }
.tab.activo { color: var(--accent); border-bottom-color: var(--accent); }
.panel { display: none; }
.panel.activo { display: block; }
.filtros {
  display: flex; gap: 12px; flex-wrap: wrap; align-items: center;
  background: var(--panel); border: 1px solid var(--border);
  padding: 12px; border-radius: 6px; margin-bottom: 16px;
}
.filtros input, .filtros select {
  background: var(--bg); color: var(--text); border: 1px solid var(--border);
  padding: 6px 10px; border-radius: 4px; font-family: var(--mono); font-size: 12px;
}
.contador { font-family: var(--mono); color: var(--text-dim); font-size: 12px; margin-bottom: 8px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
  text-align: left; padding: 8px 10px; background: var(--panel);
  border-bottom: 1px solid var(--border); color: var(--text-dim);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
}
td { padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
tr:hover td { background: #1c2129; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-family: var(--mono); }
.badge-abierta { background: rgba(63,185,80,0.15); color: var(--ok); }
.badge-otro { background: rgba(139,148,158,0.15); color: var(--text-dim); }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.monto { font-family: var(--mono); text-align: right; }
.vacio { color: var(--text-dim); font-style: italic; padding: 24px; text-align: center; }
.btn-fav {
  background: none; border: none; cursor: pointer; font-size: 16px;
  color: var(--text-dim); padding: 2px 4px;
}
.btn-fav:hover { color: #e3b341; }
label.chk { display: flex; align-items: center; gap: 6px; font-family: var(--mono); font-size: 12px; color: var(--text-dim); }
"""

JS = """
function inicializarTab(nombreTab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('activo'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('activo'));
  document.querySelector(`[data-tab="${nombreTab}"]`).classList.add('activo');
  document.getElementById(`panel-${nombreTab}`).classList.add('activo');
}

function filtrarTabla(prefijo) {
  const texto = (document.getElementById(`${prefijo}-buscar`).value || '').toLowerCase();
  const montoMin = parseFloat(document.getElementById(`${prefijo}-monto-min`).value) || 0;
  const organismo = document.getElementById(`${prefijo}-organismo`).value;
  const soloFavEl = document.getElementById(`${prefijo}-solo-favoritos`);
  const soloFavoritos = soloFavEl && soloFavEl.checked;

  const filas = document.querySelectorAll(`#tabla-${prefijo} tbody tr`);
  let visibles = 0;
  filas.forEach(fila => {
    const nombre = (fila.dataset.nombre || '').toLowerCase();
    const org = fila.dataset.organismo || '';
    const monto = parseFloat(fila.dataset.monto) || 0;
    const esFavorito = fila.dataset.favorito === 'true';

    const pasaTexto = !texto || nombre.includes(texto);
    const pasaMonto = monto >= montoMin;
    const pasaOrganismo = !organismo || org === organismo;
    const pasaFavorito = !soloFavoritos || esFavorito;

    const visible = pasaTexto && pasaMonto && pasaOrganismo && pasaFavorito;
    fila.style.display = visible ? '' : 'none';
    if (visible) visibles++;
  });
  document.getElementById(`${prefijo}-contador`).textContent = `${visibles} de ${filas.length} resultados`;
}

async function toggleFavorito(boton) {
  const codigo = boton.dataset.codigo;
  const nuevoEstado = boton.textContent.trim() !== '\u2605';
  try {
    const resp = await fetch('/api/favorito', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({codigo: codigo, favorito: nuevoEstado})
    });
    if (!resp.ok) throw new Error('respuesta no OK');
    boton.textContent = nuevoEstado ? '\u2605' : '\u2606';
    boton.closest('tr').dataset.favorito = nuevoEstado ? 'true' : 'false';
    const prefijo = boton.closest('table').id.replace('tabla-', '');
    filtrarTabla(prefijo);
  } catch (e) {
    alert('No se pudo guardar el favorito. ¿Sigue abierta la ventana del programa (la consola negra)?');
  }
}
"""


def _formatear_monto(valor) -> str:
    if valor is None:
        return "\u2014"
    try:
        return "$" + f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "\u2014"


def _fila_licitacion(lic: dict, favoritos: dict) -> str:
    codigo = lic.get("CodigoExterno", "")
    nombre = lic.get("Nombre", "(sin nombre)")
    comprador = lic.get("Comprador") or {}
    organismo = lic.get("NombreOrganismo", "") or comprador.get("NombreOrganismo", "")
    estado = lic.get("Estado", "")
    fecha_cierre = lic.get("FechaCierre", "")
    monto = lic.get("MontoEstimado")
    url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"
    es_favorito = codigo in favoritos
    estrella = "\u2605" if es_favorito else "\u2606"

    return (
        f'<tr data-nombre="{nombre}" data-organismo="{organismo}" data-monto="{monto or 0}" '
        f'data-favorito="{"true" if es_favorito else "false"}">'
        f'<td><button class="btn-fav" data-codigo="{codigo}" onclick="toggleFavorito(this)">{estrella}</button></td>'
        f'<td><a href="{url}" target="_blank">{codigo}</a></td>'
        f'<td>{nombre}</td>'
        f'<td>{organismo}</td>'
        f'<td><span class="badge badge-abierta">{estado}</span></td>'
        f'<td>{fecha_cierre}</td>'
        f'<td class="monto">{_formatear_monto(monto)}</td>'
        f'</tr>'
    )


def _fila_compra_agil(ca: dict, favoritos: dict) -> str:
    codigo = ca.get("codigo", "")
    nombre = ca.get("nombre", "(sin nombre)")
    institucion = ca.get("institucion") or {}
    organismo = institucion.get("organismo_comprador", "")
    montos = ca.get("montos") or {}
    monto = montos.get("monto_disponible_clp") or montos.get("monto_disponible")
    estado_raw = ca.get("estado")
    estado = estado_raw.get("glosa", "") if isinstance(estado_raw, dict) else (estado_raw or "")
    fechas = ca.get("fechas") or {}
    fecha_cierre = fechas.get("fecha_cierre", "")
    url = f"https://compra-agil.mercadopublico.cl/resumen-cotizacion/{codigo}"
    es_favorito = codigo in favoritos
    estrella = "\u2605" if es_favorito else "\u2606"

    return (
        f'<tr data-nombre="{nombre}" data-organismo="{organismo}" data-monto="{monto or 0}" '
        f'data-favorito="{"true" if es_favorito else "false"}">'
        f'<td><button class="btn-fav" data-codigo="{codigo}" onclick="toggleFavorito(this)">{estrella}</button></td>'
        f'<td><a href="{url}" target="_blank">{codigo}</a></td>'
        f'<td>{nombre}</td>'
        f'<td>{organismo}</td>'
        f'<td><span class="badge badge-otro">{estado}</span></td>'
        f'<td>{fecha_cierre}</td>'
        f'<td class="monto">{_formatear_monto(monto)}</td>'
        f'</tr>'
    )


def _tabla(prefijo: str, filas_html: str, organismos: list) -> str:
    opciones = "".join(f'<option value="{o}">{o}</option>' for o in sorted(set(organismos)) if o)
    filas_html = filas_html or '<tr><td colspan="7" class="vacio">Sin resultados.</td></tr>'

    return f"""
    <div class="filtros">
      <input id="{prefijo}-buscar" type="text" placeholder="Buscar por nombre..." oninput="filtrarTabla('{prefijo}')">
      <input id="{prefijo}-monto-min" type="number" placeholder="Monto minimo CLP" oninput="filtrarTabla('{prefijo}')">
      <select id="{prefijo}-organismo" onchange="filtrarTabla('{prefijo}')">
        <option value="">Todos los organismos</option>
        {opciones}
      </select>
      <label class="chk"><input type="checkbox" id="{prefijo}-solo-favoritos" onchange="filtrarTabla('{prefijo}')"> Solo favoritos</label>
    </div>
    <div class="contador" id="{prefijo}-contador"></div>
    <table id="tabla-{prefijo}">
      <thead><tr><th>\u2605</th><th>Codigo</th><th>Nombre</th><th>Organismo</th><th>Estado</th><th>Cierre</th><th>Monto</th></tr></thead>
      <tbody>{filas_html}</tbody>
    </table>
    """


def generar_reporte(licitaciones_filtradas, compra_agil_filtrada, compra_agil_todas, keywords, ruta_salida, favoritos=None):
    """
    Genera el archivo HTML final con 3 pestanas:
    - Licitaciones que coinciden con tus habilidades (Motor 1).
    - Compra Agil que coincide con tus habilidades (Motor 1, via q=).
    - Compra Agil completa sin filtrar, con filtros interactivos (Motor 2).

    favoritos: dict {codigo: True} cargado desde data/favoritos.json.
    """
    favoritos = favoritos or {}

    filas_lic = "".join(_fila_licitacion(l, favoritos) for l in licitaciones_filtradas)
    filas_ca_match = "".join(_fila_compra_agil(c, favoritos) for c in compra_agil_filtrada)
    filas_ca_todas = "".join(_fila_compra_agil(c, favoritos) for c in compra_agil_todas)

    organismos_lic = [l.get("NombreOrganismo", "") for l in licitaciones_filtradas]
    organismos_ca_match = [(c.get("institucion") or {}).get("organismo_comprador", "") for c in compra_agil_filtrada]
    organismos_ca_todas = [(c.get("institucion") or {}).get("organismo_comprador", "") for c in compra_agil_todas]

    ahora = datetime.now().strftime("%d-%m-%Y %H:%M")
    keywords_str = ", ".join(keywords)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Buscador Mercado Publico</title>
<style>{CSS}</style>
</head>
<body>
  <h1>BUSCADOR MERCADO PUBLICO</h1>
  <div class="subtitulo">Generado {ahora} | Keywords activas: {keywords_str}</div>

  <div class="tabs">
    <div class="tab activo" data-tab="lic" onclick="inicializarTab('lic')">Licitaciones - Por habilidad ({len(licitaciones_filtradas)})</div>
    <div class="tab" data-tab="ca-match" onclick="inicializarTab('ca-match')">Compra Agil - Por habilidad ({len(compra_agil_filtrada)})</div>
    <div class="tab" data-tab="ca-todas" onclick="inicializarTab('ca-todas')">Compra Agil - Todo ({len(compra_agil_todas)})</div>
  </div>

  <div class="panel activo" id="panel-lic">{_tabla("lic", filas_lic, organismos_lic)}</div>
  <div class="panel" id="panel-ca-match">{_tabla("ca-match", filas_ca_match, organismos_ca_match)}</div>
  <div class="panel" id="panel-ca-todas">{_tabla("ca-todas", filas_ca_todas, organismos_ca_todas)}</div>

  <script>{JS}
    ['lic', 'ca-match', 'ca-todas'].forEach(p => filtrarTabla(p));
  </script>
</body>
</html>"""

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html)
