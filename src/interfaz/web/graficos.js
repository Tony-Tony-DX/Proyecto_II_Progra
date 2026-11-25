/* Dibujo de grafos, mapas y gráficas con SVG (sin bibliotecas externas). */
"use strict";

const SVGNS = "http://www.w3.org/2000/svg";

function svgEl(tag, attrs = {}, padre = null) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) e.setAttribute(k, v);
  }
  if (padre) padre.appendChild(e);
  return e;
}

const COLOR_TIPO = {
  boveda_central: "#8e2a2a", boveda_regional: "#c97a2c", agencia: "#2f5d8a", cajero: "#5a8fc2",
  agente: "#3f8f6b", paso: "#a3a8b0", cuenta: "#2f5d8a", compensacion: "#6a4c9c", canal: "#6a4c9c",
  billetera: "#3f8f6b", efectivo: "#c97a2c", agencia_externa: "#46618a", tarjeta: "#8e2a2a",
  procesador: "#6a4c9c",
};
const NOMBRE_TIPO = {
  boveda_central: "Bóveda central", boveda_regional: "Bóveda regional", agencia: "Agencia",
  cajero: "Cajero", agente: "Agente corresponsal", paso: "Nodo de paso", cuenta: "Cuenta",
  compensacion: "Cámara de compensación", canal: "Canal", billetera: "Billetera digital",
  efectivo: "Efectivo", agencia_externa: "Agencia externa", tarjeta: "Tarjeta", procesador: "Procesador",
};
const PALETA_NIVELES = ["#9b2c2c", "#c27a2c", "#2f7d4f", "#2b5a8a", "#6a4c9c", "#46818a", "#8a6a46", "#5d6470"];
const PRIORIDAD = { boveda_central: 0, boveda_regional: 1, agencia: 2, agente: 3, paso: 4, cajero: 5 };

function sinIndefinidos(obj) {
  return Object.fromEntries(Object.entries(obj || {}).filter(([, v]) => v !== undefined));
}

function radioNodo(n) {
  if (n.r) return n.r;
  if (n.tipo === "boveda_central") return 13;
  if (n.tipo === "boveda_regional") return 10;
  if (n.tipo === "cajero" || n.tipo === "paso") return 6;
  return 8;
}

/* ------------------------------------------------------------ globo */
const Globo = {
  el: null,
  mostrar(evt, html) {
    this.el = this.el || document.getElementById("globo");
    this.el.innerHTML = html;
    this.el.style.display = "block";
    const x = Math.min(evt.clientX + 14, window.innerWidth - 300);
    this.el.style.left = x + "px";
    this.el.style.top = (evt.clientY + 14) + "px";
  },
  ocultar() { if (this.el) this.el.style.display = "none"; },
};

/* ------------------------------------------------------------ posiciones */
/* Proyección "ojo de pez" centrada en la bóveda central: conserva la dirección
   geográfica de cada nodo pero comprime las distancias largas (r' = r^0.5),
   así la ciudad de Cusco y el Valle Sagrado no quedan amontonados. */
function ojoDePez(nodos, exponente = 0.4) {
  const centro = nodos.find(n => n.tipo === "boveda_central") || nodos[0];
  const coslat = Math.cos((centro.lat * Math.PI) / 180);
  return nodos.map(n => {
    const dx = (n.lon - centro.lon) * coslat, dy = n.lat - centro.lat;
    const r = Math.hypot(dx, dy);
    if (r === 0) return { ...n, _x: 0, _y: 0 };
    const k = Math.pow(r, exponente) / r;
    return { ...n, _x: dx * k, _y: dy * k };
  });
}

/* Esquema de la red física de Cusco (como la Figura 1 de la problemática):
   respeta la orientación geográfica, pero separa las zonas densas para que
   se lea bien al proyectar. Coordenadas sobre un lienzo de 1000 x 780. */
const ESQUEMA_CUSCO = {
  ECH: [320, 50], QUI_AG: [500, 60], QUI_BR: [420, 95], SMA: [317, 175], STE: [230, 195], HID: [190, 275],
  MPP: [296, 370], ATM_MPP: [225, 425], OLL: [427, 322], ATM_OLL: [455, 390],
  URU_BR: [524, 300], URU_AG: [565, 240], ATM_URU: [630, 210], CHI: [560, 385], CAL: [650, 280],
  PIS: [735, 365], PAU: [880, 300], ANT: [482, 442], LMT: [330, 470],
  CUS_BC: [613, 454], CUS_CEN: [555, 520], ATM_PLZ: [495, 560], ATM_SOL: [575, 590], CUS_WAN: [645, 392],
  SAN: [625, 545], SSB: [710, 500], SJE: [790, 525], ATM_AER: [775, 450],
  URC: [700, 610], OCO: [840, 565], AGT_MCP: [915, 455], QCM: [960, 345],
  COM: [735, 690], YAN: [640, 725], SIC_BR: [845, 700], SIC_AG: [925, 680], ATM_SIC: [972, 625],
  YAU: [925, 752], STO: [790, 762],
};

function posicionesGeograficas(nodos, W, H, margen = 55) {
  const conocidos = nodos.filter(n => ESQUEMA_CUSCO[n.id]).length;
  if (conocidos >= nodos.length * 0.6) {
    const pos = {};
    const ref = nodos.find(n => n.id === "CUS_BC");
    for (const n of nodos) {
      if (ESQUEMA_CUSCO[n.id]) pos[n.id] = [...ESQUEMA_CUSCO[n.id]];
      else if (ref && typeof n.lat === "number") {
        const [bx, by] = ESQUEMA_CUSCO.CUS_BC;
        pos[n.id] = [Math.max(20, Math.min(980, bx + (n.lon - ref.lon) * 260)),
          Math.max(20, Math.min(760, by - (n.lat - ref.lat) * 260))];
      } else pos[n.id] = [40, 740];
    }
    for (const id in pos) pos[id] = [pos[id][0] * W / 1000, pos[id][1] * H / 780];
    return despejar(pos, nodos, 18);
  }
  return posicionesGeograficasReales(nodos, W, H, margen);
}

function posicionesGeograficasReales(nodos, W, H, margen = 55) {
  let conCoord = nodos.filter(n => typeof n.lat === "number" && typeof n.lon === "number");
  const pos = {};
  if (!conCoord.length) return posicionesCirculo(nodos.map(n => n.id), W / 2, H / 2, Math.min(W, H) / 2 - margen);
  conCoord = ojoDePez(conCoord).map(n => ({ ...n, lon: n._x, lat: n._y }));
  const lons = conCoord.map(n => n.lon), lats = conCoord.map(n => n.lat);
  const [x0, x1] = [Math.min(...lons), Math.max(...lons)];
  const [y0, y1] = [Math.min(...lats), Math.max(...lats)];
  // escala por eje: el esquema ocupa todo el lienzo (no es un mapa a escala)
  const ex = (W - 2 * margen) / ((x1 - x0) || 1), ey = (H - 2 * margen) / ((y1 - y0) || 1);
  for (const n of conCoord) pos[n.id] = [margen + (n.lon - x0) * ex, margen + (y1 - n.lat) * ey];
  // nodos sin coordenadas: en una fila al pie
  nodos.filter(n => !pos[n.id]).forEach((n, i) => { pos[n.id] = [margen + i * 60, H - 20]; });
  return despejar(pos, nodos);
}

/* Separa nodos que quedan casi encima (ciudad de Cusco, bóveda + agencia +
   cajero): el nodo principal queda en su lugar y los demás forman un anillo
   respetando su dirección geográfica. */
function despejar(pos, nodos, umbral = 34) {
  const orden = [...nodos].sort((a, b) => (PRIORIDAD[a.tipo] ?? 9) - (PRIORIDAD[b.tipo] ?? 9));
  const asignado = new Set();
  const salida = { ...pos };
  for (const centro of orden) {
    if (asignado.has(centro.id) || !pos[centro.id]) continue;
    const [cx, cy] = pos[centro.id];
    const cercanos = orden.filter(n => n.id !== centro.id && !asignado.has(n.id) && pos[n.id] &&
      Math.hypot(pos[n.id][0] - cx, pos[n.id][1] - cy) < umbral);
    asignado.add(centro.id);
    if (!cercanos.length) continue;
    const r = Math.min(26 + 5 * cercanos.length, 62);
    const angulos = cercanos.map(n => {
      const dx = pos[n.id][0] - cx, dy = pos[n.id][1] - cy;
      return { n, a: (dx === 0 && dy === 0) ? 0 : Math.atan2(dy, dx) };
    }).sort((p, q) => p.a - q.a);
    const paso = (2 * Math.PI) / angulos.length;
    const inicio = angulos[0].a;
    angulos.forEach((p, i) => {
      const a = (cercanos.length === 1) ? (p.a || -Math.PI / 4) : inicio + i * paso;
      salida[p.n.id] = [cx + r * Math.cos(a), cy + r * Math.sin(a)];
      asignado.add(p.n.id);
    });
  }
  return salida;
}

function posicionesXY(nodos, W, H, margen = 60) {
  const xs = nodos.map(n => n.x), ys = nodos.map(n => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const escala = Math.min((W - 2 * margen) / ((x1 - x0) || 1), (H - 2 * margen) / ((y1 - y0) || 1));
  const offX = (W - (x1 - x0) * escala) / 2, offY = (H - (y1 - y0) * escala) / 2;
  const pos = {};
  for (const n of nodos) pos[n.id] = [offX + (n.x - x0) * escala, offY + (n.y - y0) * escala];
  return pos;
}

function posicionesCirculo(ids, cx, cy, r) {
  const pos = {};
  ids.forEach((id, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / ids.length;
    pos[id] = [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
  return pos;
}

/* Columnas por capa (orden topológico, profundidad de rastreo, etc.). */
function posicionesCapas(nodos, W, H, margen = 70) {
  const capas = {};
  for (const n of nodos) (capas[n.capa ?? 0] = capas[n.capa ?? 0] || []).push(n.id);
  const claves = Object.keys(capas).map(Number).sort((a, b) => a - b);
  const pos = {};
  claves.forEach((c, i) => {
    const x = claves.length === 1 ? W / 2 : margen + (i * (W - 2 * margen)) / (claves.length - 1);
    const ids = capas[c].sort();
    ids.forEach((id, j) => {
      const y = ids.length === 1 ? H / 2 : margen * 0.6 + (j * (H - 1.2 * margen)) / (ids.length - 1);
      pos[id] = [x, y];
    });
  });
  return pos;
}

/* Anillos concéntricos por nivel (proximidad BFS). */
function posicionesAnillos(nodos, W, H) {
  const niveles = {};
  for (const n of nodos) (niveles[n.capa] = niveles[n.capa] || []).push(n.id);
  const pos = {};
  const maxNivel = Math.max(...Object.keys(niveles).map(Number));
  const radioMax = Math.min(W, H) / 2 - 50;
  for (const [nivel, ids] of Object.entries(niveles)) {
    const k = Number(nivel);
    if (k === 0) { ids.forEach(id => { pos[id] = [W / 2, H / 2]; }); continue; }
    const r = (radioMax * k) / maxNivel;
    ids.sort().forEach((id, i) => {
      const a = -Math.PI / 2 + (2 * Math.PI * i) / ids.length + k * 0.3;
      pos[id] = [W / 2 + r * Math.cos(a), H / 2 + r * Math.sin(a)];
    });
  }
  return pos;
}

/* ------------------------------------------------------------ dibujo de red */
function dibujarRed(contenedor, cfg) {
  contenedor.querySelectorAll("svg").forEach(s => s.remove());
  const W = cfg.W || 1000, H = cfg.H || 720;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
  contenedor.prepend(svg);
  const defs = svgEl("defs", {}, svg);
  const marcadores = {};
  const marcador = (color) => {
    const id = "m" + Object.keys(marcadores).length + Math.random().toString(36).slice(2, 6);
    if (marcadores[color]) return marcadores[color];
    const m = svgEl("marker", { id, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7,
      markerHeight: 7, orient: "auto-start-reverse", markerUnits: "userSpaceOnUse" }, defs);
    m.setAttribute("markerWidth", 11); m.setAttribute("markerHeight", 11);
    const p = svgEl("path", { d: "M0,0 L10,5 L0,10 z" }, m);
    p.style.fill = color;
    marcadores[color] = `url(#${id})`;
    return marcadores[color];
  };

  const pos = cfg.pos;
  const porId = {};
  for (const n of cfg.nodos) porId[n.id] = n;
  const existe = new Set(cfg.aristas.map(a => a.u + "|" + a.v));
  const gResalte = svgEl("g", {}, svg);
  const gA = svgEl("g", {}, svg);
  const gEtA = svgEl("g", {}, svg);
  const gN = svgEl("g", {}, svg);
  const gEt = svgEl("g", {}, svg);
  const elemArista = {}, elemNodo = {};

  for (const a of cfg.aristas) {
    const p1 = pos[a.u], p2 = pos[a.v];
    if (!p1 || !p2) continue;
    const est = Object.assign({ color: "var(--tenue)", ancho: 1.6, opacidad: 0.75 },
      sinIndefinidos(cfg.estiloArista ? cfg.estiloArista(a) : {}));
    if (est.oculta) continue;
    const flecha = est.flecha ?? cfg.dirigido;
    const rV = radioNodo(porId[a.v] || {}) + (flecha ? 4 : 0);
    const dx = p2[0] - p1[0], dy = p2[1] - p1[1], L = Math.hypot(dx, dy) || 1;
    // se curva si hay arista en sentido contrario o si la recta pasa encima de otro nodo
    const tapaNodo = cfg.nodos.some(n => {
      if (n.id === a.u || n.id === a.v || !pos[n.id]) return false;
      const [px, py] = pos[n.id];
      const t = ((px - p1[0]) * dx + (py - p1[1]) * dy) / (L * L);
      if (t <= 0.05 || t >= 0.95) return false;
      return Math.hypot(p1[0] + t * dx - px, p1[1] + t * dy - py) < 9;
    });
    const curva = (cfg.dirigido && existe.has(a.v + "|" + a.u)) || est.curva || tapaNodo;
    let d, mx, my;
    if (curva) {
      const nx = -dy / L, ny = dx / L, k = 0.18 * L;
      const cxp = (p1[0] + p2[0]) / 2 + nx * k, cyp = (p1[1] + p2[1]) / 2 + ny * k;
      const ex = p2[0] - (p2[0] - cxp) / Math.hypot(p2[0] - cxp, p2[1] - cyp) * rV;
      const ey = p2[1] - (p2[1] - cyp) / Math.hypot(p2[0] - cxp, p2[1] - cyp) * rV;
      d = `M${p1[0]},${p1[1]} Q${cxp},${cyp} ${ex},${ey}`;
      mx = (p1[0] + 2 * cxp + p2[0]) / 4; my = (p1[1] + 2 * cyp + p2[1]) / 4;
    } else {
      const ex = p2[0] - (dx / L) * rV, ey = p2[1] - (dy / L) * rV;
      d = `M${p1[0]},${p1[1]} L${ex},${ey}`;
      mx = (p1[0] + p2[0]) / 2; my = (p1[1] + p2[1]) / 2;
    }
    if (est.resalte) {
      const r = svgEl("path", { d, fill: "none", "stroke-linecap": "round" }, gResalte);
      r.style.stroke = est.resalte; r.style.strokeWidth = est.ancho + 12;
    }
    const camino = svgEl("path", { d, fill: "none", "stroke-linecap": "round" }, gA);
    camino.style.stroke = est.color;
    camino.style.strokeWidth = est.ancho;
    camino.style.opacity = est.opacidad;
    if (est.guiones) camino.style.strokeDasharray = est.guiones;
    if (est.clase) camino.setAttribute("class", est.clase);
    if (flecha) camino.setAttribute("marker-end", marcador(est.color));
    if (cfg.alClicArista || cfg.globoArista) {
      const zona = svgEl("path", { d, fill: "none", class: "arista-clic" }, gA);
      zona.style.stroke = "transparent"; zona.style.strokeWidth = 14;
      if (cfg.alClicArista) zona.addEventListener("click", () => cfg.alClicArista(a));
      if (cfg.globoArista) {
        zona.addEventListener("mousemove", e => Globo.mostrar(e, cfg.globoArista(a)));
        zona.addEventListener("mouseleave", () => Globo.ocultar());
      }
    }
    if (est.etiqueta !== undefined && est.etiqueta !== null && est.etiqueta !== "") {
      const t = svgEl("text", { x: mx, y: my - 4, "text-anchor": "middle", class: "etq-arista" }, gEtA);
      t.textContent = est.etiqueta;
      if (est.colorEtiqueta) t.style.fill = est.colorEtiqueta;
      if (est.negritaEtiqueta) t.style.fontWeight = 700;
    }
    elemArista[a.u + "|" + a.v] = camino;
  }

  for (const n of cfg.nodos) {
    const p = pos[n.id];
    if (!p) continue;
    const est = Object.assign({ color: COLOR_TIPO[n.tipo] || "#2f5d8a", r: radioNodo(n), borde: "var(--panel-2)" },
      sinIndefinidos(cfg.estiloNodo ? cfg.estiloNodo(n) : {}));
    if (est.halo) {
      const h = svgEl("circle", { cx: p[0], cy: p[1], r: est.r + 7, fill: "none", class: est.haloPulso === false ? "" : "pulso" }, gN);
      h.style.stroke = est.halo; h.style.strokeWidth = 4;
    }
    const c = svgEl("circle", { cx: p[0], cy: p[1], r: est.r, class: "nodo" }, gN);
    c.style.fill = est.vacio ? "var(--panel)" : est.color;
    c.style.stroke = est.vacio ? est.color : est.borde;
    c.style.strokeWidth = est.vacio ? 3 : 2;
    if (est.opacidad !== undefined) c.style.opacity = est.opacidad;
    if (cfg.alClicNodo) c.addEventListener("click", () => cfg.alClicNodo(n));
    if (cfg.globoNodo) {
      c.addEventListener("mousemove", e => Globo.mostrar(e, cfg.globoNodo(n)));
      c.addEventListener("mouseleave", () => Globo.ocultar());
    }
    const texto = cfg.etiquetaNodo ? cfg.etiquetaNodo(n) : n.id;
    if (texto) {
      const posEt = est.etiquetaAbajo
        ? { x: p[0], y: p[1] + est.r + 13, "text-anchor": "middle" }
        : { x: p[0] + est.r + 3, y: p[1] - est.r + 2 };
      const t = svgEl("text", { ...posEt, class: "etq" }, gEt);
      t.textContent = texto;
      if (est.negrita) t.style.fontWeight = 700;
      if (est.tamEtiqueta) t.style.fontSize = est.tamEtiqueta + "px";
    }
    if (est.subetiqueta) {
      const t = svgEl("text", { x: p[0], y: p[1] + 4, "text-anchor": "middle", class: "etq" }, gEt);
      t.textContent = est.subetiqueta;
      t.style.fontSize = "11px"; t.style.fontWeight = 700; t.style.fill = "#fff"; t.style.stroke = "none";
    }
    elemNodo[n.id] = c;
  }
  return { svg, pos, elemNodo, elemArista };
}

function leyenda(contenedor, items) {
  contenedor.querySelectorAll(".leyenda").forEach(l => l.remove());
  const div = document.createElement("div");
  div.className = "leyenda";
  div.innerHTML = items.map(([color, texto, linea]) =>
    `<span><i class="${linea ? "linea" : ""}" style="background:${color}"></i>${texto}</span>`).join("");
  contenedor.appendChild(div);
}

/* ------------------------------------------------------------ gráficas */
function numeroRedondo(max) {
  if (max <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(max)));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * exp >= max) return m * exp;
  return 10 * exp;
}

function graficoLineas(contenedor, cfg) {
  const W = 460, H = 270, m = { i: 56, d: 14, s: 30, b: 44 };
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}` }, contenedor);
  const todos = cfg.series.flatMap(s => s.puntos);
  const xMax = Math.max(...todos.map(p => p[0])), xMin = Math.min(...todos.map(p => p[0]));
  const yMax = numeroRedondo(Math.max(...todos.map(p => p[1])) * 1.05);
  const X = x => m.i + ((x - xMin) / ((xMax - xMin) || 1)) * (W - m.i - m.d);
  const Y = y => H - m.b - (y / yMax) * (H - m.s - m.b);
  const t = svgEl("text", { x: m.i, y: 18, class: "etq" }, svg);
  t.textContent = cfg.titulo; t.style.fontWeight = 700; t.style.fontSize = "13px";
  for (let i = 0; i <= 4; i++) {
    const v = (yMax * i) / 4, y = Y(v);
    const l = svgEl("line", { x1: m.i, x2: W - m.d, y1: y, y2: y }, svg);
    l.style.stroke = "var(--linea)";
    const e = svgEl("text", { x: m.i - 6, y: y + 4, "text-anchor": "end", class: "etq-arista" }, svg);
    e.textContent = v >= 100 ? Math.round(v) : +v.toFixed(2);
  }
  const xs = [...new Set(todos.map(p => p[0]))].sort((a, b) => a - b);
  for (const x of xs) {
    const e = svgEl("text", { x: X(x), y: H - m.b + 16, "text-anchor": "middle", class: "etq-arista" }, svg);
    e.textContent = x;
  }
  const ex = svgEl("text", { x: (W + m.i) / 2, y: H - 8, "text-anchor": "middle", class: "etq-arista" }, svg);
  ex.textContent = cfg.ejeX || "";
  const ey = svgEl("text", { x: 14, y: (H - m.b + m.s) / 2, "text-anchor": "middle", class: "etq-arista",
    transform: `rotate(-90 14 ${(H - m.b + m.s) / 2})` }, svg);
  ey.textContent = cfg.ejeY || "";
  const colores = ["#9b2c2c", "#2b5a8a", "#2f7d4f", "#c27a2c"];
  cfg.series.forEach((s, k) => {
    const color = colores[k % colores.length];
    const d = s.puntos.map((p, i) => `${i ? "L" : "M"}${X(p[0])},${Y(p[1])}`).join(" ");
    const linea = svgEl("path", { d, fill: "none" }, svg);
    linea.style.stroke = color; linea.style.strokeWidth = 2.5;
    for (const p of s.puntos) {
      const c = svgEl("circle", { cx: X(p[0]), cy: Y(p[1]), r: 3.5 }, svg);
      c.style.fill = color;
    }
    const lx = m.i + 8, ly = m.s + 6 + k * 16;
    const r = svgEl("rect", { x: lx, y: ly - 8, width: 12, height: 4, rx: 2 }, svg);
    r.style.fill = color;
    const tx = svgEl("text", { x: lx + 16, y: ly - 3, class: "etq-arista" }, svg);
    tx.textContent = s.nombre; tx.style.fill = "var(--tinta)";
  });
  return svg;
}

function colorCalor(v, min, max) {
  if (v === null || v === undefined) return "transparent";
  const t = max > min ? (v - min) / (max - min) : 0;
  const a = [232, 240, 248], b = [155, 44, 44];
  const c = a.map((x, i) => Math.round(x + (b[i] - x) * t));
  return `rgb(${c.join(",")})`;
}
