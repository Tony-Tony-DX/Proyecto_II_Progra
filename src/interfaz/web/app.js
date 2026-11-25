/* Interfaz gráfica – Sistema de Análisis y Optimización de Redes Financieras. */
"use strict";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ================================================================ utilidades */
async function api(ruta, datos) {
  const opciones = datos === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos),
  };
  const r = await fetch("/api/" + ruta, opciones);
  const json = await r.json();
  if (!r.ok) { aviso(json.error || "Error", true); throw new Error(json.error); }
  return json;
}

let temporizadorAviso;
function aviso(texto, error = false) {
  const el = $("#aviso");
  el.textContent = texto;
  el.className = "aviso-flotante visible" + (error ? " error" : "");
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => el.classList.remove("visible"), error ? 5000 : 2600);
}

const fmt = (n, dec = 0) => n === null || n === undefined ? "∞"
  : Number(n).toLocaleString("es-PE", { minimumFractionDigits: dec, maximumFractionDigits: dec });
const soles = (n, dec = 2) => n === null || n === undefined ? "—" : "S/ " + fmt(n, dec);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const cargando = (el, texto = "Calculando…") => { el.innerHTML = `<div class="cargando">${texto}</div>`; };
const chips = (ids, clase = "") => ids.map(i => `<span class="insignia ${clase}">${esc(i)}</span>`).join(" ");
const camino = (ids) => ids.map(esc).join(' <span class="tenue">→</span> ');

function leerAtributos(texto) {
  const salida = {};
  for (const parte of texto.split(",")) {
    const [k, ...v] = parte.split("=");
    if (!k.trim() || !v.length) continue;
    const valor = v.join("=").trim();
    salida[k.trim()] = valor !== "" && !isNaN(Number(valor)) ? Number(valor) : valor;
  }
  return salida;
}

function kpi(valor, etiqueta, detalle = "", clase = "") {
  return `<div class="tarjeta kpi ${clase}"><div class="etiqueta">${etiqueta}</div>
    <div class="valor">${valor}</div><div class="detalle">${detalle}</div></div>`;
}

/* Componentes genéricos: pestañas y botones segmentados */
const alCambiarPestana = {};
function activarPestana(grupo, tab) {
  const barra = $(`.pestanas[data-grupo="${grupo}"]`);
  $$("button", barra).forEach(b => b.classList.toggle("activo", b.dataset.tab === tab));
  $$(`[data-panel^="${grupo}:"]`).forEach(p => { p.hidden = p.dataset.panel !== `${grupo}:${tab}`; });
  if (alCambiarPestana[grupo]) alCambiarPestana[grupo](tab);
}
document.addEventListener("click", e => {
  const b = e.target.closest(".pestanas button");
  if (b) activarPestana(b.parentElement.dataset.grupo, b.dataset.tab);
});

function segmentado(id, alCambiar) {
  const cont = $("#" + id);
  cont.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    $$("button", cont).forEach(x => x.classList.toggle("activo", x === b));
    alCambiar(b.dataset.v);
  });
  return {
    valor: () => $("button.activo", cont).dataset.v,
    fijar: (v) => $$("button", cont).forEach(x => x.classList.toggle("activo", x.dataset.v === v)),
  };
}

/* ================================================================ navegación */
const TITULOS = {
  inicio: "Inicio", red: "Módulo 1 · Gestión y modelamiento de la red",
  fraude: "Módulo 2 · Análisis de transacciones y detección de operaciones sospechosas",
  rutas: "Módulo 3 · Enrutamiento de operaciones y cálculo de comisiones",
  liquidez: "Módulo 4 · Planificación de la distribución de liquidez",
  evaluacion: "Módulo 5 · Evaluación, comparación y validación",
  animacion: "Algoritmos en acción · paso a paso", sustentacion: "Sustentación técnica",
  reportes: "Reportes",
};
const iniciadas = new Set();
const INICIAR = {};

async function ir(pagina) {
  $$(".nav-item").forEach(b => b.classList.toggle("activo", b.dataset.ir === pagina));
  $$(".pagina").forEach(p => p.classList.toggle("activa", p.id === "p-" + pagina));
  $("#titulo-pagina").textContent = TITULOS[pagina];
  window.scrollTo({ top: 0 });
  if (!iniciadas.has(pagina) && INICIAR[pagina]) {
    iniciadas.add(pagina);
    await INICIAR[pagina]();
  }
}
$$(".nav-item").forEach(b => b.addEventListener("click", () => ir(b.dataset.ir)));

/* Preferencias de presentación */
function preferencia(clave, valor) {
  try { if (valor === undefined) return localStorage.getItem(clave); localStorage.setItem(clave, valor); }
  catch (e) { return null; }
}
if (preferencia("tema") === "oscuro") document.documentElement.dataset.tema = "oscuro";
if (preferencia("expo") === "1") document.documentElement.classList.add("expo");
$("#btn-tema").addEventListener("click", () => {
  const oscuro = document.documentElement.dataset.tema !== "oscuro";
  document.documentElement.dataset.tema = oscuro ? "oscuro" : "";
  preferencia("tema", oscuro ? "oscuro" : "claro");
});
$("#btn-expo").addEventListener("click", () => {
  const activo = document.documentElement.classList.toggle("expo");
  preferencia("expo", activo ? "1" : "0");
  aviso(activo ? "Modo exposición activado: letra más grande" : "Modo exposición desactivado");
});
$("#btn-pantalla").addEventListener("click", () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen?.();
});

/* ================================================================ INICIO */
const GUION = [
  ["Presentar la red de la Caja", "Red física de Cusco: 39 nodos, carreteras y tren; puntos críticos.", async () => { await ir("red"); $("#red-criticos").checked = true; dibujarRedFisica(); }],
  ["Detectar el ciclo y las capas de lavado", "Tarjan encuentra el grupo; el orden topológico revela 3 capas.", async () => { await ir("fraude"); activarPestana("fraude", "capas"); }],
  ["Ver BFS en acción", "Animación por niveles desde la bóveda central.", async () => { await ir("animacion"); Ani.cargar("bfs", "cusco"); }],
  ["Quillabamba → Lima: mover el monto", "Dijkstra cambia de ruta según el monto y el criterio.", async () => { await ir("rutas"); Rutas.escenario(0); }],
  ["Activar la campaña y descubrir el ruleteo", "Pesos negativos → Bellman-Ford detecta el ciclo negativo.", async () => { await ir("rutas"); Rutas.variante("ruleteo"); }],
  ["Temporada alta: el tren es el cuello de botella", "Flujo máximo y corte mínimo en el mapa.", async () => { await ir("liquidez"); Liq.reiniciar(); }],
  ["Simular el huaico en Abra Málaga en vivo", "Se cierra el tramo y se recalcula todo.", async () => { await ir("liquidez"); Liq.huaico(); }],
  ["Demostrar con pruebas", "Validación 21/21 y comparación empírica de algoritmos.", async () => { await ir("evaluacion"); }],
];

INICIAR.inicio = async () => {
  $("#guion").innerHTML = GUION.map(([t, d], i) =>
    `<li><div class="txt"><b>${t}</b><span class="tenue pequeno">${d}</span></div>
     <button class="btn chico" data-guion="${i}">Ir ▸</button></li>`).join("");
  $("#guion").addEventListener("click", e => {
    const b = e.target.closest("[data-guion]");
    if (b) GUION[+b.dataset.guion][2]();
  });
  const r = await api("resumen");
  const totalAlertas = Object.values(r.alertas).reduce((a, b) => a + b, 0);
  $("#inicio-kpis").innerHTML = [
    kpi(fmt(r.transacciones), "Transacciones analizadas", `${fmt(r.redes[3].V)} cuentas · junio 2026`, "azul"),
    kpi(totalAlertas, "Alertas detectadas", Object.entries(r.alertas).map(([k, v]) => `${k}: ${v}`).join(" · "), "acento"),
    kpi(fmt(r.cobertura.alta, 1) + " %", "Cobertura de efectivo · temporada alta", `faltan S/ ${fmt(r.pendiente.alta)} mil`, "ambar"),
    kpi(fmt(r.cobertura.huaico, 1) + " %", "Cobertura con huaico", `faltan S/ ${fmt(r.pendiente.huaico)} mil`, "acento"),
    kpi(`${r.validacion.ok}/${r.validacion.total}`, "Validaciones correctas", "casos con resultado esperado", "verde"),
  ].join("");
  $("#inicio-redes").innerHTML = `<table class="tabla"><thead><tr><th>Red</th><th>Tipo</th><th class="num">V</th><th class="num">E</th></tr></thead><tbody>${
    r.redes.map(x => `<tr><td>${x.nombre}</td><td><span class="insignia gris">${x.tipo}</span></td><td class="num">${fmt(x.V)}</td><td class="num">${fmt(x.E)}</td></tr>`).join("")}</tbody></table>`;
};

/* ================================================================ MÓDULO 1 */
let redFisica = null;
let posFisica = null;

function globoNodoFisico(n) {
  const filas = [`<b>${esc(n.nombre || n.id)}</b>`, `${NOMBRE_TIPO[n.tipo] || n.tipo || ""} · ${esc(n.provincia || "")}`];
  if (n.oferta) filas.push(`Oferta: S/ ${fmt(n.oferta)} mil`);
  if (n.almacenamiento) filas.push(`Almacenamiento: S/ ${fmt(n.almacenamiento)} mil`);
  if (n.demanda_alta) filas.push(`Demanda: normal ${fmt(n.demanda_normal)} · alta ${fmt(n.demanda_alta)} (miles S/)`);
  return filas.join("<br>");
}
function globoAristaFisica(a) {
  return `<b>${esc(a.nombre || a.u + " – " + a.v)}</b><br>${a.u} – ${a.v} · ${a.tipo_via || ""}<br>` +
    `${fmt(a.distancia_km, 1)} km · ${fmt(a.tiempo_h, 2)} h · riesgo ${a.riesgo}/10`;
}
function estiloBaseArista(a) {
  return a.tipo_via === "tren"
    ? { color: "#d07a2a", ancho: 2.6, guiones: "8 5", opacidad: 0.95 }
    : { color: "var(--tenue)", ancho: 1.8, opacidad: 0.6 };
}
function leyendaFisica(cont, extra = []) {
  leyenda(cont, [["#8e2a2a", "Bóveda central"], ["#c97a2c", "Bóveda regional"], ["#2f5d8a", "Agencia"],
    ["#5a8fc2", "Cajero"], ["#3f8f6b", "Agente"], ["#a3a8b0", "Nodo de paso"], ["#d07a2a", "Tren", true], ...extra]);
}

function dibujarRedFisica() {
  if (!redFisica) return;
  const cont = $("#red-mapa");
  posFisica = posicionesGeograficas(redFisica.nodos, 1000, 760);
  const criticos = $("#red-criticos").checked ? redFisica.criticos : {};
  const nombres = $("#red-nombres").checked;
  dibujarRed(cont, {
    nodos: redFisica.nodos, aristas: redFisica.aristas, dirigido: false, pos: posFisica, W: 1000, H: 760,
    estiloArista: estiloBaseArista,
    estiloNodo: n => criticos[n.id] ? { halo: "#6a4c9c" } : {},
    etiquetaNodo: n => nombres ? (n.nombre || n.id).replace("Agencia ", "").replace("Cajero ", "ATM ") : n.id,
    globoNodo: n => globoNodoFisico(n) + (criticos[n.id] ? `<br><b>Crítico:</b> si falla aísla ${criticos[n.id].length} nodos` : ""),
    globoArista: globoAristaFisica,
    alClicNodo: n => {
      $("#nodo-id").value = n.id; $("#nodo-tipo").value = n.tipo || "agencia";
      activarPestana("red", "editar"); aviso(`Nodo ${n.id} cargado en el formulario`);
    },
    alClicArista: a => {
      $("#arista-u").value = a.u; $("#arista-v").value = a.v;
      $("#arista-attrs").value = `tipo_via=${a.tipo_via}, distancia_km=${a.distancia_km}, tiempo_h=${a.tiempo_h}, riesgo=${a.riesgo}`;
      activarPestana("red", "editar"); aviso(`Tramo ${a.u} – ${a.v} cargado en el formulario`);
    },
  });
  leyendaFisica(cont, Object.keys(criticos).length ? [["#6a4c9c", "Punto crítico"]] : []);
  renderResumenRed();
}

function renderResumenRed() {
  const r = redFisica;
  const criticos = Object.entries(r.criticos).sort((a, b) => b[1].length - a[1].length);
  $("#red-resumen").innerHTML = `
    <div class="rejilla r3">
      ${kpi(r.nodos.length, "Nodos")}${kpi(r.aristas.length, "Tramos")}${kpi(r.componentes.length, "Componentes", r.componentes.length === 1 ? "red conexa" : "¡red desconectada!")}
    </div>
    <p class="mt">${Object.entries(r.tipos).map(([t, c]) => `<span class="insignia gris">${NOMBRE_TIPO[t] || t}: ${c}</span>`).join(" ")}</p>
    ${r.problemas.length ? `<div class="alerta">${r.problemas.map(esc).join("<br>")}</div>` : '<div class="exito">Validación de consistencia: sin problemas.</div>'}
    ${r.componentes.length > 1 ? `<div class="alerta mt">Nodos separados del bloque principal: ${chips(r.componentes.slice(1).flat(), "rojo")}</div>` : ""}
    <h3 class="mt">Puntos críticos <span class="insignia">eliminación + BFS (G7)</span></h3>
    <div class="scroll" style="max-height:260px"><table class="tabla"><thead><tr><th>Nodo</th><th>Si falla, quedan aislados</th></tr></thead><tbody>
    ${criticos.map(([n, s]) => `<tr><td><b>${n}</b></td><td class="pequeno">${s.join(", ")}</td></tr>`).join("")}</tbody></table></div>`;
}

INICIAR.red = async () => {
  redFisica = await api("red");
  dibujarRedFisica();
  ["red-criticos", "red-nombres"].forEach(id => $("#" + id).addEventListener("change", dibujarRedFisica));
  $$("[data-nodo]").forEach(b => b.addEventListener("click", async () => {
    const accion = b.dataset.nodo;
    const atributos = accion === "eliminar" ? {} : { ...leerAtributos($("#nodo-attrs").value), tipo: $("#nodo-tipo").value };
    if (accion === "agregar" && !("nombre" in atributos)) atributos.nombre = $("#nodo-id").value;
    if (accion === "agregar" && !("lat" in atributos)) { atributos.lat = -13.6; atributos.lon = -71.75; }
    redFisica = await api("nodo", { accion, id: $("#nodo-id").value.trim(), atributos });
    dibujarRedFisica(); aviso(`Nodo ${accion === "eliminar" ? "eliminado" : accion === "agregar" ? "agregado" : "modificado"}`);
  }));
  $$("[data-arista]").forEach(b => b.addEventListener("click", async () => {
    const accion = b.dataset.arista;
    redFisica = await api("arista", { accion, u: $("#arista-u").value.trim(), v: $("#arista-v").value.trim(),
      atributos: accion === "eliminar" ? {} : leerAtributos($("#arista-attrs").value) });
    dibujarRedFisica(); aviso("Tramo actualizado: se recalcularon conectividad y puntos críticos");
  }));
  $("#btn-restablecer").addEventListener("click", async () => {
    redFisica = await api("restablecer", {}); dibujarRedFisica(); aviso("Red restablecida desde data/");
  });
  $("#archivo").addEventListener("change", async e => {
    const f = e.target.files[0];
    if (!f) return;
    const contenido = await f.text();
    const r = await api("cargar", { nombre: f.name, contenido, dirigido: $("#archivo-dirigido").checked });
    const cont = $("#archivo-resultado");
    cont.innerHTML = `<pre class="pequeno" style="white-space:pre-wrap">${esc(r.resumen)}</pre><div class="lienzo"></div>`;
    const ids = r.nodos.map(n => n.id);
    const pos = posicionesCirculo(ids, 300, 220, 170);
    dibujarRed($(".lienzo", cont), { nodos: r.nodos, aristas: r.aristas, dirigido: r.dirigido, pos, W: 600, H: 440,
      estiloArista: a => ({ etiqueta: Object.entries(a).filter(([k, v]) => !["u", "v"].includes(k) && typeof v === "number").map(([, v]) => v)[0] }) });
  });
  alCambiarPestana.red = async tab => {
    if (tab === "titularidad" && !$("#red-titularidad").dataset.ok) {
      const t = await api("titularidad");
      $("#red-titularidad").dataset.ok = 1;
      $("#red-titularidad").innerHTML = `
        <div class="rejilla r2">${kpi(fmt(t.clientes), "Clientes")}${kpi(fmt(t.cuentas), "Cuentas")}</div>
        <div class="${t.bipartito ? "exito" : "alerta"} mt">${t.bipartito ? "✔ El grafo cliente – cuenta es <b>bipartito</b>: ningún cliente se enlaza con otro cliente ni una cuenta con otra cuenta (BFS de dos colores, G7)." : t.problemas.join("<br>")}</div>
        <p class="mt pequeno">Grafo <b>no dirigido y no ponderado</b>. Clientes con varias cuentas (relación 1 a N):</p>
        ${t.multiples.map(m => `<div><b>${m.cliente}</b>: ${chips(m.cuentas)}</div>`).join("")}`;
    }
  };
};

/* ================================================================ MÓDULO 2 */
let fraudeDatos = null;

function dibujarSubgrafo(cont, sub, cfg = {}) {
  const W = cfg.W || 900, H = cfg.H || 420;
  const pos = cfg.layout === "circulo"
    ? posicionesCirculo(sub.nodos.map(n => n.id), W / 2, H / 2, Math.min(W, H) / 2 - 60)
    : cfg.layout === "anillos" ? posicionesAnillos(sub.nodos, W, H) : posicionesCapas(sub.nodos, W, H);
  return dibujarRed(cont, {
    nodos: sub.nodos.map(n => ({ ...n, tipo: "cuenta" })), aristas: sub.aristas, dirigido: true, pos, W, H,
    estiloNodo: n => Object.assign({ color: PALETA_NIVELES[n.capa % PALETA_NIVELES.length] }, cfg.estiloNodo ? cfg.estiloNodo(n) : {}),
    estiloArista: a => Object.assign({ color: "var(--tenue)", ancho: 1.2 + Math.min(6, Math.sqrt((a.monto || 0) / 8000)),
      opacidad: 0.8, etiqueta: cfg.sinEtiquetas ? "" : `S/ ${fmt(a.monto)}${a.n > 1 ? ` (${a.n} ops)` : ""}` },
      cfg.estiloArista ? cfg.estiloArista(a) : {}),
    globoNodo: n => `<b>${n.id}</b>${cfg.nombreCapa ? "<br>" + cfg.nombreCapa(n.capa) : ""}`,
    globoArista: a => `<b>${a.u} → ${a.v}</b><br>Monto total: S/ ${fmt(a.monto, 2)}<br>Operaciones: ${a.n}`,
    etiquetaNodo: n => n.id,
  });
}

function panelPatron(sel, html) { $(`[data-panel="fraude:${sel}"]`).innerHTML = html; }

function renderFraude() {
  const f = fraudeDatos;
  $("#fraude-aviso").innerHTML = "⚖ " + esc(f.aviso);
  $("#fraude-kpis").innerHTML = [
    kpi(f.pitufeo.length, "Pitufeo", f.pitufeo.map(a => a.cuenta_destino).join(", "), "acento"),
    kpi(f.ciclos.length, "Ciclos de fondos", f.ciclos.map(c => c.cuentas.length + " cuentas").join(", "), "acento"),
    kpi(f.puentes.length, "Cuentas puente", f.puentes.map(a => a.cuenta_puente).join(", "), "acento"),
    kpi(f.estratificacion.length, "Estratificación", f.estratificacion.map(h => h.numero_capas + " capas").join(", "), "acento"),
    kpi(f.viajes.length, "Viaje imposible", f.viajes.map(v => v.tarjeta).join(", "), "acento"),
  ].join("");
  const badge = (tab, n) => { const b = $(`#fraude-tabs [data-tab="${tab}"]`); if (n) b.insertAdjacentHTML("beforeend", ` <span class="chip-num">${n}</span>`); };
  badge("pitufeo", f.pitufeo.length); badge("ciclos", f.ciclos.length); badge("puente", f.puentes.length);
  badge("capas", f.estratificacion.length); badge("viaje", f.viajes.length);

  // Pitufeo
  const p = f.pitufeo[0];
  panelPatron("pitufeo", p ? `
    <div class="rejilla r2"><div><p>Muchos depósitos <b>fraccionados justo por debajo del umbral</b> de S/ ${fmt(f.umbral)} (entre S/ ${fmt(f.umbral * 0.8)} y S/ ${fmt(f.umbral - 1)}) desde varias cuentas hacia una sola, en una ventana de 72 horas.</p>
      <div class="alerta"><b>${p.cuenta_destino}</b> recibió <b>${p.operaciones} depósitos</b> de <b>${p.emisores.length} cuentas</b> entre ${p.desde} y ${p.hasta}: total ${soles(p.monto_total)}. Agencias: ${chips(p.agencias)} (corredor Interoceánica).</div></div>
      <div class="porque"><b class="t">Cómo se detecta</b>Sobre el <b>registro de eventos</b> se cuentan las entradas de cada cuenta con una <b>ventana deslizante de dos punteros</b> (O(n log n)). En el grafo se ve como una estrella: muchas aristas que convergen en un nodo (alto grado de entrada).</div></div>
    <div class="lienzo mt" id="g-pitufeo"></div>` : "<p>Sin alertas.</p>");
  if (p) dibujarSubgrafo($("#g-pitufeo"), p.grafo, { nombreCapa: c => c ? "Cuenta destino" : "Cuenta emisora",
    estiloNodo: n => n.capa === 1 ? { r: 16, halo: "#c0392b" } : {} });

  // Ciclos
  const c = f.ciclos[0];
  panelPatron("ciclos", c ? `
    <div class="rejilla r2"><div><p>El dinero <b>vuelve a su origen</b> pasando por empresas relacionadas.</p>
      <div class="alerta">Grupo ${chips(c.cuentas, "rojo")}<br>${soles(c.monto_interno)} circulando dentro del grupo.<br>${c.ciclos.map(x => "Ciclo: " + camino(x)).join("<br>")}</div></div>
      <div class="porque"><b class="t">Algoritmo: Tarjan (G7) · O(V+E)</b>Las <b>componentes fuertemente conexas</b> son grupos donde cada cuenta puede llegar a todas las demás: el dinero puede circular. Luego un <b>DFS</b> dentro del grupo extrae los ciclos. Kosaraju da el mismo resultado con dos pasadas.</div></div>
    <div class="lienzo mt" id="g-ciclo"></div>` : "<p>Sin alertas.</p>");
  if (c) dibujarSubgrafo($("#g-ciclo"), c.grafo, { layout: "circulo", H: 380,
    estiloArista: () => ({ color: "#c0392b", clase: "flujo-anim" }) });

  // Puente
  const pu = f.puentes[0];
  panelPatron("puente", pu ? `
    <div class="rejilla r2"><div><p>Una cuenta <b>recibe un monto alto y lo reenvía casi completo</b> a varias cuentas en pocas horas.</p>
      <div class="alerta"><b>${pu.cuenta_puente}</b> recibió ${soles(pu.recibido)} de ${pu.de} y reenvió <b>${pu.porcentaje} %</b> en <b>${pu.horas} h</b> a ${chips(pu.receptores)}.</div></div>
      <div class="porque"><b class="t">Cómo se detecta</b>Para cada entrada ≥ S/ 20 000 se suman las salidas de esa cuenta en las 12 horas siguientes. Si superan el 80 % y van a 2 o más cuentas, se genera la alerta.</div></div>
    <div class="lienzo mt" id="g-puente"></div>` : "<p>Sin alertas.</p>");
  if (pu) dibujarSubgrafo($("#g-puente"), pu.grafo, { H: 340, nombreCapa: c => ["Origen", "Cuenta puente", "Receptor"][c],
    estiloNodo: n => n.capa === 1 ? { r: 15, halo: "#c0392b" } : {} });

  // Estratificación
  const h = f.estratificacion[0];
  panelPatron("capas", h ? `
    <div class="rejilla r2"><div><p>El dinero pasa por <b>varias capas de cuentas</b> antes de llegar a su destino final (fase de estratificación del lavado).</p>
      <div class="alerta">Destino final ${chips(h.final, "rojo")}: el dinero pasó por <b>${h.numero_capas} capas</b> desde ${chips(h.origenes)}.<br>
      ${Object.entries(h.capas).map(([k, v]) => `Capa ${k}: ${v.join(", ")}`).join("<br>")}</div></div>
      <div class="porque"><b class="t">Algoritmo: orden topológico (G7) · O(V+E)</b>1) Se toman solo las transferencias ≥ S/ ${fmt(f.umbral_alto)}. 2) Tarjan contrae los ciclos → el <b>grafo condensado es acíclico</b>. 3) El orden topológico asigna a cada cuenta su capa (camino más largo desde una fuente).</div></div>
    <div class="lienzo mt" id="g-capas"></div>` : "<p>Sin alertas.</p>");
  if (h) dibujarSubgrafo($("#g-capas"), h.grafo, { H: 360, nombreCapa: c => "Capa " + c,
    estiloNodo: n => n.capa === h.numero_capas ? { r: 15, halo: "#c0392b" } : {} });

  // Viaje imposible
  panelPatron("viaje", `
    <div class="rejilla r2"><div><p>Una misma tarjeta se usa en dos cajeros con <b>menos tiempo del que toma viajar</b> entre ellos: posible tarjeta clonada.</p>
      ${f.viajes.map((v, i) => `<div class="alerta" style="margin-bottom:8px;cursor:pointer" data-viaje="${i}">💳 <b>${v.tarjeta}</b>: ${v.cajero_1} (${v.fecha_1}) → ${v.cajero_2} (${v.fecha_2})<br>
        Pasaron <b>${fmt(v.horas_transcurridas, 2)} h</b>, pero el viaje mínimo toma <b>${fmt(v.horas_minimas_viaje, 2)} h</b>. <span class="tenue pequeno">(clic para ver la ruta)</span></div>`).join("")}
      <div class="exito pequeno">La tarjeta T0250 (turista que fue de Cusco a Machupicchu en 9 h) no se marca: no hay falso positivo.</div></div>
      <div class="porque"><b class="t">Algoritmo: Floyd-Warshall (G10) · O(V³)</b>Se calcula una sola vez la matriz de <b>tiempos mínimos entre todos los pares</b> de la red física (39 nodos) y luego cada par de retiros consecutivos se compara en O(1).</div></div>
    <div class="lienzo mt" id="g-viaje"></div>`);
  dibujarViaje(0);
  $(`[data-panel="fraude:viaje"]`).addEventListener("click", e => {
    const d = e.target.closest("[data-viaje]"); if (d) dibujarViaje(+d.dataset.viaje);
  });
}

async function dibujarViaje(i) {
  const v = fraudeDatos.viajes[i];
  if (!v) return;
  if (!redFisica) redFisica = await api("red");
  const pos = posicionesGeograficas(redFisica.nodos, 1000, 640);
  const enCamino = new Set(v.camino.slice(1).map((n, k) => [v.camino[k], n].sort().join("|")));
  const cont = $("#g-viaje");
  dibujarRed(cont, {
    nodos: redFisica.nodos, aristas: redFisica.aristas, dirigido: false, pos, W: 1000, H: 640,
    estiloArista: a => enCamino.has([a.u, a.v].sort().join("|"))
      ? { color: "#c0392b", ancho: 5, opacidad: 1, etiqueta: fmt(a.tiempo_h, 2) + " h", colorEtiqueta: "#c0392b", negritaEtiqueta: true }
      : { ...estiloBaseArista(a), opacidad: 0.35 },
    estiloNodo: n => [v.cajero_1, v.cajero_2].includes(n.id) ? { halo: "#c0392b", r: 10 } : { opacidad: v.camino.includes(n.id) ? 1 : 0.45 },
    etiquetaNodo: n => v.camino.includes(n.id) || n.tipo.startsWith("boveda") ? n.id : "",
    globoNodo: globoNodoFisico, globoArista: globoAristaFisica,
  });
  leyenda(cont, [["#c0392b", `Ruta más rápida: ${fmt(v.horas_minimas_viaje, 2)} h`, true]]);
}

INICIAR.fraude = async () => {
  cargando($('[data-panel="fraude:pitufeo"]'));
  fraudeDatos = await api("fraude");
  renderFraude();
  api("cuentas").then(cs => { $("#lista-cuentas").innerHTML = cs.map(c => `<option value="${c}">`).join(""); });
  $("#prox-niveles").addEventListener("input", e => { $("#prox-niv-txt").textContent = e.target.value; });
  $("#btn-prox").addEventListener("click", async () => {
    const r = await api(`proximidad?cuenta=${encodeURIComponent($("#prox-cuenta").value)}&niveles=${$("#prox-niveles").value}`);
    const cont = $("#prox-resultado");
    cont.innerHTML = `<div class="rejilla r2"><div>${Object.entries(r.totales).map(([n, t]) =>
      `<span class="insignia" style="background:${PALETA_NIVELES[n]}22;color:${PALETA_NIVELES[n]}">A ${n} salto(s): ${t} cuentas</span>`).join(" ")}
      <p class="pequeno tenue mt">Se muestran hasta 24 cuentas por nivel. El sentido de la transferencia no importa: interesa la relación.</p></div>
      <div class="porque"><b class="t">Algoritmo: BFS por niveles (G7) · O(V+E)</b>BFS explora primero todos los vecinos directos y luego los de segundo nivel, así el nivel es el <b>menor número de saltos</b>. DFS no garantiza eso.</div></div>
      <div class="lienzo mt"></div>`;
    dibujarSubgrafo($(".lienzo", cont), r.grafo, { layout: "anillos", H: 560, sinEtiquetas: true,
      nombreCapa: c => c === 0 ? "Cuenta marcada" : `A ${c} salto(s)`, estiloNodo: n => n.capa === 0 ? { r: 15, halo: "#c0392b" } : { r: 7 },
      estiloArista: () => ({ ancho: 1, opacidad: 0.35, flecha: false }) });
  });
  $("#btn-ras").addEventListener("click", async () => {
    const r = await api(`rastreo?cuenta=${encodeURIComponent($("#ras-cuenta").value)}&minimo=${$("#ras-minimo").value || 0}`);
    const cont = $("#ras-resultado");
    cont.innerHTML = `<div class="rejilla r2"><div><p><b>${r.caminos.length}</b> recorridos encontrados.</p>
      <p>Intermediarios: ${chips(r.intermediarios) || "ninguno"}</p><p>Receptores finales: ${chips(r.receptores, "rojo") || "ninguno"}</p></div>
      <div class="porque"><b class="t">Algoritmo: DFS (G7)</b>Sigue cada recorrido de los fondos hasta una cuenta sin salidas o hasta 6 saltos, solo por relaciones de al menos el monto indicado. Se usa una pila explícita (sin recursión).</div></div>
      <div class="lienzo mt"></div>`;
    dibujarSubgrafo($(".lienzo", cont), r.grafo, { H: 400, nombreCapa: c => "Profundidad " + c });
  });
  alCambiarPestana.fraude = async tab => {
    if (tab === "proximidad" && !$("#prox-resultado").innerHTML) $("#btn-prox").click();
    if (tab === "rastreo" && !$("#ras-resultado").innerHTML) $("#btn-ras").click();
    if (tab === "cfc" && !$('[data-panel="fraude:cfc"]').innerHTML) {
      const r = await api("cfc");
      panelPatron("cfc", `<p>Ambos algoritmos de la Guía 7 sobre la red real de ${fmt(fraudeDatos.cuentas)} cuentas y ${fmt(fraudeDatos.relaciones)} relaciones:</p>
        <table class="tabla"><thead><tr><th>Algoritmo</th><th class="num">Componentes</th><th class="num">Tiempo (ms)</th><th class="num">Memoria pico (KB)</th><th>Pasadas DFS</th></tr></thead><tbody>
        <tr><td><b>Kosaraju</b></td><td class="num">${r.kosaraju.componentes}</td><td class="num">${r.kosaraju.ms}</td><td class="num">${r.kosaraju.kb}</td><td>2 (+ grafo transpuesto)</td></tr>
        <tr><td><b>Tarjan</b></td><td class="num">${r.tarjan.componentes}</td><td class="num">${r.tarjan.ms}</td><td class="num">${r.tarjan.kb}</td><td>1 (índice y lowlink)</td></tr></tbody></table>
        <div class="${r.coinciden ? "exito" : "alerta"} mt">${r.coinciden ? "✔ Ambos encuentran exactamente las mismas componentes." : "Los resultados difieren."} Grupos con más de una cuenta: ${r.grupos.map(g => chips(g, "rojo")).join(" ")}</div>
        <div class="porque mt"><b class="t">Elección</b>Tarjan: misma complejidad O(V+E) pero una sola pasada y sin construir el transpuesto, por eso usa menos memoria.</div>`);
    }
  };
};

/* ================================================================ MÓDULO 3 */
const Rutas = {
  red: null, pos: null, ultima: null, temporizador: null, varianteActual: "",
  montoDesdeSlider: t => {
    const v = Math.pow(10, Math.log10(50) + (t / 100) * (Math.log10(100000) - Math.log10(50)));
    const paso = v < 1000 ? 50 : v < 10000 ? 100 : 1000;
    return Math.max(50, Math.round(v / paso) * paso);
  },
  sliderDesdeMonto: m => 100 * (Math.log10(m) - Math.log10(50)) / (Math.log10(100000) - Math.log10(50)),
  montoExacto: null,
  monto() { return this.montoExacto ?? this.montoDesdeSlider(+$("#ruta-monto").value); },
  fijarMonto(m) { this.montoExacto = m; $("#ruta-monto").value = this.sliderDesdeMonto(m); this.actualizarMontoTexto(); },

  async cargarRed(variante) {
    this.red = await api("enrutamiento" + (variante ? "?variante=" + variante : ""));
    if (!this.pos) this.pos = this.posiciones();
  },
  posiciones() {
    // Disposición por bandas: pagos a Lima (arriba), turista (centro), retiro de efectivo (abajo)
    const ESQUEMA = {
      CTA_CMA_QUI: [80, 170], CTA_CMA_CUS: [80, 330], BILL_A: [300, 55], EFECTIVO_QUI: [300, 135],
      INTERPLAZA: [300, 215], BILL_B: [520, 55], AG_BX_QUI: [520, 135], CTA_CMA_LIMA: [520, 215],
      CCE_INM: [700, 255], CCE_DIF: [700, 345], CTA_BX_LIMA: [920, 150], CTA_BY_CUS: [920, 330],
      TC_EXT: [80, 500], PROC_TARJ: [470, 430], ATM_CMA_MPP: [300, 500], ATM_RED_MPP: [300, 570],
      EFECTIVO_MPP: [620, 535], CTA_REST_MPP: [920, 480],
      TD_CMA_CUS: [80, 665], ATM_CMA_LEJOS: [400, 630], ATM_RED_CERCA: [400, 705], EFECTIVO_CLIENTE: [720, 665],
    };
    if (this.red.nodos.every(n => ESQUEMA[n.id])) return ESQUEMA;
    const entrantes = {};
    this.red.nodos.forEach(n => { entrantes[n.id] = 0; });
    this.red.aristas.forEach(a => { entrantes[a.v]++; });
    const nivel = {};
    const cola = this.red.nodos.filter(n => entrantes[n.id] === 0).map(n => n.id);
    cola.forEach(id => { nivel[id] = 0; });
    while (cola.length) {
      const u = cola.shift();
      for (const a of this.red.aristas.filter(x => x.u === u)) {
        if (nivel[a.v] === undefined) { nivel[a.v] = nivel[u] + 1; cola.push(a.v); }
      }
    }
    return posicionesCapas(this.red.nodos.map(n => ({ id: n.id, capa: nivel[n.id] ?? 0 })), 1000, 640, 80);
  },
  async escenario(i) {
    if (!this.red) await INICIAR_RUTAS_PROMESA;
    const e = this.red.escenarios[i];
    $("#ruta-escenario").value = i;
    $("#ruta-origen").value = e.origen; $("#ruta-destino").value = e.destino;
    this.fijarMonto(e.monto);
    await this.consultar();
  },
  async variante(v) {
    if (!this.red) await INICIAR_RUTAS_PROMESA;
    this.selector.fijar(v);
    await this.cambiarVariante(v);
  },
  async cambiarVariante(v) {
    this.varianteActual = v;
    await this.cargarRed(v);
    if (v) { $("#ruta-origen").value = "CTA_CMA_QUI"; $("#ruta-destino").value = "CTA_BX_LIMA"; this.fijarMonto(400); }
    await this.consultar();
    if (v === "promo") aviso("Campaña CyberDays: la billetera B paga S/ 4 de cashback → aparece un peso negativo");
    if (v === "ruleteo") aviso("Se agrega la devolución de la billetera a la cuenta CMA → se cierra un ciclo");
  },
  actualizarMontoTexto() { $("#ruta-monto-txt").textContent = soles(this.monto(), 0); },
  costoArista(a, monto) { return (a.comision_fija || 0) + (a.comision_pct || 0) / 100 * monto - (a.bonificacion || 0); },

  async consultar() {
    const monto = this.monto();
    const datos = { origen: $("#ruta-origen").value, destino: $("#ruta-destino").value, monto, variante: this.varianteActual };
    const r = await api("consulta", datos);
    this.ultima = r;
    this.render(r, monto);
  },

  render(r, monto) {
    const tarjeta = (titulo, x, color, icono) => {
      if (x.ciclo_negativo) return `<div class="tarjeta" style="border-top:3px solid var(--rojo)"><h3>${icono} ${titulo}</h3>
        <div class="alerta">No hay ruta mínima definida: existe un <b>ciclo negativo</b> alcanzable.</div><p class="mt"><span class="insignia rojo">${x.algoritmo}</span></p></div>`;
      if (!x.camino.length) return `<div class="tarjeta"><h3>${icono} ${titulo}</h3><div class="alerta">No hay ruta viable para este monto.</div></div>`;
      return `<div class="tarjeta" style="border-top:3px solid ${color}">
        <h3>${icono} ${titulo}</h3>
        <div class="rejilla r2"><div><div class="kpi" style="padding:0"><div class="etiqueta">Comisión</div><div class="valor">${soles(x.costo)}</div></div></div>
        <div><div class="kpi" style="padding:0"><div class="etiqueta">Tiempo</div><div class="valor">${x.tiempo_min >= 1440 ? fmt(x.tiempo_min / 60, 0) + " h" : fmt(x.tiempo_min) + " min"}</div></div></div></div>
        <p class="mt">${camino(x.camino)}</p>
        <p class="pequeno tenue">${x.canales.map(esc).join(" · ")}</p>
        <span class="insignia ${x.algoritmo.startsWith("Bellman") ? "ambar" : ""}">${x.algoritmo}</span></div>`;
    };
    $("#ruta-mejores").innerHTML = tarjeta("Ruta más barata", r.costo, "var(--verde)", "💰") + tarjeta("Ruta más rápida", r.tiempo, "var(--azul)", "⚡");
    $("#ruta-alerta").innerHTML = r.ruleteo
      ? `<div class="alerta"><b>⚠ Ruleteo detectado (Bellman-Ford):</b> ${camino(r.ruleteo.ciclo)} produce una ganancia de <b>${soles(-r.ruleteo.costo_por_vuelta)}</b> por vuelta. Repetirlo genera dinero sin límite: se reporta al área de cumplimiento (módulo 2).</div>` : "";

    const usaBF = r.costo.algoritmo.startsWith("Bellman");
    $("#ruta-porque").innerHTML = usaBF
      ? `<p><span class="insignia ambar">Bellman-Ford · O(V·E)</span></p><p>Hay <b>pesos negativos</b> (el cashback supera la comisión). Dijkstra asume que al extraer un nodo su distancia ya es definitiva, lo que es falso con pesos negativos. Bellman-Ford relaja todas las aristas V−1 veces y una relajación extra revela si hay un <b>ciclo negativo</b>.</p>`
      : `<p><span class="insignia">Dijkstra · O((V+E) log V)</span></p><p>Todas las comisiones y tiempos son <b>no negativos</b>, así que Dijkstra con cola de prioridad (heapq) es correcto y más rápido que Bellman-Ford. Si una campaña introduce un peso negativo, el sistema cambia solo a Bellman-Ford.</p>`;

    // grafo
    const enCosto = new Set(r.costo.camino.slice(1).map((n, k) => r.costo.camino[k] + "|" + n));
    const enTiempo = new Set(r.tiempo.camino.slice(1).map((n, k) => r.tiempo.camino[k] + "|" + n));
    const enCiclo = new Set(r.ruleteo ? r.ruleteo.ciclo.slice(1).map((n, k) => r.ruleteo.ciclo[k] + "|" + n) : []);
    const cont = $("#ruta-grafo");
    dibujarRed(cont, {
      nodos: this.red.nodos, aristas: this.red.aristas, dirigido: true, pos: this.pos, W: 1000, H: 750,
      estiloArista: a => {
        const clave = a.u + "|" + a.v, w = this.costoArista(a, monto);
        const excluida = a.disponible === 0 || (a.limite !== null && a.limite !== undefined && a.limite < monto);
        const base = { etiqueta: "", ancho: 1.4, opacidad: 0.5 };
        const conCosto = { etiqueta: soles(w), negritaEtiqueta: true };
        if (enCiclo.has(clave)) return { ...base, ...conCosto, color: "#c0392b", ancho: 4, opacidad: 1, clase: "flujo-anim", colorEtiqueta: "#c0392b" };
        if (enCosto.has(clave) && enTiempo.has(clave)) return { ...base, ...conCosto, color: "#2f7d4f", ancho: 5, opacidad: 1, resalte: "rgba(43,90,138,.35)" };
        if (enCosto.has(clave)) return { ...base, ...conCosto, color: "#2f7d4f", ancho: 4.5, opacidad: 1, colorEtiqueta: "#2f7d4f" };
        if (enTiempo.has(clave)) return { ...base, ...conCosto, etiqueta: fmt(a.tiempo_min) + " min", color: "#2b5a8a", ancho: 4.5, opacidad: 1, colorEtiqueta: "#2b5a8a" };
        if (excluida) return { ...base, color: "#c0392b", guiones: "4 4", opacidad: 0.3 };
        if (w < 0) return { ...base, ...conCosto, color: "#6a4c9c", ancho: 2.5, opacidad: 1, colorEtiqueta: "#6a4c9c" };
        return base;
      },
      estiloNodo: n => [$("#ruta-origen").value, $("#ruta-destino").value].includes(n.id) ? { halo: "#9b2c2c", haloPulso: false } : {},
      etiquetaNodo: n => n.id,
      globoNodo: n => `<b>${esc(n.nombre)}</b><br>${NOMBRE_TIPO[n.tipo] || n.tipo}`,
      globoArista: a => `<b>${esc(a.canal)}</b><br>Fija ${soles(a.comision_fija)} · ${fmt(a.comision_pct, 2)} %${a.bonificacion ? ` · cashback ${soles(a.bonificacion)}` : ""}<br>Tiempo ${fmt(a.tiempo_min)} min · límite ${soles(a.limite, 0)}<br><b>Costo para ${soles(monto, 0)}: ${soles(this.costoArista(a, monto))}</b>`,
      alClicNodo: n => { $("#ruta-destino").value = n.id; this.consultar(); },
    });
    leyenda(cont, [["#2f7d4f", "Ruta más barata", true], ["#2b5a8a", "Ruta más rápida", true], ["#c0392b", "Excede el límite / ciclo", true], ["#6a4c9c", "Peso negativo (cashback)", true]]);

    const fila = (x, i) => `<tr><td>${i + 1}</td><td>${camino(x.camino)}</td><td class="num">${soles(x.costo)}</td><td class="num">${fmt(x.tiempo_min)} min</td><td class="pequeno tenue">${x.canales.map(esc).join(" · ")}</td></tr>`;
    $("#ruta-alternativas").innerHTML = `<table class="tabla"><thead><tr><th>#</th><th>Ruta</th><th class="num">Comisión</th><th class="num">Tiempo</th><th>Canales</th></tr></thead><tbody>${r.viables.map(fila).join("")}</tbody></table>
      ${r.no_viables.length ? `<p class="mt pequeno"><b>Descartadas por límite:</b></p>${r.no_viables.map(x => `<div class="pequeno">${camino(x.camino)} <span class="insignia rojo">${x.restricciones.map(esc).join(", ")}</span></div>`).join("")}` : ""}`;
  },

  async tiempos(alg) {
    const t = await api("tiempos?algoritmo=" + alg);
    const vals = t.matriz.flat().filter(v => v > 0);
    const [mn, mx] = [Math.min(...vals), Math.max(...vals)];
    $("#tiempos").innerHTML = `<p class="pequeno tenue">Horas · calculado con <b>${alg === "floyd" ? "Floyd-Warshall O(V³)" : "Johnson O(V·E log V)"}</b> en ${t.ms} ms. Ambos dan la misma matriz.</p>
      <div class="scroll" style="max-height:none"><table class="matriz calor"><tr><th></th>${t.puntos.map(p => `<th title="${esc(t.nombres[t.puntos.indexOf(p)])}">${p}</th>`).join("")}</tr>
      ${t.matriz.map((fila, i) => `<tr><th>${t.puntos[i]}</th>${fila.map(v => `<td style="background:${v ? colorCalor(v, mn, mx) : "transparent"};color:${v > (mn + mx) / 2 ? "#fff" : "#1f2533"}">${v ? fmt(v, 1) : "0"}</td>`).join("")}</tr>`).join("")}</table></div>`;
  },
};

let INICIAR_RUTAS_PROMESA = null;
INICIAR.rutas = () => {
  INICIAR_RUTAS_PROMESA = (async () => {
    await Rutas.cargarRed("");
    const opciones = Rutas.red.nodos.map(n => `<option value="${n.id}">${n.id} — ${esc(n.nombre)}</option>`).join("");
    $("#ruta-origen").innerHTML = opciones; $("#ruta-destino").innerHTML = opciones;
    $("#ruta-escenario").innerHTML = Rutas.red.escenarios.map((e, i) => `<option value="${i}">${esc(e.titulo)} (${soles(e.monto, 0)})</option>`).join("");
    Rutas.selector = segmentado("ruta-variante", v => Rutas.cambiarVariante(v));
    $("#ruta-escenario").addEventListener("change", e => Rutas.escenario(+e.target.value));
    ["ruta-origen", "ruta-destino"].forEach(id => $("#" + id).addEventListener("change", () => Rutas.consultar()));
    $("#ruta-monto").addEventListener("input", () => {
      Rutas.montoExacto = null;
      Rutas.actualizarMontoTexto();
      clearTimeout(Rutas.temporizador);
      Rutas.temporizador = setTimeout(() => Rutas.consultar(), 180);
    });
    segmentado("tiempos-alg", v => Rutas.tiempos(v));
    await Rutas.escenario(0);
    await Rutas.tiempos("floyd");
  })();
  return INICIAR_RUTAS_PROMESA;
};

/* ================================================================ MÓDULO 4 */
const Liq = {
  cerrados: [], plan: null, troncal: null, pos: null,
  estado() {
    return { temporada: this.sTemporada.valor(), metodo: this.sMetodo.valor(), cerrados: this.cerrados,
      umbral_riesgo: $("#liq-riesgo").value ? +$("#liq-riesgo").value : null };
  },
  async calcular() {
    cargando($("#liq-corte"));
    const [plan, troncal] = await Promise.all([api("liquidez", this.estado()),
      api("troncal?cerrados=" + encodeURIComponent(JSON.stringify(this.cerrados)))]);
    this.plan = plan; this.troncal = troncal;
    this.render();
  },
  async huaico() {
    if (!this.sTemporada) await INICIAR_LIQ_PROMESA;
    if (!this.cerrados.some(p => p.join() === "OLL,SMA")) this.cerrados.push(["OLL", "SMA"]);
    this.sTemporada.fijar("alta");
    aviso("⚠ Huaico: se cerró el tramo Ollantaytambo – Santa María (Abra Málaga)");
    await this.calcular();
  },
  async reiniciar() {
    if (!this.sTemporada) await INICIAR_LIQ_PROMESA;
    this.cerrados = []; this.sTemporada.fijar("alta"); this.sMetodo.fijar("costo_minimo"); $("#liq-riesgo").value = "";
    await this.calcular();
  },
  alternarTramo(a) {
    const clave = [a.u, a.v].sort().join(",");
    const i = this.cerrados.findIndex(p => [...p].sort().join(",") === clave);
    if (i >= 0) { this.cerrados.splice(i, 1); aviso(`Tramo ${a.u} – ${a.v} reabierto`); }
    else { this.cerrados.push([a.u, a.v]); aviso(`Tramo ${a.u} – ${a.v} cerrado`); }
    this.calcular();
  },
  render() {
    const p = this.plan, t = this.troncal;
    $("#liq-kpis").innerHTML = [
      kpi(`S/ ${fmt(p.flujo_maximo)} mil`, "Efectivo distribuido", `de S/ ${fmt(p.demanda_total)} mil de demanda`, "azul"),
      `<div class="tarjeta kpi ${p.cobertura_pct < 100 ? "ambar" : "verde"}"><div class="etiqueta">Cobertura</div><div class="valor">${fmt(p.cobertura_pct, 1)} %</div>
        <div class="barra-progreso mt"><div style="width:${p.cobertura_pct}%;background:${p.cobertura_pct < 95 ? "var(--rojo)" : p.cobertura_pct < 100 ? "var(--ambar)" : "var(--verde)"}"></div></div></div>`,
      kpi(`S/ ${fmt(p.costo_total)} mil`, "Costo de traslado", this.sMetodo.valor() === "costo_minimo" ? "mínimo posible (Bellman-Ford en la red residual)" : "compare con «Costo mínimo»", "acento"),
      kpi(`${fmt(p.ms, 1)} ms`, p.algoritmo.split(" (")[0], `${p.aumentos} caminos aumentantes · ${p.verificacion.length ? "⚠ flujo inválido" : "✔ capacidad y conservación"}`, "verde"),
    ].join("");

    // mapa
    const nodos = p.nodos;
    if (!this.pos) this.pos = posicionesGeograficas(nodos, 1000, 760);
    const tramos = {};
    p.tramos.forEach(x => { tramos[[x.u, x.v].sort().join("|")] = x; });
    const cerrados = new Set(this.cerrados.map(c => [...c].sort().join("|")));
    const corte = new Set(p.corte.filter(c => c[0] === "ruta").map(c => c[1].split(" (")[0].split(" -> ").sort().join("|")));
    const enTroncal = new Set(t.aristas.map(a => [a.u, a.v].sort().join("|")));
    const pendientes = {};
    p.pendientes.forEach(d => { pendientes[d.nodo] = d; });
    const verTroncal = $("#liq-troncal").checked, verCriticos = $("#liq-criticos").checked;
    const maxFlujo = Math.max(1, ...p.tramos.map(x => x.flujo));
    const aristas = p.fisicas.map(a => {
      const tr = tramos[[a.u, a.v].sort().join("|")];
      return tr && tr.flujo > 0 ? { ...a, u: tr.desde, v: tr.hacia, _tr: tr } : { ...a, _tr: tr };
    });
    const cont = $("#liq-mapa");
    dibujarRed(cont, {
      nodos, aristas, dirigido: false, pos: this.pos, W: 1000, H: 760,
      estiloArista: a => {
        const clave = [a.u, a.v].sort().join("|"), tr = a._tr;
        if (cerrados.has(clave)) return { color: "#c0392b", ancho: 3, guiones: "3 6", opacidad: 1, etiqueta: "✕ cerrado", colorEtiqueta: "#c0392b", negritaEtiqueta: true };
        if (verTroncal && !enTroncal.has(clave)) return { color: "var(--tenue)", ancho: 1.2, opacidad: 0.25, guiones: "2 4" };
        if (!tr || tr.flujo === 0) return { ...estiloBaseArista(a), opacidad: 0.35, color: verTroncal ? "#1f2533" : estiloBaseArista(a).color };
        const uso = tr.uso_pct;
        const color = uso >= 100 ? "#c0392b" : uso >= 70 ? "#c27a2c" : "#2f7d4f";
        return { color, ancho: 2 + 8 * Math.sqrt(tr.flujo / maxFlujo), opacidad: 0.9, clase: "flujo-anim",
          resalte: corte.has(clave) ? "rgba(192,57,43,.28)" : null,
          etiqueta: corte.has(clave) ? `corte: ${fmt(tr.flujo)}/${fmt(tr.capacidad)}` : (uso >= 100 ? "saturada" : ""),
          colorEtiqueta: "#c0392b", negritaEtiqueta: true };
      },
      estiloNodo: n => {
        if (pendientes[n.id]) return { halo: "#c0392b", r: radioNodo(n) + 3 };
        if (verCriticos && t.criticos[n.id]) return { halo: "#6a4c9c", haloPulso: false };
        return {};
      },
      etiquetaNodo: n => n.id,
      globoNodo: n => globoNodoFisico(n) + (pendientes[n.id] ? `<br><b>Demanda no cubierta: S/ ${fmt(pendientes[n.id].pendiente)} mil</b>` : "") +
        (t.criticos[n.id] ? `<br>Punto crítico: aísla ${t.criticos[n.id].join(", ")}` : ""),
      globoArista: a => {
        const tr = a._tr;
        return globoAristaFisica(a) + (tr ? `<br><b>Flujo: S/ ${fmt(tr.flujo)} mil</b> (${tr.desde} → ${tr.hacia})<br>Capacidad: ${fmt(tr.capacidad)} · uso ${fmt(tr.uso_pct, 1)} %` : "") + "<br><i>Clic para cerrar / reabrir</i>";
      },
      alClicArista: a => this.alternarTramo(a),
    });
    leyenda(cont, [["#2f7d4f", "Uso < 70 %", true], ["#c27a2c", "Uso 70–99 %", true], ["#c0392b", "Saturada / cerrada", true],
      ["rgba(192,57,43,.4)", "Corte mínimo", true], ["#c0392b", "Demanda pendiente"]]);

    $("#liq-corte").innerHTML = p.corte.length ? p.corte.map(([tipo, desc, cap]) =>
      `<div style="padding:6px 0;border-bottom:1px dashed var(--linea)"><span class="insignia ${tipo === "ruta" ? "rojo" : tipo === "oferta" ? "ambar" : ""}">${tipo}</span> ${esc(desc)} <b style="float:right">${fmt(cap)}</b></div>`).join("")
      + `<div class="porque mt"><b class="t">Teorema flujo máximo = corte mínimo</b>Capacidad del corte = S/ ${fmt(p.capacidad_corte)} mil = flujo máximo. Ampliar estas rutas es lo único que aumenta la distribución.</div>`
      : '<div class="exito">Toda la demanda se cubre: el corte mínimo está en los arcos de demanda.</div>';
    $("#liq-pendientes").innerHTML = p.pendientes.length
      ? `<table class="tabla"><thead><tr><th>Punto</th><th class="num">Demanda</th><th class="num">Recibe</th><th class="num">Falta</th></tr></thead><tbody>${p.pendientes.map(d =>
          `<tr><td>${d.nodo}</td><td class="num">${fmt(d.demanda)}</td><td class="num">${fmt(d.recibido)}</td><td class="num"><b style="color:var(--rojo)">${fmt(d.pendiente)}</b></td></tr>`).join("")}</tbody></table><p class="pequeno tenue">Miles de soles.</p>`
      : '<div class="exito">✔ Ningún punto queda desabastecido.</div>';
    $("#liq-almacenes").innerHTML = p.almacenes.map(a => `<div style="margin-bottom:8px"><div class="pequeno"><b>${a.boveda}</b> <span class="tenue" style="float:right">${fmt(a.uso)} / ${fmt(a.capacidad)}</span></div>
      <div class="barra-progreso"><div style="width:${100 * a.uso / a.capacidad}%;background:${a.uso >= a.capacidad ? "var(--rojo)" : "var(--azul)"}"></div></div></div>`).join("")
      + '<p class="pequeno tenue">Cada bóveda regional se divide en <code>v::entrada → v::salida</code> con capacidad = almacenamiento.</p>';
    $("#liq-rutas").innerHTML = `<table class="tabla"><thead><tr><th>Ruta</th><th class="num">Flujo</th><th class="num">Capacidad</th><th class="num">Uso</th><th class="num">Costo</th></tr></thead><tbody>${
      p.rutas.filter(r => r.flujo > 0).slice(0, 25).map(r => `<tr><td>${r.origen} → ${r.destino}</td><td class="num">${fmt(r.flujo)}</td><td class="num">${fmt(r.capacidad)}</td><td class="num">${fmt(r.uso_pct, 1)} %</td><td class="num">${fmt(r.costo)}</td></tr>`).join("")}</tbody></table>`;
    const criticos = Object.entries(t.criticos).sort((a, b) => b[1].length - a[1].length);
    $("#liq-troncal-info").innerHTML = `<p><span class="insignia">Kruskal (G8) · O(E log E)</span> Riesgo total de la red troncal: <b>${t.costo}</b> con ${t.aristas.length} tramos.</p>
      <p class="pequeno">Tramos que quedan fuera (alternativos, de mayor riesgo): ${t.fuera.map(f => `<span class="insignia gris">${f.u}–${f.v} (${f.riesgo})</span>`).join(" ")}</p>
      ${t.componentes > 1 ? `<div class="alerta">La red quedó dividida en ${t.componentes} partes.</div>` : ""}
      <p class="mt"><b>Puntos críticos</b> (eliminación + BFS): ${criticos.slice(0, 10).map(([n, s]) => `<span class="insignia rojo" title="Aísla: ${s.join(", ")}">${n} (${s.length})</span>`).join(" ")}</p>`;
  },
};

let INICIAR_LIQ_PROMESA = null;
INICIAR.liquidez = () => {
  INICIAR_LIQ_PROMESA = (async () => {
    Liq.sTemporada = segmentado("liq-temporada", () => Liq.calcular());
    Liq.sMetodo = segmentado("liq-metodo", () => Liq.calcular());
    $("#liq-riesgo").addEventListener("change", () => Liq.calcular());
    $("#btn-huaico").addEventListener("click", () => Liq.huaico());
    $("#btn-reabrir").addEventListener("click", () => { Liq.cerrados = []; Liq.calcular(); aviso("Todos los tramos reabiertos"); });
    ["liq-troncal", "liq-criticos"].forEach(id => $("#" + id).addEventListener("change", () => Liq.render()));
    await Liq.calcular();
  })();
  return INICIAR_LIQ_PROMESA;
};

/* ================================================================ MÓDULO 5 */
INICIAR.evaluacion = async () => {
  cargando($("#eval-validacion"));
  const v = await api("validacion");
  const ok = v.casos.filter(c => c.ok).length;
  const mostrar = x => esc(typeof x === "object" ? JSON.stringify(x) : String(x));
  $("#eval-validacion").innerHTML = `
    <div class="${ok === v.casos.length ? "exito" : "alerta"}" style="font-size:1.05rem"><b>${ok} de ${v.casos.length}</b> casos con resultado esperado conocido son correctos.</div>
    <table class="tabla mt"><thead><tr><th></th><th>Caso</th><th>Esperado</th><th>Obtenido</th></tr></thead><tbody>${v.casos.map(c =>
      `<tr><td>${c.ok ? '<span class="insignia verde">✔</span>' : '<span class="insignia rojo">✖</span>'}</td><td>${esc(c.caso)}</td><td class="pequeno"><code>${mostrar(c.esperado)}</code></td><td class="pequeno"><code>${mostrar(c.obtenido)}</code></td></tr>`).join("")}</tbody></table>
    <p class="pequeno tenue mt">Además, <code>python -m pytest</code> ejecuta 77 pruebas automatizadas (ejemplos de las guías 7 a 11 incluidos).</p>`;
  const sModo = segmentado("cmp-modo", () => {});
  $("#btn-cmp").addEventListener("click", async () => {
    const cont = $("#cmp-resultado");
    cargando(cont, sModo.valor() === "completo" ? "Ejecutando comparación completa… puede tardar varios minutos" : "Ejecutando comparación…");
    $("#btn-cmp").disabled = true;
    try {
      const r = await api("comparacion", { modo: sModo.valor() });
      const grupos = [...new Set(r.filas.map(f => f.comparacion))];
      cont.innerHTML = `<div class="rejilla r3" id="cmp-graficos"></div>
        <table class="tabla mt"><thead><tr><th>Comparación</th><th>Algoritmo</th><th class="num">V</th><th class="num">E</th><th>Complejidad</th><th class="num">ms</th><th class="num">KB</th><th>Resultado</th><th>Coinciden</th></tr></thead><tbody>${
          r.filas.map(f => `<tr><td>${f.comparacion}</td><td><b>${f.algoritmo}</b></td><td class="num">${f.V}</td><td class="num">${f.E}</td><td><code>${f.complejidad}</code></td><td class="num">${fmt(f.tiempo_ms, 2)}</td><td class="num">${fmt(f.memoria_kb, 1)}</td><td>${esc(f.resultado)}</td><td>${f.coincide ? '<span class="insignia verde">sí</span>' : '<span class="insignia rojo">no</span>'}</td></tr>`).join("")}</tbody></table>`;
      for (const g of grupos) {
        const div = document.createElement("div");
        div.className = "tarjeta";
        $("#cmp-graficos").appendChild(div);
        const algs = [...new Set(r.filas.filter(f => f.comparacion === g).map(f => f.algoritmo))];
        graficoLineas(div, { titulo: g, ejeX: "Nodos (V)", ejeY: "Tiempo (ms)",
          series: algs.map(a => ({ nombre: `${a}  ${r.filas.find(f => f.algoritmo === a).complejidad}`,
            puntos: r.filas.filter(f => f.algoritmo === a).map(f => [f.V, f.tiempo_ms]) })) });
      }
      $("#cmp-graficos").insertAdjacentHTML("beforeend", `<div class="tarjeta"><h3>Lectura de resultados</h3>
        <p class="pequeno">• <b>Dijkstra</b> supera a Bellman-Ford: O((V+E) log V) frente a O(V·E).</p>
        <p class="pequeno">• <b>Floyd-Warshall</b> gana en redes pequeñas, pero su O(V³) crece rápido: <b>Johnson</b> lo supera en redes dispersas grandes.</p>
        <p class="pequeno">• <b>Tarjan</b> usa menos memoria que Kosaraju (una pasada, sin transpuesto).</p>
        <p class="pequeno">• <b>Edmonds-Karp</b> necesita muchos menos caminos aumentantes que Ford-Fulkerson con DFS.</p></div>`);
    } finally { $("#btn-cmp").disabled = false; }
  });
  alCambiarPestana.eval = async tab => {
    if (tab === "comparacion" && !$("#cmp-resultado").innerHTML) $("#btn-cmp").click();
    if (tab === "huaico" && !$("#eval-huaico").innerHTML) {
      cargando($("#eval-huaico"));
      const h = await api("huaico");
      const flecha = (a, b, unidad = "", mejor = "menor") => {
        const sube = b > a; const malo = mejor === "menor" ? sube : !sube;
        return `<span>${fmt(a, unidad === "h" ? 2 : 0)}${unidad}</span> <span class="tenue">→</span> <b style="color:${malo ? "var(--rojo)" : "var(--verde)"}">${fmt(b, unidad === "h" ? 2 : 0)}${unidad}</b>`;
      };
      $("#eval-huaico").innerHTML = `
        <p>Escenario de contingencia: un <b>huaico cierra Abra Málaga</b> (tramo Ollantaytambo – Santa María) en plena temporada alta. Se recalculan rutas, puntos críticos y flujo máximo.</p>
        <div class="rejilla r4">
          ${kpi(flecha(h.tiempo_cusco_quillabamba[0], h.tiempo_cusco_quillabamba[1], " h"), "Tiempo Cusco → Quillabamba", "Floyd-Warshall: ahora por tren y Santa Teresa", "azul")}
          ${kpi(flecha(h.flujo[0], h.flujo[1], "", "mayor"), "Efectivo distribuido (miles S/)", "Edmonds-Karp / costo mínimo", "ambar")}
          ${kpi(flecha(h.pendiente[0], h.pendiente[1]), "Demanda no cubierta (miles S/)", "", "acento")}
          ${kpi(h.nuevos_criticos.join(", ") || "—", "Nuevos puntos críticos", "eliminación + BFS", "acento")}
        </div>
        <div class="rejilla r2 mt">
          <div><h3>Puntos sin abastecer</h3><table class="tabla"><tbody>${h.pendientes_despues.map(d => `<tr><td>${d.nodo}</td><td class="num">faltan <b>${fmt(d.pendiente)}</b> de ${fmt(d.demanda)}</td></tr>`).join("")}</tbody></table></div>
          <div><h3>Nuevo corte mínimo</h3>${h.corte_despues.map(([t, d, c]) => `<div><span class="insignia ${t === "ruta" ? "rojo" : "ambar"}">${t}</span> ${esc(d)}: <b>${fmt(c)}</b></div>`).join("")}
          <div class="porque mt"><b class="t">Interpretación</b>Quillabamba no queda aislada, pero ahora depende del tren Ollantaytambo – Machupicchu, que compite con la demanda turística de Machupicchu Pueblo.</div></div>
        </div>
        <p class="mt"><button class="btn primario" id="btn-ver-huaico">Ver el huaico en el mapa del módulo 4 ▸</button></p>`;
      $("#btn-ver-huaico").addEventListener("click", async () => { await ir("liquidez"); Liq.huaico(); });
    }
  };
};

/* ================================================================ ANIMACIÓN */
const PSEUDO = {
  bfs: ["marcar(origen); cola.encolar(origen)", "mientras la cola no esté vacía:", "    u = cola.desencolar()          # visitar",
    "    para cada vecino v de u:", "        si v no fue marcado:", "            marcar(v); nivel[v] = nivel[u] + 1", "            cola.encolar(v)"],
  dijkstra: ["dist[origen] = 0; cola = {(0, origen)}", "mientras la cola no esté vacía:", "    u = extraer el de menor distancia",
    "    si u ya está cerrado: continuar", "    para cada arista (u, v, w):", "        si dist[u] + w < dist[v]:   # relajación",
    "            dist[v] = dist[u] + w; anterior[v] = u"],
  kruskal: ["ordenar aristas de menor a mayor peso", "para cada arista (u, v):", "    si find(u) != find(v):        # no forma ciclo",
    "        union(u, v); agregar al árbol", "    si no: descartar (formaría ciclo)", "    parar al tener |V| - 1 aristas"],
  edmonds_karp: ["flujo = 0", "mientras BFS encuentre un camino s -> t con capacidad residual:", "    c = menor capacidad residual del camino",
    "    enviar c por el camino (y sumar c a los arcos inversos)", "    flujo = flujo + c", "devolver flujo     # = capacidad del corte mínimo"],
  floyd: ["dist = matriz de adyacencia (inf si no hay arista)", "para cada k (nodo intermedio):", "    para cada i:", "        para cada j:",
    "            si dist[i][k] + dist[k][j] < dist[i][j]:", "                dist[i][j] = dist[i][k] + dist[k][j]"],
};
const NOMBRE_ALG = { bfs: "BFS – búsqueda en anchura (Guía 7)", dijkstra: "Dijkstra (Guía 9)", kruskal: "Kruskal (Guía 8)",
  edmonds_karp: "Edmonds-Karp (Guía 11)", floyd: "Floyd-Warshall (Guía 10)" };

const Ani = {
  datos: null, paso: 0, timer: null, pos: null, alg: "bfs", red: "guia",

  async cargar(alg = this.alg, red = this.red, origen = null) {
    if (!this.sAlg) await INICIAR.animacionPromesa;
    this.pausar();
    this.alg = alg; this.red = alg === "floyd" ? "guia" : red;
    this.sAlg.fijar(this.alg); this.sRed.fijar(this.red);
    this.datos = await api(`animacion?algoritmo=${alg}&red=${this.red}${origen ? "&origen=" + origen : ""}`);
    const d = this.datos;
    const W = d.layout === "mapa" ? 1000 : 620, H = d.layout === "mapa" ? 760 : 330;
    this.W = W; this.H = H;
    this.pos = d.layout === "mapa" ? posicionesGeograficas(d.nodos, W, H) : posicionesXY(d.nodos, W, H, 45);
    $("#ani-titulo").textContent = NOMBRE_ALG[alg] + " · " + d.titulo;
    $("#ani-desc").textContent = d.descripcion;
    $("#ani-origen-campo").style.visibility = ["bfs", "dijkstra"].includes(alg) ? "visible" : "hidden";
    $("#ani-origen").innerHTML = d.nodos.map(n => `<option ${n.id === d.origen ? "selected" : ""}>${n.id}</option>`).join("");
    this.paso = 0;
    this.dibujar();
  },
  total() { return this.datos.pasos.length; },
  ir(p) { this.paso = Math.max(0, Math.min(this.total(), p)); this.dibujar(); },
  reproducir() {
    if (this.timer) return this.pausar();
    if (this.paso >= this.total()) this.paso = 0;
    $("#ani-play").textContent = "⏸ Pausar";
    const avanzar = () => {
      if (this.paso >= this.total()) return this.pausar();
      this.ir(this.paso + 1);
      this.timer = setTimeout(avanzar, 2300 - 210 * +$("#ani-vel").value);
    };
    this.timer = setTimeout(avanzar, 200);
  },
  pausar() { clearTimeout(this.timer); this.timer = null; $("#ani-play").textContent = "▶ Reproducir"; },

  /* Reconstruye el estado del algoritmo hasta el paso actual. */
  estado() {
    const d = this.datos, pasos = d.pasos.slice(0, this.paso), ultimo = pasos[pasos.length - 1];
    const e = { ultimo, linea: 0, texto: "", nivel: {}, visitados: new Set(), arbol: new Set(), dist: {}, cerrados: new Set(),
      anterior: {}, aceptadas: new Set(), rechazadas: new Set(), costo: 0, flujo: {}, total: 0, cola: [], actualArista: null, camino: [] };
    const clave = (u, v) => d.dirigido ? u + "|" + v : [u, v].sort().join("|");
    if (this.alg === "bfs") {
      e.nivel[d.origen] = 0; e.cola = [d.origen];
      for (const p of pasos) {
        if (p.tipo === "visitar") { e.visitados.add(p.nodo); e.cola.shift(); }
        else { e.nivel[p.nodo] = p.nivel; e.arbol.add(clave(p.desde, p.nodo)); e.cola.push(p.nodo); }
      }
      if (ultimo) {
        e.linea = ultimo.tipo === "visitar" ? 2 : 5;
        e.texto = ultimo.tipo === "visitar" ? `Se desencola y visita <b>${ultimo.nodo}</b> (nivel ${ultimo.nivel}).`
          : `Desde <b>${ultimo.desde}</b> se descubre <b>${ultimo.nodo}</b>: nivel ${ultimo.nivel}. Se encola.`;
        if (ultimo.tipo === "descubrir") e.actualArista = clave(ultimo.desde, ultimo.nodo);
      }
    } else if (this.alg === "dijkstra") {
      e.dist[d.origen] = 0;
      for (const p of pasos) {
        if (p.tipo === "cerrar") e.cerrados.add(p.nodo);
        else { e.dist[p.nodo] = p.distancia; e.anterior[p.nodo] = p.desde; }
      }
      for (const n of e.cerrados) if (e.anterior[n]) e.arbol.add(clave(e.anterior[n], n));
      if (ultimo) {
        e.linea = ultimo.tipo === "cerrar" ? 2 : 6;
        e.texto = ultimo.tipo === "cerrar" ? `Se extrae <b>${ultimo.nodo}</b> con distancia <b>${fmt(ultimo.distancia, 2)}</b> (la menor de la cola) y queda cerrado.`
          : `Relajación: dist[<b>${ultimo.nodo}</b>] mejora de ${ultimo.antes === null ? "∞" : fmt(ultimo.antes, 2)} a <b>${fmt(ultimo.distancia, 2)}</b> pasando por ${ultimo.desde}.`;
        if (ultimo.tipo === "relajar") e.actualArista = clave(ultimo.desde, ultimo.nodo);
      }
    } else if (this.alg === "kruskal") {
      for (const p of pasos) {
        (p.tipo === "aceptar" ? e.aceptadas : e.rechazadas).add(clave(p.u, p.v));
        e.costo = p.costo;
      }
      if (ultimo) {
        e.linea = ultimo.tipo === "aceptar" ? 3 : 4;
        e.actualArista = clave(ultimo.u, ultimo.v);
        e.texto = ultimo.tipo === "aceptar" ? `Arista <b>${ultimo.u} – ${ultimo.v}</b> (peso ${ultimo.peso}): une dos componentes distintas → se <b>acepta</b>. Costo acumulado: ${ultimo.costo}.`
          : `Arista <b>${ultimo.u} – ${ultimo.v}</b> (peso ${ultimo.peso}): sus extremos ya están conectados → formaría un <b>ciclo</b>, se descarta.`;
      }
    } else if (this.alg === "edmonds_karp") {
      for (const p of pasos) {
        for (let i = 1; i < p.camino.length; i++) {
          const u = p.camino[i - 1], v = p.camino[i];
          const directa = d.aristas.some(a => a.u === u && a.v === v);
          if (d.layout === "mapa") { const k = [u, v].sort().join("|"); e.flujo[k] = (e.flujo[k] || 0) + p.cantidad; }
          else if (directa) e.flujo[u + "|" + v] = (e.flujo[u + "|" + v] || 0) + p.cantidad;
          else e.flujo[v + "|" + u] = (e.flujo[v + "|" + u] || 0) - p.cantidad;
        }
        e.total = p.total;
      }
      if (ultimo) {
        e.linea = 3; e.camino = ultimo.camino;
        e.texto = `Camino aumentante #${this.paso}: ${ultimo.camino.join(" → ")}. Cuello de botella = <b>${fmt(ultimo.cantidad)}</b>. Flujo total = <b>${fmt(ultimo.total)}</b>.`;
      }
    } else if (this.alg === "floyd") {
      e.matriz = (ultimo || d.pasos[0]).matriz; e.cambios = ultimo ? ultimo.cambios : []; e.k = ultimo?.k;
      if (ultimo) {
        e.linea = ultimo.tipo === "inicio" ? 0 : 5;
        e.texto = ultimo.tipo === "inicio" ? "Matriz inicial: peso de cada arista directa, ∞ si no hay arista, 0 en la diagonal."
          : `k = <b>${ultimo.k}</b>: se prueba ${ultimo.k} como intermediario. <b>${ultimo.cambios.length}</b> distancia(s) mejoran.`;
      }
    }
    if (this.paso === 0) e.texto = "Estado inicial. Presione ▶ Reproducir o avance con ▶|.";
    if (this.paso === this.total() && this.total()) {
      e.linea = PSEUDO[this.alg].length - 1;
      const r = d.resultado;
      e.texto = {
        bfs: `Recorrido completo: ${e.visitados.size} nodos alcanzados en ${Math.max(...Object.values(e.nivel)) + 1} niveles.`,
        dijkstra: "Fin: todas las distancias mínimas desde el origen están calculadas (árbol de caminos mínimos en verde).",
        kruskal: `Árbol de expansión mínima: <b>${r.aristas}</b> aristas (V − 1) y costo total <b>${r.costo}</b>.`,
        edmonds_karp: `No quedan caminos aumentantes: <b>flujo máximo = ${fmt(r.flujo_maximo)}</b> con ${r.aumentos} aumentos.`,
        floyd: "Matriz final de caminos mínimos entre todos los pares. Por ejemplo, A → X cuesta 8 (A→C→D→E→X).",
      }[this.alg];
    }
    return e;
  },

  dibujar() {
    const d = this.datos, e = this.estado();
    $("#ani-contador").textContent = `${this.paso} / ${this.total()}`;
    $("#ani-narracion").innerHTML = e.texto;
    $("#ani-pseudo").innerHTML = PSEUDO[this.alg].map((l, i) => `<div class="${i === e.linea && this.paso ? "activa" : ""}">${esc(l)}</div>`).join("");
    const clave = (u, v) => d.dirigido ? u + "|" + v : [u, v].sort().join("|");
    const mapa = d.layout === "mapa";
    const enCamino = new Set(e.camino.slice(1).map((n, i) => mapa ? [e.camino[i], n].sort().join("|") : e.camino[i] + "|" + n));
    const maxFlujo = Math.max(1, ...Object.values(e.flujo));
    const cont = $("#ani-lienzo");
    dibujarRed(cont, {
      nodos: d.nodos, aristas: d.aristas, dirigido: d.dirigido, pos: this.pos, W: this.W, H: this.H,
      estiloArista: a => {
        const k = clave(a.u, a.v), kMapa = [a.u, a.v].sort().join("|");
        const etq = mapa ? "" : (a.peso ?? "");
        const base = mapa ? { ...estiloBaseArista(a), opacidad: 0.35 } : { color: "var(--tenue)", ancho: 2, opacidad: 0.7, etiqueta: etq };
        if (this.alg === "bfs" || this.alg === "dijkstra") {
          if (k === e.actualArista) return { ...base, color: "#c27a2c", ancho: 5, opacidad: 1, negritaEtiqueta: true };
          if (e.arbol.has(k)) return { ...base, color: "#2f7d4f", ancho: 4, opacidad: 1 };
        }
        if (this.alg === "kruskal") {
          if (k === e.actualArista) return { ...base, color: e.ultimo.tipo === "aceptar" ? "#2f7d4f" : "#c0392b", ancho: 6, opacidad: 1, resalte: "rgba(194,122,44,.35)", etiqueta: mapa ? a.peso : etq };
          if (e.aceptadas.has(k)) return { ...base, color: "#2f7d4f", ancho: 4, opacidad: 1, etiqueta: mapa ? "" : etq };
          if (e.rechazadas.has(k)) return { ...base, color: "#c0392b", guiones: "4 4", opacidad: 0.6 };
          return mapa ? base : { ...base, etiqueta: etq };
        }
        if (this.alg === "edmonds_karp") {
          const f = mapa ? (e.flujo[kMapa] || 0) : (e.flujo[a.u + "|" + a.v] || 0);
          const actual = mapa ? enCamino.has(kMapa) : enCamino.has(a.u + "|" + a.v);
          const est = { ...base, etiqueta: mapa ? (actual ? fmt(e.ultimo.cantidad) : "") : `${f}/${a.peso}` };
          if (actual) return { ...est, color: "#c27a2c", ancho: 6, opacidad: 1, clase: "flujo-anim", negritaEtiqueta: true, colorEtiqueta: "#c27a2c" };
          if (f > 0) return { ...est, color: "#2b5a8a", ancho: 2 + 6 * Math.sqrt(f / maxFlujo), opacidad: 0.9 };
          return est;
        }
        if (this.alg === "floyd" && e.k && (a.u === e.k || a.v === e.k)) return { ...base, color: "#2b5a8a", ancho: 3.5, opacidad: 1 };
        return base;
      },
      estiloNodo: n => {
        if (this.alg === "bfs") {
          if (e.nivel[n.id] === undefined) return { color: "#a3a8b0", opacidad: mapa ? 0.6 : 1 };
          const color = PALETA_NIVELES[e.nivel[n.id] % PALETA_NIVELES.length];
          const actual = e.ultimo && e.ultimo.nodo === n.id;
          return { color, vacio: !e.visitados.has(n.id), halo: actual ? "#c27a2c" : null, subetiqueta: mapa ? null : String(e.nivel[n.id]), r: mapa ? undefined : 16 };
        }
        if (this.alg === "dijkstra") {
          const dist = e.dist[n.id];
          const actual = e.ultimo && e.ultimo.nodo === n.id;
          return { color: e.cerrados.has(n.id) ? "#2f7d4f" : dist !== undefined ? "#c27a2c" : "#a3a8b0", vacio: dist !== undefined && !e.cerrados.has(n.id),
            halo: actual ? "#c27a2c" : null, r: mapa ? undefined : 16 };
        }
        if (this.alg === "edmonds_karp") return { halo: e.camino.includes(n.id) ? "#c27a2c" : null, r: mapa ? undefined : 16, color: ["s", "t"].includes(n.id) ? "#9b2c2c" : undefined };
        if (this.alg === "floyd") return { halo: n.id === e.k ? "#2b5a8a" : null, r: 16 };
        return mapa ? {} : { r: 16 };
      },
      etiquetaNodo: n => {
        if (this.alg === "dijkstra" && !mapa) return `${n.id}  d=${e.dist[n.id] === undefined ? "∞" : fmt(e.dist[n.id], 1)}`;
        if (this.alg === "dijkstra" && mapa) return e.dist[n.id] !== undefined ? `${n.id} ${fmt(e.dist[n.id], 1)}h` : n.id;
        return n.id;
      },
      globoNodo: n => `<b>${esc(n.nombre || n.id)}</b>` + (this.alg === "dijkstra" ? `<br>dist = ${e.dist[n.id] === undefined ? "∞" : fmt(e.dist[n.id], 2)}` : "") + (this.alg === "bfs" && e.nivel[n.id] !== undefined ? `<br>nivel ${e.nivel[n.id]}` : ""),
      globoArista: a => `${a.u} – ${a.v}${a.peso !== null && a.peso !== undefined ? `<br>peso: ${a.peso}` : ""}`,
    });
    this.dibujarEstado(e);
  },

  dibujarEstado(e) {
    const d = this.datos, el = $("#ani-estado");
    if (this.alg === "bfs") {
      const porNivel = {};
      Object.entries(e.nivel).forEach(([n, l]) => { (porNivel[l] = porNivel[l] || []).push(n); });
      el.innerHTML = `<p><b>Cola (FIFO):</b> ${e.cola.length ? e.cola.map(c => `<span class="insignia ambar">${c}</span>`).join(" ") : "<span class='tenue'>vacía</span>"}</p>
        ${Object.entries(porNivel).map(([l, ns]) => `<p class="pequeno"><span class="insignia" style="background:${PALETA_NIVELES[l % 8]}22;color:${PALETA_NIVELES[l % 8]}">Nivel ${l}</span> ${ns.join(", ")}</p>`).join("")}
        <p class="pequeno tenue">Relleno = visitado · borde = descubierto en la cola.</p>`;
    } else if (this.alg === "dijkstra") {
      const filas = d.nodos.map(n => [n.id, e.dist[n.id], e.cerrados.has(n.id), e.anterior[n.id]]).sort((a, b) => (a[1] ?? 1e9) - (b[1] ?? 1e9));
      el.innerHTML = `<div class="scroll"><table class="tabla"><thead><tr><th>Nodo</th><th class="num">dist</th><th>Anterior</th><th>Estado</th></tr></thead><tbody>${
        filas.map(([n, dd, c, a]) => `<tr><td><b>${n}</b></td><td class="num">${dd === undefined ? "∞" : fmt(dd, 2)}</td><td>${a || "—"}</td><td>${c ? '<span class="insignia verde">cerrado</span>' : dd !== undefined ? '<span class="insignia ambar">en cola</span>' : ""}</td></tr>`).join("")}</tbody></table></div>`;
    } else if (this.alg === "kruskal") {
      el.innerHTML = `<div class="rejilla r2">${kpi(e.costo, "Costo acumulado")}${kpi(`${e.aceptadas.size} / ${d.nodos.length - 1}`, "Aristas del árbol")}</div>
        <p class="pequeno mt"><span class="insignia verde">aceptadas ${e.aceptadas.size}</span> <span class="insignia rojo">descartadas por ciclo ${e.rechazadas.size}</span></p>
        <p class="pequeno tenue">Union-Find detecta en tiempo casi constante si los extremos ya están conectados.</p>`;
    } else if (this.alg === "edmonds_karp") {
      el.innerHTML = `<div class="rejilla r2">${kpi(fmt(e.total), "Flujo acumulado")}${kpi(this.paso, "Caminos aumentantes")}</div>
        <p class="pequeno tenue mt">${d.layout === "mapa" ? "Red de liquidez de Cusco en temporada alta (miles de S/). Las súper-fuente y súper-sumidero no se dibujan." : "Etiqueta de cada arista: flujo / capacidad."}</p>
        <div class="porque mt"><b class="t">¿Por qué BFS?</b>Elegir el camino con menos arcos garantiza O(V·E²), sin depender del valor del flujo.</div>`;
    } else if (this.alg === "floyd") {
      const orden = d.resultado.orden, m = e.matriz, cambios = new Set((e.cambios || []).map(([i, j]) => i + "," + j));
      const ki = e.k ? orden.indexOf(e.k) : -1;
      el.innerHTML = `<table class="matriz"><tr><th></th>${orden.map(o => `<th>${o}</th>`).join("")}</tr>${m.map((fila, i) =>
        `<tr><th>${orden[i]}</th>${fila.map((v, j) => `<td class="${cambios.has(i + "," + j) ? "cambio" : (i === ki || j === ki) ? "k" : ""}">${v === null ? "∞" : v}</td>`).join("")}</tr>`).join("")}</table>
        <p class="pequeno tenue mt">Celdas resaltadas: mejoraron al pasar por k. Fila y columna de k en azul.</p>`;
    }
  },
};

INICIAR.animacion = () => {
  INICIAR.animacionPromesa = (async () => {
    Ani.sAlg = segmentado("ani-alg", v => Ani.cargar(v, Ani.red));
    Ani.sRed = segmentado("ani-red", v => Ani.cargar(Ani.alg, v));
    $("#ani-origen").addEventListener("change", e => Ani.cargar(Ani.alg, Ani.red, e.target.value));
    $("#ani-play").addEventListener("click", () => Ani.reproducir());
    $("#ani-adelante").addEventListener("click", () => { Ani.pausar(); Ani.ir(Ani.paso + 1); });
    $("#ani-atras").addEventListener("click", () => { Ani.pausar(); Ani.ir(Ani.paso - 1); });
    $("#ani-inicio").addEventListener("click", () => { Ani.pausar(); Ani.ir(0); });
    $("#ani-fin").addEventListener("click", () => { Ani.pausar(); Ani.ir(Ani.total()); });
    document.addEventListener("keydown", e => {
      if (!$("#p-animacion").classList.contains("activa") || ["INPUT", "SELECT"].includes(e.target.tagName)) return;
      if (e.key === "ArrowRight") { Ani.pausar(); Ani.ir(Ani.paso + 1); }
      if (e.key === "ArrowLeft") { Ani.pausar(); Ani.ir(Ani.paso - 1); }
      if (e.key === " ") { e.preventDefault(); Ani.reproducir(); }
    });
  })();
  return INICIAR.animacionPromesa.then(() => Ani.cargar("bfs", "guia"));
};

/* ================================================================ REPORTES */
async function listarReportes() {
  const lista = await api("reportes");
  const icono = f => f.endsWith(".png") ? "🖼" : f.endsWith(".csv") ? "📊" : "📄";
  $("#lista-reportes").innerHTML = lista.length
    ? `<div class="rejilla r3">${lista.map(f => `<a class="tarjeta" style="text-decoration:none;padding:10px 14px" href="/reportes/${encodeURIComponent(f)}" target="_blank">${icono(f)} ${esc(f)}</a>`).join("")}</div>`
    : '<p class="tenue">Aún no hay reportes. Presione “Generar todos los reportes”.</p>';
}
INICIAR.reportes = async () => {
  await listarReportes();
  $("#btn-generar").addEventListener("click", async () => {
    $("#btn-generar").disabled = true;
    cargando($("#lista-reportes"), "Generando reportes, mapas y gráficas…");
    try { await api("generar_reportes", {}); aviso("Reportes generados en la carpeta reportes/"); }
    finally { $("#btn-generar").disabled = false; await listarReportes(); }
  });
};

/* ================================================================ arranque */
ir("inicio");
