"""
Generador del reporte HTML final. Un solo archivo, CSS y JS embebidos,
sin dependencias externas: se abre con doble clic en cualquier navegador,
sin servidor ni conexion a internet una vez generado.
"""
from datetime import datetime

SIN_DATO = "\u2014"

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
  margin: 0; padding: 24px; font-size: 16px;
}
h1 { font-size: 24px; margin: 0 0 4px 0; letter-spacing: 0.5px; }
.subtitulo { color: var(--text-dim); font-family: var(--mono); font-size: 13px; margin-bottom: 24px; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.tab { padding: 12px 20px; cursor: pointer; color: var(--text-dim); border-bottom: 2px solid transparent; font-weight: 600; font-size: 15px; }
.tab.activo { color: var(--accent); border-bottom-color: var(--accent); }
.panel { display: none; }
.panel.activo { display: block; }
.filtros {
  display: flex; gap: 12px; flex-wrap: wrap; align-items: center;
  background: var(--panel); border: 1px solid var(--border);
  padding: 14px; border-radius: 6px; margin-bottom: 16px;
}
.filtros input, .filtros select {
  background: var(--bg); color: var(--text); border: 1px solid var(--border);
  padding: 8px 12px; border-radius: 4px; font-family: var(--mono); font-size: 14px;
}
.contador { font-family: var(--mono); color: var(--text-dim); font-size: 13px; margin-bottom: 8px; }
table { width: 100%; border-collapse: collapse; font-size: 15px; }
th {
  text-align: left; padding: 10px 12px; background: var(--panel);
  border-bottom: 1px solid var(--border); color: var(--text-dim);
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
}
td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
tr:hover td { background: #1c2129; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-family: var(--mono); }
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
.form-buscar { display: flex; flex-direction: column; gap: 16px; max-width: 600px; }
.form-buscar label { font-size: 13px; color: var(--text-dim); display: block; margin-bottom: 6px; }
.form-buscar textarea {
  width: 100%; background: var(--panel); color: var(--text); border: 1px solid var(--border);
  padding: 10px; border-radius: 4px; font-family: var(--mono); font-size: 14px; min-height: 120px;
}
.form-buscar .fila-fechas { display: flex; gap: 12px; }
.form-buscar input[type="date"] {
  background: var(--panel); color: var(--text); border: 1px solid var(--border);
  padding: 8px 12px; border-radius: 4px; font-family: var(--mono); font-size: 14px;
}
.btn-primario {
  background: var(--accent); color: #0d1117; border: none; padding: 12px 24px;
  border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 14px; align-self: flex-start;
}
.btn-primario:hover { opacity: 0.9; }
.btn-primario:disabled { opacity: 0.5; cursor: wait; }
.estado-msg { font-family: var(--mono); font-size: 13px; color: var(--text-dim); }
.badge-nuevo { background: rgba(88,166,255,0.15); color: var(--accent); }
.badge-descartado { background: rgba(139,148,158,0.10); color: var(--text-dim); text-decoration: line-through; }
.badge-favorito { background: rgba(227,179,65,0.15); color: #e3b341; }
select.select-estado {
  background: var(--bg); color: var(--text); border: 1px solid var(--border);
  padding: 4px 8px; border-radius: 4px; font-family: var(--mono); font-size: 12px;
}
th.ordenable { cursor: pointer; user-select: none; }
th.ordenable:hover { color: var(--accent); }
"""

JS = """
function inicializarTab(nombreTab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('activo'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('activo'));
  document.querySelector(`[data-tab="${nombreTab}"]`).classList.add('activo');
  document.getElementById(`panel-${nombreTab}`).classList.add('activo');
}

let _ordenTablas = {};

function ordenarTabla(prefijo, campo) {
  if (!_ordenTablas[prefijo] || _ordenTablas[prefijo].campo !== campo) {
    _ordenTablas[prefijo] = {campo: campo, asc: true};
  } else {
    _ordenTablas[prefijo].asc = !_ordenTablas[prefijo].asc;
  }
  const factor = _ordenTablas[prefijo].asc ? 1 : -1;

  const tbody = document.querySelector(`#tabla-${prefijo} tbody`);
  const filas = Array.from(tbody.querySelectorAll('tr'));
  const atributo = campo === 'nombre' ? 'nombre' : campo === 'organismo' ? 'organismo'
    : campo === 'region' ? 'region' : campo === 'monto' ? 'monto' : 'cierre';

  filas.sort((a, b) => {
    let va = a.dataset[atributo] || '';
    let vb = b.dataset[atributo] || '';
    if (campo === 'monto') {
      return (parseFloat(va || 0) - parseFloat(vb || 0)) * factor;
    }
    va = va.toLowerCase();
    vb = vb.toLowerCase();
    if (va < vb) return -1 * factor;
    if (va > vb) return 1 * factor;
    return 0;
  });

  filas.forEach(fila => tbody.appendChild(fila));
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

function aplicarPreset(prefijo, valor) {
  document.getElementById(`${prefijo}-buscar`).value = valor;
  filtrarTabla(prefijo);
}

async function toggleFavorito(boton) {
  const codigo = boton.dataset.codigo;
  const tabla = boton.dataset.tabla;
  const nuevoEstado = boton.textContent.trim() !== '\u2605';
  try {
    const resp = await fetch('/api/estado', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({codigo: codigo, tabla: tabla, estado: nuevoEstado ? 'favorito' : 'visto'})
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

// ---- Tab Buscar ----
async function cargarKeywordsEnFormulario() {
  const resp = await fetch('/api/keywords');
  const data = await resp.json();
  document.getElementById('buscar-keywords').value = data.keywords.join('\\n');
}

async function dispararBusqueda(continuar) {
  const botonBuscar = document.getElementById('buscar-boton');
  const botonContinuar = document.getElementById('continuar-boton');
  const msg = document.getElementById('buscar-mensaje');
  const keywords = document.getElementById('buscar-keywords').value
    .split('\\n').map(k => k.trim()).filter(k => k.length > 0);

  botonBuscar.disabled = true;
  botonContinuar.disabled = true;
  msg.textContent = 'Iniciando...';

  const cuerpo = {keywords: keywords};
  if (continuar) {
    cuerpo.continuar = true;
  } else {
    const fechaDesde = document.getElementById('buscar-fecha-desde').value;
    const fechaHasta = document.getElementById('buscar-fecha-hasta').value;
    cuerpo.fecha_desde = fechaDesde ? fechaDesde + 'T00:00:00' : null;
    cuerpo.fecha_hasta = fechaHasta ? fechaHasta + 'T23:59:59' : null;
  }

  try {
    const resp = await fetch('/api/buscar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(cuerpo)
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'error desconocido');
    if (continuar && data.fecha_desde) {
      msg.textContent = `Continuando desde ${data.fecha_desde.slice(0,10)} hasta ${data.fecha_hasta.slice(0,10)}...`;
    }

    const intervalo = setInterval(async () => {
      const r = await fetch('/api/progreso');
      const p = await r.json();
      const minutos = Math.floor(p.segundos / 60);
      const segundos = p.segundos % 60;
      const tiempo = minutos > 0 ? `${minutos}m ${segundos}s` : `${segundos}s`;
      msg.textContent = `${p.mensaje} (${tiempo})`;

      if (!p.activo) {
        clearInterval(intervalo);
        if (p.error) {
          msg.textContent = 'Error: ' + p.error;
          botonBuscar.disabled = false;
          botonContinuar.disabled = false;
        } else {
          msg.textContent = 'Listo. Recargando...';
          setTimeout(() => window.location.reload(), 600);
        }
      }
    }, 1200);
  } catch (e) {
    msg.textContent = 'Error: ' + e.message;
    botonBuscar.disabled = false;
    botonContinuar.disabled = false;
  }
}

// ---- Tab Historial + Tab Favoritos (comparten los mismos datos) ----
let _historialCompleto = [];
let _ordenActual = {campo: null, asc: true};

async function cargarHistorial() {
  const resp = await fetch('/api/historial');
  const data = await resp.json();
  _historialCompleto = data.items;
  filtrarHistorial();
  renderizarFavoritos();
}

function cargarFavoritosTab() {
  if (_historialCompleto.length === 0) {
    cargarHistorial();
  } else {
    renderizarFavoritos();
  }
}

function ordenarPor(campo) {
  if (_ordenActual.campo === campo) {
    _ordenActual.asc = !_ordenActual.asc;
  } else {
    _ordenActual = {campo: campo, asc: true};
  }
  const factor = _ordenActual.asc ? 1 : -1;
  _historialCompleto.sort((a, b) => {
    let va = a[campo], vb = b[campo];
    if (campo === 'monto') {
      va = parseFloat(va) || 0;
      vb = parseFloat(vb) || 0;
      return (va - vb) * factor;
    }
    va = (va || '').toString().toLowerCase();
    vb = (vb || '').toString().toLowerCase();
    if (va < vb) return -1 * factor;
    if (va > vb) return 1 * factor;
    return 0;
  });
  filtrarHistorial();
  renderizarFavoritos();
}

function filtrarHistorial() {
  const texto = (document.getElementById('historial-buscar').value || '').toLowerCase();
  const filtrados = _historialCompleto.filter(item => (item.nombre || '').toLowerCase().includes(texto));
  renderizarFilas(filtrados, 'historial-cuerpo', true);
  document.getElementById('historial-contador').textContent = `${filtrados.length} de ${_historialCompleto.length} items en el historial`;
}

function renderizarFavoritos() {
  const favoritos = _historialCompleto.filter(item => item.estado_item === 'favorito');
  renderizarFilas(favoritos, 'favoritos-cuerpo', false);
  document.getElementById('favoritos-contador').textContent = `${favoritos.length} favoritos`;
}

function formatearMonto(monto) {
  if (!monto) return '\u2014';
  return '$' + Math.round(monto).toLocaleString('es-CL');
}

function renderizarFilas(items, cuerpoId, conCheckboxYEstado) {
  const cuerpo = document.getElementById(cuerpoId);
  cuerpo.innerHTML = '';

  items.forEach(item => {
    const badgeClase = item.estado_item === 'favorito' ? 'badge-favorito'
      : item.estado_item === 'descartado' ? 'badge-descartado'
      : item.estado_item === 'nuevo' ? 'badge-nuevo' : 'badge-otro';
    const fila = document.createElement('tr');
    fila.dataset.codigo = item.codigo;
    fila.dataset.tabla = item.tabla;

    const columnaCheckbox = conCheckboxYEstado ? `<td><input type="checkbox" class="chk-historial"></td>` : '';
    const columnaEstado = conCheckboxYEstado ? `<td><span class="badge ${badgeClase}">${item.estado_item}</span></td>` : '';

    fila.innerHTML = `
      ${columnaCheckbox}
      <td><a href="${item.url}" target="_blank">${item.codigo}</a></td>
      <td>${item.nombre}</td>
      <td>${item.organismo}</td>
      <td>${item.region || '\u2014'}</td>
      <td>${item.fecha_cierre || '\u2014'}</td>
      <td class="monto">${formatearMonto(item.monto)}</td>
      ${columnaEstado}
      <td>${item.tabla === 'licitaciones' ? 'Licitacion' : 'Compra Agil'}</td>
      <td>
        <button class="btn-fav" title="Favorito" onclick="cambiarEstadoHistorial('${item.codigo}', '${item.tabla}', 'favorito')">\u2605</button>
        <button class="btn-fav" title="Marcar visto" onclick="cambiarEstadoHistorial('${item.codigo}', '${item.tabla}', 'visto')">\U0001F441</button>
        <button class="btn-fav" title="Descartar" onclick="cambiarEstadoHistorial('${item.codigo}', '${item.tabla}', 'descartado')">\U0001F5D1</button>
      </td>
    `;
    cuerpo.appendChild(fila);
  });
}

async function cambiarEstadoHistorial(codigo, tabla, nuevoEstado) {
  await fetch('/api/estado', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({codigo: codigo, tabla: tabla, estado: nuevoEstado})
  });
  await cargarHistorial();
}

function toggleSeleccionarTodos(checkbox) {
  document.querySelectorAll('.chk-historial').forEach(c => c.checked = checkbox.checked);
}

async function aplicarEstadoMasivo(nuevoEstado) {
  const filas = document.querySelectorAll('#historial-cuerpo tr');
  const seleccionadas = Array.from(filas).filter(fila => fila.querySelector('.chk-historial').checked);
  if (seleccionadas.length === 0) {
    alert('No hay items seleccionados. Marca las casillas de las filas que quieres cambiar.');
    return;
  }
  for (const fila of seleccionadas) {
    await fetch('/api/estado', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({codigo: fila.dataset.codigo, tabla: fila.dataset.tabla, estado: nuevoEstado})
    });
  }
  await cargarHistorial();
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
    region = comprador.get("RegionUnidad", "")
    estado = lic.get("Estado", "")
    fecha_cierre = lic.get("FechaCierre", "")
    monto = lic.get("MontoEstimado")
    url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"
    es_favorito = codigo in favoritos
    estrella = "\u2605" if es_favorito else "\u2606"

    return (
        f'<tr data-nombre="{nombre}" data-organismo="{organismo}" data-monto="{monto or 0}" '
        f'data-cierre="{fecha_cierre}" data-region="{region}" '
        f'data-favorito="{"true" if es_favorito else "false"}">'
        f'<td><button class="btn-fav" data-codigo="{codigo}" data-tabla="licitaciones" onclick="toggleFavorito(this)">{estrella}</button></td>'
        f'<td><a href="{url}" target="_blank">{codigo}</a></td>'
        f'<td>{nombre}</td>'
        f'<td>{organismo}</td>'
        f'<td>{region or SIN_DATO}</td>'
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
    region = institucion.get("nombre_region", "")
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
        f'data-cierre="{fecha_cierre}" data-region="{region}" '
        f'data-favorito="{"true" if es_favorito else "false"}">'
        f'<td><button class="btn-fav" data-codigo="{codigo}" data-tabla="compra_agil" onclick="toggleFavorito(this)">{estrella}</button></td>'
        f'<td><a href="{url}" target="_blank">{codigo}</a></td>'
        f'<td>{nombre}</td>'
        f'<td>{organismo}</td>'
        f'<td>{region or SIN_DATO}</td>'
        f'<td><span class="badge badge-otro">{estado}</span></td>'
        f'<td>{fecha_cierre}</td>'
        f'<td class="monto">{_formatear_monto(monto)}</td>'
        f'</tr>'
    )


def _tabla(prefijo: str, filas_html: str, organismos: list, keywords: list = None) -> str:
    opciones = "".join(f'<option value="{o}">{o}</option>' for o in sorted(set(organismos)) if o)
    filas_html = filas_html or '<tr><td colspan="8" class="vacio">Sin resultados.</td></tr>'
    keywords = keywords or []
    presets_html = "".join(
        f'<button type="button" class="btn-primario" style="padding:5px 12px;font-size:12px;" '
        f'onclick="aplicarPreset(\'{prefijo}\', \'{kw}\')">{kw}</button>'
        for kw in keywords
    )

    return f"""
    <div class="filtros">
      <input id="{prefijo}-buscar" type="text" placeholder="Buscar por nombre..." oninput="filtrarTabla('{prefijo}')">
      <input id="{prefijo}-monto-min" type="number" placeholder="Monto minimo CLP" oninput="filtrarTabla('{prefijo}')">
      <select id="{prefijo}-organismo" onchange="filtrarTabla('{prefijo}')">
        <option value="">Todos los organismos</option>
        {opciones}
      </select>
      <label class="chk"><input type="checkbox" id="{prefijo}-solo-favoritos" onchange="filtrarTabla('{prefijo}')"> Solo favoritos</label>
      {presets_html}
    </div>
    <div class="contador" id="{prefijo}-contador"></div>
    <table id="tabla-{prefijo}">
      <thead><tr>
        <th>\u2605</th>
        <th>Codigo</th>
        <th class="ordenable" onclick="ordenarTabla('{prefijo}', 'nombre')">Nombre \u2195</th>
        <th class="ordenable" onclick="ordenarTabla('{prefijo}', 'organismo')">Organismo \u2195</th>
        <th class="ordenable" onclick="ordenarTabla('{prefijo}', 'region')">Region \u2195</th>
        <th>Estado</th>
        <th class="ordenable" onclick="ordenarTabla('{prefijo}', 'cierre')">Cierre \u2195</th>
        <th class="ordenable" onclick="ordenarTabla('{prefijo}', 'monto')">Monto \u2195</th>
      </tr></thead>
      <tbody>{filas_html}</tbody>
    </table>
    """


def generar_reporte(licitaciones_filtradas, compra_agil_todas, keywords, ruta_salida, favoritos=None):
    """
    Genera el archivo HTML final con las pestanas: Buscar, Licitaciones
    (filtradas por habilidad), Compra Agil (todo, con presets de busqueda
    rapida), Favoritos e Historial.

    Compra Agil ya no tiene una pestana separada "por habilidad": en la
    practica mostraba casi lo mismo que "Todo", asi que se unificaron y
    el filtrado por keyword ahora es un preset rapido dentro de la misma
    tabla, no una consulta aparte a la API.

    favoritos: dict {codigo: True}, calculado a partir del almacen (estado == 'favorito').
    """
    favoritos = favoritos or {}

    filas_lic = "".join(_fila_licitacion(l, favoritos) for l in licitaciones_filtradas)
    filas_ca_todas = "".join(_fila_compra_agil(c, favoritos) for c in compra_agil_todas)

    organismos_lic = [l.get("NombreOrganismo", "") for l in licitaciones_filtradas]
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
    <div class="tab activo" data-tab="buscar" onclick="inicializarTab('buscar'); cargarKeywordsEnFormulario();">Buscar</div>
    <div class="tab" data-tab="lic" onclick="inicializarTab('lic')">Licitaciones - Por habilidad ({len(licitaciones_filtradas)})</div>
    <div class="tab" data-tab="ca-todas" onclick="inicializarTab('ca-todas')">Compra Agil ({len(compra_agil_todas)})</div>
    <div class="tab" data-tab="favoritos" onclick="inicializarTab('favoritos'); cargarFavoritosTab();">\u2605 Favoritos</div>
    <div class="tab" data-tab="historial" onclick="inicializarTab('historial'); cargarHistorial();">Historial</div>
  </div>

  <div class="panel activo" id="panel-buscar">
    <div class="form-buscar">
      <div>
        <label>Palabras clave (una por linea)</label>
        <textarea id="buscar-keywords"></textarea>
      </div>
      <div class="fila-fechas">
        <div>
          <label>Rango historico desde (opcional, para Licitaciones, maximo 31 dias)</label>
          <input type="date" id="buscar-fecha-desde">
        </div>
        <div>
          <label>hasta</label>
          <input type="date" id="buscar-fecha-hasta">
        </div>
      </div>
      <button class="btn-primario" id="buscar-boton" onclick="dispararBusqueda(false)">Buscar ahora</button>
      <button class="btn-primario" id="continuar-boton" onclick="dispararBusqueda(true)" style="background: var(--text-dim);">
        \u23e9 Continuar poblacion historica (siguientes 31 dias hacia atras)
      </button>
      <div class="estado-msg" id="buscar-mensaje"></div>
    </div>
  </div>

  <div class="panel" id="panel-lic">{_tabla("lic", filas_lic, organismos_lic, keywords)}</div>
  <div class="panel" id="panel-ca-todas">{_tabla("ca-todas", filas_ca_todas, organismos_ca_todas, keywords)}</div>

  <div class="panel" id="panel-favoritos">
    <div class="contador" id="favoritos-contador"></div>
    <table id="tabla-favoritos">
      <thead><tr>
        <th>Codigo</th>
        <th class="ordenable" onclick="ordenarPor('nombre')">Nombre \u2195</th>
        <th>Organismo</th>
        <th class="ordenable" onclick="ordenarPor('region')">Region \u2195</th>
        <th class="ordenable" onclick="ordenarPor('fecha_cierre')">Cierre \u2195</th>
        <th class="ordenable" onclick="ordenarPor('monto')">Monto \u2195</th>
        <th>Fuente</th><th>Acciones</th>
      </tr></thead>
      <tbody id="favoritos-cuerpo"></tbody>
    </table>
  </div>

  <div class="panel" id="panel-historial">
    <div class="filtros">
      <input id="historial-buscar" type="text" placeholder="Buscar por nombre..." oninput="filtrarHistorial()">
      <label class="chk"><input type="checkbox" id="historial-seleccionar-todos" onchange="toggleSeleccionarTodos(this)"> Seleccionar todos</label>
      <button class="btn-primario" onclick="aplicarEstadoMasivo('favorito')" style="padding:6px 14px;">\u2605 Marcar</button>
      <button class="btn-primario" onclick="aplicarEstadoMasivo('visto')" style="padding:6px 14px; background: var(--text-dim);">\U0001F441 Visto</button>
      <button class="btn-primario" onclick="aplicarEstadoMasivo('descartado')" style="padding:6px 14px; background: #8b949e;">\U0001F5D1 Descartar</button>
    </div>
    <div class="contador" id="historial-contador"></div>
    <table id="tabla-historial">
      <thead><tr>
        <th></th>
        <th>Codigo</th>
        <th class="ordenable" onclick="ordenarPor('nombre')">Nombre \u2195</th>
        <th>Organismo</th>
        <th class="ordenable" onclick="ordenarPor('region')">Region \u2195</th>
        <th class="ordenable" onclick="ordenarPor('fecha_cierre')">Cierre \u2195</th>
        <th class="ordenable" onclick="ordenarPor('monto')">Monto \u2195</th>
        <th>Estado</th><th>Fuente</th><th>Acciones</th>
      </tr></thead>
      <tbody id="historial-cuerpo"></tbody>
    </table>
  </div>

  <script>{JS}
    ['lic', 'ca-todas'].forEach(p => filtrarTabla(p));
    cargarKeywordsEnFormulario();
  </script>
</body>
</html>"""

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html)
