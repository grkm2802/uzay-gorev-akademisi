// Fırlatma, 6 aylık görev simülasyonu ve rapor.
// Sonuç yalnızca tasarımın marjlarına (güç, indirme, bütçe, bilim dağılımı) bağlıdır; her çalıştırmada olaylar değişir.

var EVENT_DEFS = [
  { id: 'storm', name: 'Güneş fırtınası',
    intro: 'Güçlü bir güneş fırtınası panelleri yıpratıyor (üretim yaklaşık %20 düşer).',
    test: function (r) { return r.generate * 0.8 >= r.consume; },
    good: function (r) { return 'Güç marjın yeterliydi (' + fmt(r.generate * 0.8) + ' W üretim, ' + fmt(r.consume) + ' W tüketim). Uydu çalışmaya devam etti.'; },
    bad: function (r) { return 'Panel üretimi ' + fmt(r.generate * 0.8) + ' W\'a düştü ama tüketim ' + fmt(r.consume) + ' W. Uydu güvenli moda geçti ve o ay bilim verisi gelmedi. Güç marjı bırakmak için büyük panel, güneşli yörünge ya da daha az tüketim dene.'; },
    factor: function () { return 0; } },
  { id: 'gs', name: 'Yer istasyonu kesintisi',
    intro: 'Yer istasyonu bir ay kısıtlı çalışıyor (indirme kapasitesi yaklaşık %30 düşer).',
    test: function (r) { return r.downlink * 0.7 >= r.dataGen; },
    good: function (r) { return 'İndirme kapasiten yeterli marja sahipti (' + fmt(r.downlink * 0.7) + ' MB/gün, üretim ' + fmt(r.dataGen) + ' MB/gün). Veri kaybı olmadı.'; },
    bad: function (r) { return 'İndirme kapasitesi ' + fmt(r.downlink * 0.7) + ' MB/gün\'e düştü ama üretim ' + fmt(r.dataGen) + ' MB/gün. Verinin bir kısmı kayboldu. Daha hızlı telsiz ya da daha az veri üreten enstrüman seç.'; },
    factor: function () { return 0.5; } },
  { id: 'fail', name: 'Enstrüman arızası',
    intro: 'Enstrümanlardan biri kalıcı olarak bozuluyor.',
    test: function (r, ctx) { return r.science - ctx.failed.science >= MISSION.minScience * 0.5; },
    good: function (r, ctx) { return ctx.failed.name + ' bozuldu ama kalan enstrümanlar (' + (r.science - ctx.failed.science) + ' puan) görevi anlamlı şekilde sürdürdü.'; },
    bad: function (r, ctx) { return ctx.failed.name + ' bozuldu ve geriye çok az bilim değeri (' + (r.science - ctx.failed.science) + ' puan) kaldı. Bilim değerini birden fazla enstrümana yaymak görevi korur.'; } },
  { id: 'budget', name: 'Bütçe kesintisi',
    intro: 'Operasyon bütçesi bir ay boyunca kısılıyor (yaklaşık 0,1M$).',
    test: function (r) { return MISSION.budget - r.cost >= 0.1; },
    good: function (r) { return 'Bütçede ' + fmt(MISSION.budget - r.cost, 2) + 'M$ pay bırakmıştın. Kesinti sorun olmadı.'; },
    bad: function (r) { return 'Bütçede yalnızca ' + fmt(MISSION.budget - r.cost, 2) + 'M$ pay vardı. Operasyon yarı hızda çalıştı. Bütçede güvenlik payı bırak.'; },
    factor: function () { return 0.5; } }
];

// Ana enstrümana göre benzer gerçek görev türleri (kaba eşleştirme)
var SIMILAR = {
  cam: 'Dünya\'yı görünür ışıkla gözlemleyen Landsat serisi',
  ir: 'Sıcaklığı ve ısıyı haritalayan ECOSTRESS gibi görevler',
  mag: 'Manyetik alanı ölçen ESA Swarm görevi',
  rad: 'Radyasyon kuşaklarını inceleyen Van Allen Probes',
  spec: 'Yüzey bileşimini inceleyen spektrometre görevleri (ör. EO-1 Hyperion)'
};

function shuffle(a) {
  a = a.slice();
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}

function simulate(r) {
  var failed = r.ins[Math.floor(Math.random() * r.ins.length)];
  var ctx = { failed: failed };
  var chosen = shuffle(EVENT_DEFS).slice(0, 3);
  var months = shuffle([2, 3, 4, 5, 6]).slice(0, 3);
  var evs = chosen.map(function (d, i) {
    var ok = d.test(r, ctx);
    return { id: d.id, name: d.name, intro: d.intro, month: months[i], ok: ok, text: ok ? d.good(r, ctx) : d.bad(r, ctx), factor: d.factor ? d.factor() : null };
  });

  var log = [], factors = [], failedShare = null;
  for (var m = 1; m <= MISSION.lifeMonths; m++) {
    var fct = failedShare !== null ? failedShare : 1;
    var here = evs.filter(function (e) { return e.month === m; });
    var note = 'Normal işletme.';
    here.forEach(function (e) {
      if (e.id === 'fail') {
        failedShare = (r.science - failed.science) / r.science;
        fct = failedShare;
        note = e.name;
      } else if (!e.ok) { fct = Math.min(fct, e.factor); note = e.name; }
      else { note = e.name + ' (atlatıldı)'; }
    });
    factors.push(fct);
    log.push({ month: m, factor: fct, events: here, note: note });
  }

  var delivered = factors.reduce(function (a, b) { return a + b; }, 0) / factors.length;
  var survived = evs.filter(function (e) { return e.ok; }).length;
  var sciScore = Math.min(100, (r.science * delivered) / (MISSION.minScience * 1.5) * 100);
  var effScore = Math.min(100, (r.science / r.cost) / 20 * 100);
  var resScore = survived / evs.length * 100;
  var team = (typeof TEAM !== 'undefined' && TEAM.on) ? teamGoalsReport(r) : null;
  var teamScore = team ? Math.round(team.filter(function (g) { return g.ok; }).length / team.length * 100) : null;
  var total = team ? Math.round(sciScore * 0.3 + effScore * 0.2 + resScore * 0.2 + teamScore * 0.3)
                   : Math.round(sciScore * 0.4 + effScore * 0.3 + resScore * 0.3);
  var success = delivered >= 0.7 && r.science * delivered >= MISSION.minScience * 0.8;
  var rating = total >= 85 ? 'Mükemmel' : total >= 65 ? 'Başarılı' : total >= 40 ? 'Kısmen başarılı' : 'Başarısız';
  var best = r.ins.slice().sort(function (a, b) { return b.science - a.science; })[0];

  var tips = [];
  if (sciScore < 70) tips.push('Bilim getirisi düşük. Daha değerli bir enstrüman ekle ya da arızaya karşı bilimi yay.');
  if (effScore < 70) tips.push('Para başına bilim düşük. Daha ucuz roket ya da daha verimli enstrüman dene.');
  if (team && teamScore < 100) tips.push('Ekibin bazı rol hedeflerini tutturamadı. Hedefler çatışırsa önce konuşun, sonra birlikte karar verin.');
  if (resScore < 100) tips.push('Her olayda marj bırakmak görevi korur. Başarısız olayların açıklamalarına bak.');
  if (!tips.length) tips.push('Güçlü bir tasarım. Şimdi aynı görevi daha ucuza ya da farklı bir yolla çözmeyi dene: tek doğru çözüm yok.');

  return {
    log: log, events: evs, delivered: delivered, success: success, rating: rating,
    scores: { sci: Math.round(sciScore), eff: Math.round(effScore), res: Math.round(resScore), team: teamScore, total: total },
    team: team,
    similar: best ? SIMILAR[best.id] : null, tips: tips
  };
}

// ---------- Arayüz ----------
var flightTimers = [];
function clearFlightTimers() { flightTimers.forEach(clearTimeout); flightTimers = []; }
function later(ms, fn) { flightTimers.push(setTimeout(fn, ms)); }

function launchSvg(scale) {
  return '<svg viewBox="0 0 400 250" role="img" aria-label="Fırlatma rampası ve roket">' +
    '<g class="pad"><rect x="140" y="212" width="120" height="14"/><rect x="268" y="110" width="10" height="116"/><rect x="268" y="110" width="44" height="7"/></g>' +
    '<g class="smoke"><circle cx="170" cy="210" r="14"/><circle cx="230" cy="210" r="14"/><circle cx="200" cy="214" r="18"/></g>' +
    '<g transform="translate(200 210) scale(' + scale + ') translate(-200 -210)"><g class="rocket">' +
    '<g class="flame"><path d="M188 206 Q200 262 212 206 Z" fill="#FFC83D"/><path d="M193 206 Q200 240 207 206 Z" fill="#fff"/></g>' +
    '<path d="M184 172 L164 210 L184 204 Z" fill="#7C5CFF" stroke="#15173F" stroke-width="3" stroke-linejoin="round"/>' +
    '<path d="M216 172 L236 210 L216 204 Z" fill="#7C5CFF" stroke="#15173F" stroke-width="3" stroke-linejoin="round"/>' +
    '<rect x="184" y="92" width="32" height="116" rx="5" fill="#F1F2FF" stroke="#15173F" stroke-width="3"/>' +
    '<path d="M184 94 Q200 40 216 94 Z" fill="#FFC83D" stroke="#15173F" stroke-width="3" stroke-linejoin="round"/>' +
    '<circle cx="200" cy="132" r="8" fill="#7C5CFF" stroke="#15173F" stroke-width="3"/></g></g></svg>';
}

function logLine(m, res) {
  var cls = m.factor >= 1 ? 'ok' : m.factor > 0 ? 'warn' : 'no';
  var html = '<li class="' + cls + '"><div class="ml"><b>Ay ' + m.month + '</b><span>bilim getirisi %' + Math.round(m.factor * 100) + '</span></div><p>' + m.note + '</p>';
  m.events.forEach(function (e) { html += '<div class="ev"><em>' + e.intro + '</em><p>' + e.text + '</p></div>'; });
  return html + '</li>';
}

function scoreBar(label, v) {
  return '<div class="sc"><div class="sc-top"><span>' + label + '</span><b>' + v + '</b></div><div class="track"><div class="fill" style="width:' + v + '%"></div></div></div>';
}

function showReport(r, res) {
  var rep = document.getElementById('report');
  var html = '<h2>Görev raporu</h2><div class="verdict ' + (res.success ? 'good' : 'badr') + '"><b>' +
    res.rating + ', ' + res.scores.total + ' puan</b><span>' + (res.success ? 'Bilim hedefi tutturuldu.' : 'Bilim hedefi tutturulamadı.') + '</span></div>' +
    '<div class="scores">' + scoreBar('Bilim getirisi', res.scores.sci) + scoreBar('Kaynak verimi', res.scores.eff) + scoreBar('Dayanıklılık', res.scores.res) +
    (res.scores.team !== null ? scoreBar('Ekip uyumu', res.scores.team) : '') + '</div>' +
    (res.team ? teamReportHtml(res.team) : '') +
    '<h3>Neden böyle oldu?</h3><ul class="why">';
  res.events.forEach(function (e) {
    html += '<li class="' + (e.ok ? 'ok' : 'no') + '"><b>' + e.name + ' (Ay ' + e.month + '): ' + (e.ok ? 'atlatıldı' : 'zarar verdi') + '</b><p>' + e.text + '</p></li>';
  });
  html += '</ul><h3>Bir sonraki denemede</h3><ul class="tips">';
  res.tips.forEach(function (t) { html += '<li>' + t + '</li>'; });
  html += '</ul>';
  if (res.similar) html += '<p class="similar">Ana enstrümanın şu türdeki gerçek görevlere benziyor: <b>' + res.similar + '</b>.</p>';
  html += '<p class="mentor"><b>Prof.</b> ' + (res.success
    ? 'Güzel iş! Ama unutma: aynı hedefe başka yollardan da ulaşılır. Farklı bir tasarım deneyip karşılaştır.'
    : 'Sorun değil, mühendisler de ilk denemede başarısız olur. Raporu oku, tasarımı düzelt ve tekrar dene.') + '</p>' +
    '<div class="actions"><button id="redesign" class="btn ghost">Tasarımı düzenle</button><button id="rerun" class="btn">Tekrar simüle et</button></div>';
  rep.innerHTML = html;
  rep.classList.remove('hidden');
  document.getElementById('redesign').onclick = function () { show('design'); initDesign(); };
  document.getElementById('rerun').onclick = requestLaunch;
  rep.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function startFlight(resOverride) {
  var r = calc();
  if (!r.ins.length) return;
  var res = resOverride && resOverride.log ? resOverride : simulate(r);
  clearFlightTimers();
  show('flight');

  var stage = document.getElementById('launchStage');
  var craftEl = document.getElementById('craftFlight');
  var logEl = document.getElementById('flightLog');
  var status = document.getElementById('flightStatus');
  var skip = document.getElementById('skipFlight');
  var title = document.getElementById('flightTitle');
  var grid = stage.closest('.flight-grid');
  var scale = r.lau.id === 'rideshare' ? 0.78 : r.lau.id === 'small' ? 0.95 : 1.12;

  grid.classList.add('solo');
  stage.innerHTML = launchSvg(scale);
  stage.className = 'craft launch';
  stage.classList.remove('hidden');
  craftEl.classList.add('hidden');
  logEl.innerHTML = '';
  document.getElementById('report').classList.add('hidden');
  title.textContent = 'Fırlatma';
  skip.classList.remove('hidden');

  var capUse = Math.round(r.mass / r.lau.cap * 100);
  var cd = ['3', '2', '1'];
  cd.forEach(function (n, i) { later(i * 800, function () { status.textContent = 'Geri sayım: ' + n; }); });
  later(2400, function () {
    status.textContent = r.lau.name + ' ateşlendi. Uydu kütlesi ' + fmt(r.mass) + ' kg, roketin kapasitesinin %' + capUse + '\'i.';
    stage.classList.add('lift');
  });
  later(5400, function () {
    stage.classList.add('hidden');
    grid.classList.remove('solo');
    drawCraft('craftFlight');
    craftEl.classList.remove('hidden');
    title.textContent = 'Görev günlüğü';
    status.textContent = r.orb.name + ' yörüngesine ulaşıldı. 6 aylık görev başladı.';
    var i = 0;
    (function next() {
      if (i >= res.log.length) { later(900, function () { skip.classList.add('hidden'); status.textContent = 'Görev tamamlandı.'; showReport(r, res); }); return; }
      logEl.insertAdjacentHTML('beforeend', logLine(res.log[i++]));
      logEl.lastElementChild.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      later(1000, next);
    })();
  });

  skip.onclick = function () {
    clearFlightTimers();
    stage.classList.add('hidden');
    grid.classList.remove('solo');
    drawCraft('craftFlight');
    craftEl.classList.remove('hidden');
    title.textContent = 'Görev günlüğü';
    status.textContent = 'Görev tamamlandı.';
    logEl.innerHTML = res.log.map(function (m) { return logLine(m); }).join('');
    skip.classList.add('hidden');
    showReport(r, res);
  };
}

function teamReportHtml(team) {
  var html = '<h3>Ekip uyumu</h3><ul class="teamgoals">';
  team.forEach(function (g) {
    html += '<li class="' + (g.ok ? 'ok' : 'no') + '"><b>' + g.role + ' (' + esc(g.who) + '): ' + (g.ok ? 'hedef tutturuldu' : 'hedef tutturulamadı') +
      '</b><p>' + g.goal + ' Sonuç: ' + g.value + '.</p></li>';
  });
  return html + '</ul>';
}
