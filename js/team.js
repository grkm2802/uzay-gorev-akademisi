// Takım modu: 4 rol, gizli hedefler, çevrimiçi oda (Firebase Realtime Database) ve aynı ekranda oyun.
// Çevrimiçi oyunda oda kurucu (host) otoritedir: herkes isteğini ona gönderir, o durumu herkese yayar.

var ROLES = [
  { id: 'planner', name: 'Görev planlayıcı', groups: ['orbit', 'launcher'],
    desc: 'Roketi ve yörüngeyi seçersin. Bütçeyi sen korursun.',
    goalText: 'Bütçede en az 0,40 milyon $ pay bırak.',
    test: function (r) { return MISSION.budget - r.cost >= 0.4; },
    value: function (r) { return 'pay ' + fmt(MISSION.budget - r.cost, 2) + 'M$'; } },
  { id: 'engineer', name: 'Uzay aracı mühendisi', groups: ['structure', 'solar', 'battery', 'adcs'],
    desc: 'Gövdeyi, güç sistemini ve yönelimi kurarsın.',
    goalText: 'Güç üretimi, tüketimin en az %15 üstünde olsun.',
    test: function (r) { return r.generate >= 1.15 * r.consume; },
    value: function (r) { return 'marj %' + Math.round((r.generate / r.consume - 1) * 100); } },
  { id: 'comms', name: 'Haberleşme sorumlusu', groups: ['comms'],
    desc: 'Telsizi seçersin. Veri yere ulaşmalı.',
    goalText: 'İndirme kapasitesi, veri üretiminin en az 1,3 katı olsun.',
    test: function (r) { return r.downlink >= 1.3 * r.dataGen; },
    value: function (r) { return r.dataGen ? (r.downlink / r.dataGen).toFixed(1) + ' kat' : 'veri yok'; } },
  { id: 'science', name: 'Bilim sorumlusu', groups: ['instruments'],
    desc: 'Enstrümanları seçersin. Görevin amacı sende.',
    goalText: 'Bilim değeri en az 55 puan olsun.',
    test: function (r) { return r.science >= 55; },
    value: function (r) { return r.science + ' puan'; } }
];
var ROLE_OF = {};
ROLES.forEach(function (r) { r.groups.forEach(function (g) { ROLE_OF[g] = r.id; }); });
function roleById(id) { return ROLES.filter(function (r) { return r.id === id; })[0]; }
function groupTitle(key) { var g = GROUPS.filter(function (x) { return x.key === key; })[0]; return g ? g.title : key; }

var TEAM = { on: false, mode: '', host: false, started: false, myPid: '', myName: '', myRole: null, code: '', roles: {}, players: {}, chat: [] };

function esc(s) {
  return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
}
function myName() { return TEAM.myName || 'Oyuncu'; }
function ownerName(roleId) {
  if (TEAM.mode === 'local') return TEAM.myRole === roleId ? 'sıra sende' : 'sırası gelince';
  var pid = TEAM.roles[roleId];
  return pid ? (TEAM.players[pid] || 'Oyuncu') + (pid === TEAM.myPid ? ' (sen)' : '') : 'boş rol, herkes düzenleyebilir';
}

// ---------- İzinler ----------
function teamCanEdit(key) {
  if (!TEAM.on) return true;
  var rid = ROLE_OF[key];
  if (TEAM.mode === 'local') return TEAM.myRole === rid;
  var owner = TEAM.roles[rid];
  return !owner || owner === TEAM.myPid;
}
function teamOwnerLabel(key) {
  if (!TEAM.on) return '';
  var r = roleById(ROLE_OF[key]);
  return '<p class="owner' + (teamCanEdit(key) ? '' : ' locked') + '">' + r.name + ': ' + esc(ownerName(r.id)) +
    (teamCanEdit(key) ? '' : '. Bu bölümü yalnızca o düzenleyebilir.') + '</p>';
}
function applyPick(key, id, pid) {
  if (TEAM.mode === 'online') {
    var owner = TEAM.roles[ROLE_OF[key]];
    if (owner && owner !== pid) return false;
  } else if (TEAM.mode === 'local' && TEAM.myRole !== ROLE_OF[key]) return false;
  if (key === 'instruments') {
    var i = design.instruments.indexOf(id);
    if (i >= 0) design.instruments.splice(i, 1); else design.instruments.push(id);
    // istekler farklı sırada ulaşabilir; sırayı sabitle (tüm cihazlarda aynı görünsün)
    var order = INSTRUMENTS.map(function (x) { return x.id; });
    design.instruments.sort(function (x, y) { return order.indexOf(x) - order.indexOf(y); });
  } else design[key] = id;
  return true;
}

// ---------- Ağ (Firebase Realtime Database: REST + SSE) ----------
// Oda verisi kendi veritabanımızda: odalar/<6 harf>/{b,s,g,i,p}
//   b: kurucunun işareti (sayı, 8 sn'de bir)      s: durum (JSON metni, kurucu yazar)
//   g: kurucudan herkese olaylar (inceleme, fırlatma, kapanış)   i: oyunculardan kurucuya istekler
//   p: oyuncu nabzı p/<kimlik> = {n: ad, t: zaman} (6 sn'de bir)
// Herkes yalnızca dışarıya doğru HTTPS ile bağlanır (okuma SSE akışı, yazma REST). Kurucu (host) otoritedir.
var DB_URL = 'https://uzay-gorev-akademisi-default-rtdb.firebaseio.com';
var Net = { room: '', es: null, timers: [], lastSeen: {}, lastHost: 0, seenG: {}, handled: {}, startTs: 0, closing: false };
var ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
var lastDesignJson = '';

function rid(n) { var s = ''; for (var i = 0; i < n; i++) s += ALPHA[Math.floor(Math.random() * ALPHA.length)]; return s; }
function newPid() { return 'p' + Math.random().toString(16).slice(2, 10) + Date.now().toString(36).slice(-3); }
function rurl(path, room) { return DB_URL + '/odalar/' + (room || Net.room) + (path || '') + '.json'; }
function dbPut(path, val) { return fetch(rurl(path), { method: 'PUT', body: JSON.stringify(val) }).catch(function () { }); }
function dbPost(path, val) { return fetch(rurl(path), { method: 'POST', body: JSON.stringify(val) }).catch(function () { }); }
function dbDel(path) { return fetch(rurl(path), { method: 'DELETE' }).catch(function () { }); }
// {ok, val}: ok=false ise ağ ya da kural hatası
function dbGet(room, path) {
  return fetch(rurl(path, room)).then(function (r) {
    if (!r.ok) return { ok: false, status: r.status };
    return r.json().then(function (v) { return { ok: true, val: v }; });
  }).catch(function () { return { ok: false, status: 0 }; });
}

function snapshot() {
  return { t: 'state', design: design, roles: TEAM.roles, players: TEAM.players, chat: TEAM.chat.slice(-40), started: TEAM.started };
}
function sendAll(msg) { dbPost('/g', JSON.stringify({ msg: msg })); }          // kurucu -> herkese olay
function bcast() { dbPut('/s', JSON.stringify(snapshot())); afterState(true); } // kurucu -> herkese durum
function toHost(msg) { dbPost('/i', JSON.stringify({ from: TEAM.myPid, msg: msg, ts: Date.now() })); }
function heartbeat() { dbPut('/p/' + TEAM.myPid, JSON.stringify({ n: TEAM.myName, t: Date.now() })); }

function afterState(designMayHaveChanged) {
  var j = JSON.stringify(design);
  var changed = j !== lastDesignJson;
  lastDesignJson = j;
  if (TEAM.started && document.getElementById('team').classList.contains('active')) { enterDesign(); return; }
  if (document.getElementById('design').classList.contains('active')) {
    if (changed) render(); else teamRender();
  } else renderLobby();
}

function hostHandle(conn, msg) {
  var pid = conn.peer;
  if (msg.t === 'ping') return;
  if (msg.t === 'join') { TEAM.players[pid] = String(msg.name || 'Oyuncu').slice(0, 20); }
  else if (msg.t === 'claim') {
    if (roleById(msg.role) && (!TEAM.roles[msg.role] || TEAM.roles[msg.role] === pid)) {
      Object.keys(TEAM.roles).forEach(function (k) { if (TEAM.roles[k] === pid) delete TEAM.roles[k]; });
      TEAM.roles[msg.role] = pid;
    }
  } else if (msg.t === 'release') {
    Object.keys(TEAM.roles).forEach(function (k) { if (TEAM.roles[k] === pid) delete TEAM.roles[k]; });
  } else if (msg.t === 'pick') { if (!applyPick(msg.key, msg.id, pid)) return; }
  else if (msg.t === 'chat') { TEAM.chat.push({ name: TEAM.players[pid] || 'Oyuncu', text: String(msg.text || '').slice(0, 200) }); }
  else if (msg.t === 'submit') { sendAll({ t: 'submit' }); reviewNow(); return; }
  else if (msg.t === 'launch') { hostLaunch(); return; }
  else return;
  bcast();
}
function hostLaunch() {
  var res = simulate(calc());
  sendAll({ t: 'flight', res: res });
  startFlight(res);
}
function clientHandle(msg) {
  if (msg.t === 'state') {
    Object.assign(design, msg.design);
    design.instruments = (msg.design.instruments || []).slice();
    TEAM.roles = msg.roles || {}; TEAM.players = msg.players || {}; TEAM.chat = msg.chat || []; TEAM.started = !!msg.started;
    if (!TEAM.players[TEAM.myPid]) heartbeat();   // oda bizi unuttuysa nabzımızla yeniden görünürüz
    afterState(true);
  } else if (msg.t === 'submit') reviewNow();
  else if (msg.t === 'flight') startFlight(msg.res);
}

function lobbyMsg(t, isErr) { var e = document.getElementById('teamMsg'); e.textContent = t || ''; e.className = 'teammsg' + (isErr ? ' err' : ''); }
function clearNet() {
  Net.timers.forEach(clearInterval);
  try { if (Net.es) Net.es.close(); } catch (e) { }
  Net = { room: '', es: null, timers: [], lastSeen: {}, lastHost: 0, seenG: {}, handled: {}, startTs: 0, closing: false };
}
function resetTeam() {
  clearNet();
  TEAM = { on: false, mode: '', host: false, started: false, myPid: '', myName: TEAM.myName, myRole: null, code: '', roles: {}, players: {}, chat: [] };
}
function parseJson(s) { try { return JSON.parse(s); } catch (e) { return null; } }

// ----- SSE olay yönlendirme -----
function onB() { if (!TEAM.host) Net.lastHost = Date.now(); }
function onS(v) {
  if (TEAM.host || typeof v !== 'string') return;
  var st = parseJson(v);
  if (st && st.t === 'state') { Net.lastHost = Date.now(); clientHandle(st); }
}
function onG(id, v, initial) {
  if (TEAM.host || Net.seenG[id]) return;
  Net.seenG[id] = 1;
  if (initial || typeof v !== 'string') return;               // bağlanmadan önceki olayları tekrar oynatma
  var o = parseJson(v);
  if (!o || !o.msg) return;
  Net.lastHost = Date.now();
  if (o.msg.t === 'closed') { lobbyMsg('Kurucu odayı kapattı.', true); resetTeam(); show('team'); renderLobby(); return; }
  clientHandle(o.msg);
}
function onI(id, v) {
  if (!TEAM.host || Net.handled[id] || typeof v !== 'string') return;
  Net.handled[id] = 1;
  var o = parseJson(v);
  dbDel('/i/' + id);
  if (!o || !o.from || !o.msg) return;
  if (o.ts && o.ts < Net.startTs - 120000) return;            // eski kurucudan kalan istek
  Net.lastSeen[o.from] = Date.now();
  hostHandle({ peer: o.from }, o.msg);
}
function onP(pid, v) {
  if (!TEAM.host || pid === TEAM.myPid || typeof v !== 'string') return;
  var o = parseJson(v);
  if (!o) return;
  Net.lastSeen[pid] = Date.now();
  if (!TEAM.players[pid]) { TEAM.players[pid] = String(o.n || 'Oyuncu').slice(0, 20); bcast(); }
}
function route(type, path, data) {
  if (type === 'patch') {
    Object.keys(data || {}).forEach(function (k) { route('put', (path === '/' ? '' : path) + '/' + k, data[k]); });
    return;
  }
  var parts = path.split('/').filter(Boolean);
  var each = function (obj, fn, initial) { Object.keys(obj || {}).forEach(function (k) { fn(k, obj[k], initial); }); };
  if (parts.length === 0) {                                    // tüm oda nesnesi (bağlanınca ve yeniden bağlanınca)
    var o = data || {};
    if (o.b !== undefined) onB(o.b);
    if (o.s !== undefined) onS(o.s);
    each(o.g, onG, true); each(o.i, onI); each(o.p, onP);
    return;
  }
  var k = parts[0];
  if (k === 'b') onB(data);
  else if (k === 's') onS(data);
  else if (k === 'g') { if (parts.length === 1) each(data, onG, false); else onG(parts[1], data, false); }
  else if (k === 'i') { if (parts.length === 1) each(data, onI); else onI(parts[1], data); }
  else if (k === 'p') { if (parts.length === 1) each(data, onP); else onP(parts[1], data); }
}
function openStream() {
  var es = new EventSource(rurl(''));
  Net.es = es;
  ['put', 'patch'].forEach(function (type) {
    es.addEventListener(type, function (e) {
      var o = parseJson(e.data);
      if (o && typeof o.path === 'string') route(type, o.path, o.data);
    });
  });
}

async function createRoom(name) {
  resetTeam(); TEAM.myName = name;
  lobbyMsg('Veritabanına bağlanılıyor…');
  var code = null;
  for (var t = 0; t < 8 && !code; t++) {
    var cand = rid(6);
    var r = await dbGet(cand, '/b');
    if (!r.ok) {
      lobbyMsg('Veritabanına ulaşılamadı (' + (r.status || 'ağ') + '). İnternet bağlantını ya da ağın engelini kontrol et. Aynı ekranda oynayabilirsin.', true);
      return;
    }
    if (r.val === null || Date.now() - r.val > 600000) code = cand;   // boş ya da 10 dakikadan eski (terk edilmiş) oda
  }
  if (!code) { lobbyMsg('Boş oda kodu bulunamadı, tekrar dene.', true); return; }

  Net.room = code; Net.startTs = Date.now();
  await fetch(rurl(''), { method: 'DELETE' }).catch(function () { });  // eski artıkları temizle
  TEAM.on = true; TEAM.mode = 'online'; TEAM.host = true; TEAM.code = code; TEAM.myPid = newPid();
  TEAM.players[TEAM.myPid] = name;
  await dbPut('/b', Date.now());
  await dbPut('/s', JSON.stringify(snapshot()));
  openStream();
  Net.timers.push(setInterval(function () {
    dbPut('/b', Date.now());
    var now = Date.now(), changed = false;
    Object.keys(TEAM.players).forEach(function (pid) {
      if (pid !== TEAM.myPid && Net.lastSeen[pid] && now - Net.lastSeen[pid] > 25000) {
        delete TEAM.players[pid]; delete Net.lastSeen[pid]; changed = true;
        Object.keys(TEAM.roles).forEach(function (k) { if (TEAM.roles[k] === pid) delete TEAM.roles[k]; });
        dbDel('/p/' + pid);
      }
    });
    if (changed) bcast();
  }, 8000));
  window.addEventListener('beforeunload', function () {
    if (TEAM.on && TEAM.host && Net.room) fetch(rurl(''), { method: 'DELETE', keepalive: true }).catch(function () { });
  });
  lastDesignJson = JSON.stringify(design);
  lobbyMsg('');
  renderLobby();
}

async function joinRoom(code, name) {
  code = String(code || '').toUpperCase().replace(/[^A-Z]/g, '');
  if (!/^[A-Z]{6}$/.test(code)) { lobbyMsg('Oda kodu 6 harftir (örnek: ABCDEF).', true); return; }
  resetTeam(); TEAM.myName = name;
  lobbyMsg('Oda aranıyor…');
  var r = await dbGet(code, '/b');
  if (!r.ok) { lobbyMsg('Veritabanına ulaşılamadı (' + (r.status || 'ağ') + '). Ağın engelliyor olabilir. Başka bir ağ (örneğin mobil veri) dene.', true); return; }
  if (r.val === null) { lobbyMsg('Bu kodla açık bir oda bulunamadı. Kodu kontrol et ve kurucunun odayı açık tuttuğundan emin ol.', true); return; }

  Net.room = code; Net.lastHost = Date.now();
  TEAM.on = true; TEAM.mode = 'online'; TEAM.host = false; TEAM.code = code; TEAM.myPid = newPid();
  await dbPut('/p/' + TEAM.myPid, JSON.stringify({ n: name, t: Date.now() }));
  openStream();
  var ok = false;                                              // kurucunun bizi odaya aldığını bekle
  for (var i = 0; i < 40 && !ok; i++) {
    await new Promise(function (res) { setTimeout(res, 250); });
    ok = !!TEAM.players[TEAM.myPid];
    if (!ok && i % 12 === 11) heartbeat();
  }
  if (!ok) { resetTeam(); lobbyMsg('Odaya girilemedi (kurucudan yanıt gelmedi). Tekrar dene.', true); return; }
  Net.timers.push(setInterval(function () {
    heartbeat();
    if (Date.now() - Net.lastHost > 30000) { lobbyMsg('Odayla bağlantı koptu.', true); resetTeam(); show('team'); renderLobby(); }
  }, 6000));
  window.addEventListener('beforeunload', function () {
    if (TEAM.on && !TEAM.host && Net.room) fetch(rurl('/p/' + TEAM.myPid), { method: 'DELETE', keepalive: true }).catch(function () { });
  });
  lastDesignJson = JSON.stringify(design);
  lobbyMsg('');
  renderLobby();
}

function startLocal(name) {
  resetTeam(); TEAM.myName = name;
  TEAM.on = true; TEAM.mode = 'local'; TEAM.host = true; TEAM.myRole = 'planner';
  lastDesignJson = JSON.stringify(design);
  renderLobby();
}

// ---------- Eylemler ----------
function teamPick(key, id) {
  if (TEAM.mode === 'online' && !TEAM.host) { toHost({ t: 'pick', key: key, id: id }); applyPick(key, id, TEAM.myPid); render(); return; }   // kendi seçimini anında göster, kurucunun durumu sonra doğrular
  if (applyPick(key, id, TEAM.myPid)) { if (TEAM.mode === 'online') bcast(); else render(); }
}
function teamSubmit() {
  if (TEAM.mode === 'online' && !TEAM.host) { toHost({ t: 'submit' }); return; }
  if (TEAM.mode === 'online') sendAll({ t: 'submit' });
  reviewNow();
}
function reviewNow() {
  var cs = checks(calc());
  var el = document.getElementById('review');
  if (!el) return;
  review(cs.filter(function (c) { return !c.ok; }).length);
}
function requestLaunch() {
  if (TEAM.on && TEAM.mode === 'online' && !TEAM.host) { toHost({ t: 'launch' }); return; }
  if (TEAM.on && TEAM.mode === 'online') { hostLaunch(); return; }
  startFlight();
}
function claimRole(id) {
  if (TEAM.mode !== 'online') return;
  if (TEAM.host) { hostHandle({ peer: TEAM.myPid }, { t: 'claim', role: id }); } else toHost({ t: 'claim', role: id });
}
function releaseRole() {
  if (TEAM.host) hostHandle({ peer: TEAM.myPid }, { t: 'release' }); else toHost({ t: 'release' });
}
function sendChat(text) {
  text = text.trim();
  if (!text) return;
  if (TEAM.host) hostHandle({ peer: TEAM.myPid }, { t: 'chat', text: text }); else toHost({ t: 'chat', text: text });
}
function enterDesign() {
  show('design'); initDesign(); teamRender();
}
function startTeam() {
  if (TEAM.mode === 'local') { TEAM.started = true; enterDesign(); return; }
  if (!TEAM.host) return;
  TEAM.started = true; bcast(); enterDesign();
}
function myRoleId() {
  if (TEAM.mode === 'local') return TEAM.myRole;
  var m = null;
  Object.keys(TEAM.roles).forEach(function (k) { if (TEAM.roles[k] === TEAM.myPid) m = k; });
  return m;
}

// ---------- Arayüz: lobi ----------
function renderLobby() {
  var entry = document.getElementById('teamEntry'), room = document.getElementById('teamRoom');
  if (!TEAM.on) { entry.classList.remove('hidden'); room.classList.add('hidden'); return; }
  entry.classList.add('hidden'); room.classList.remove('hidden');
  var html = '';
  if (TEAM.mode === 'online') {
    html += '<div class="roomcode"><span>Oda kodu</span><b>' + TEAM.code + '</b><small>Arkadaşların bu kodu girerek katılsın (en fazla 4 kişi).</small></div>';
    html += '<h3>Oyuncular</h3><ul class="players">';
    Object.keys(TEAM.players).forEach(function (pid) { html += '<li>' + esc(TEAM.players[pid]) + (pid === TEAM.myPid ? ' (sen)' : '') + (TEAM.host && pid === TEAM.myPid ? ' · kurucu' : '') + '</li>'; });
    html += '</ul>';
  } else {
    html += '<div class="roomcode"><span>Aynı ekranda</span><small>Tek cihazı sırayla devredin. Her rol yalnızca kendi bölümünü düzenler; sıra değişince rolü değiştirirsiniz.</small></div>';
  }
  html += '<h3>Roller</h3><div class="rolegrid">';
  var mine = myRoleId();
  ROLES.forEach(function (r) {
    var pid = TEAM.roles[r.id], cls = 'rolecard' + (mine === r.id ? ' mine' : '');
    html += '<div class="' + cls + '"><b>' + r.name + '</b><p>' + r.desc + '</p><p class="rg">Seçtiğin bölümler: ' + r.groups.map(groupTitle).join(', ') + '</p>';
    if (TEAM.mode === 'online') {
      if (mine === r.id) html += '<p class="goal">Gizli hedefin: ' + r.goalText + '</p><button class="btn ghost" data-act="release">Rolü bırak</button>';
      else if (pid) html += '<p class="taken">' + esc(TEAM.players[pid] || 'Oyuncu') + '</p>';
      else html += '<button class="btn" data-act="claim" data-role="' + r.id + '">Bu rolü al</button>';
    }
    html += '</div>';
  });
  html += '</div>';
  if (TEAM.mode === 'online') html += '<p class="hint">Boş kalan rolleri herkes düzenleyebilir. Her rolün gizli bir hedefi var. Hedefler birbiriyle çatışabilir, o yüzden konuşun. Oda veritabanında tutulur: sohbete kişisel bilgi yazma.</p>';
  html += TEAM.host ? '<button id="teamStart" class="btn">Takımı başlat</button>' : '<p class="hint">Kurucunun takımı başlatmasını bekle…</p>';
  room.innerHTML = html;
  var st = document.getElementById('teamStart');
  if (st) st.onclick = startTeam;
}

// ---------- Arayüz: tasarım ekranındaki takım çubuğu ve paneli ----------
function teamRender() {
  var bar = document.getElementById('teamBar'), panel = document.getElementById('teamPanel');
  if (!TEAM.on) { bar.classList.add('hidden'); panel.classList.add('hidden'); return; }
  bar.classList.remove('hidden'); panel.classList.remove('hidden');
  var html = '';
  ROLES.forEach(function (r) {
    var isMine = myRoleId() === r.id;
    if (TEAM.mode === 'local') html += '<button class="chip' + (isMine ? ' mine' : '') + '" data-switch="' + r.id + '"><b>' + r.name + '</b></button>';
    else html += '<span class="chip' + (isMine ? ' mine' : '') + '"><b>' + r.name + '</b><small>' + esc(ownerName(r.id)) + '</small></span>';
  });
  bar.innerHTML = (TEAM.mode === 'local' ? '<p class="teamnote">Şimdi oynayan rol:</p>' : '') + html;

  var rid = myRoleId(), r = rid ? roleById(rid) : null, ph = '';
  if (r) {
    var calcR = calc(), ok = r.test(calcR);
    ph += '<div class="goalcard ' + (ok ? 'ok' : 'no') + '"><b>' + (TEAM.mode === 'local' ? 'Bu rolün gizli hedefi' : 'Senin gizli hedefin') + '</b><p>' + r.goalText + '</p><span>' +
      (ok ? 'Tutturuldu' : 'Henüz değil') + ': ' + r.value(calcR) + '</span></div>';
  } else ph += '<div class="goalcard"><b>Rolün yok</b><p>Boş rollerin bölümlerini düzenleyebilirsin. Hedefler rol sahiplerine özeldir.</p></div>';
  if (TEAM.mode === 'online') {
    ph += '<div class="chat"><h3>Takım sohbeti</h3><ul id="chatLog">';
    TEAM.chat.slice(-30).forEach(function (m) { ph += '<li><b>' + esc(m.name) + ':</b> ' + esc(m.text) + '</li>'; });
    ph += '</ul><form id="chatForm"><input id="chatInput" maxlength="200" autocomplete="off" placeholder="Takıma yaz"><button class="btn" type="submit">Gönder</button></form></div>';
  }
  var keep = document.getElementById('chatInput') ? document.getElementById('chatInput').value : '';
  panel.innerHTML = ph;
  var ci = document.getElementById('chatInput');
  if (ci) ci.value = keep;
  var cl = document.getElementById('chatLog');
  if (cl) cl.scrollTop = cl.scrollHeight;
}

// Takım hedefleri (rapor için)
function teamGoalsReport(r) {
  return ROLES.map(function (ro) {
    var pid = TEAM.roles[ro.id];
    var who = TEAM.mode === 'local' ? 'Aynı ekran' : (pid ? (TEAM.players[pid] || 'Oyuncu') : 'Boş rol');
    return { role: ro.name, who: who, goal: ro.goalText, ok: ro.test(r), value: ro.value(r) };
  });
}

// ---------- Olay bağlama ----------
document.getElementById('toTeam').addEventListener('click', function () { show('team'); renderLobby(); });
document.getElementById('teamBack').addEventListener('click', function () { resetTeam(); show('brief'); });
document.getElementById('teamLocal').addEventListener('click', function () { startLocal(document.getElementById('teamName').value.trim() || 'Oyuncu'); });
document.getElementById('teamCreate').addEventListener('click', function () { createRoom(document.getElementById('teamName').value.trim() || 'Oyuncu'); });
document.getElementById('teamJoin').addEventListener('click', function () { joinRoom(document.getElementById('teamCode').value, document.getElementById('teamName').value.trim() || 'Oyuncu'); });
document.getElementById('teamRoom').addEventListener('click', function (e) {
  var b = e.target.closest('button[data-act]');
  if (!b) return;
  if (b.dataset.act === 'claim') claimRole(b.dataset.role); else releaseRole();
});
document.getElementById('teamBar').addEventListener('click', function (e) {
  var b = e.target.closest('[data-switch]');
  if (!b) return;
  TEAM.myRole = b.dataset.switch;
  render(); teamRender();
});
document.getElementById('teamPanel').addEventListener('submit', function (e) {
  if (e.target.id !== 'chatForm') return;
  e.preventDefault();
  var i = document.getElementById('chatInput');
  sendChat(i.value); i.value = '';
});
