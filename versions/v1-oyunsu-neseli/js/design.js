// Tasarım odası: seçimler -> hesap -> kaynak çubukları ve kontroller

var design = {
  structure: '3u', solar: 'small', battery: 'small', comms: 'uhf',
  adcs: 'mag', launcher: 'rideshare', orbit: 'leo600', instruments: []
};

function byId(list, id) {
  return list.filter(function (x) { return x.id === id; })[0];
}
function fmt(n, d) { return Number(n).toFixed(d === undefined ? 1 : d); }

// Seçim grupları (eğitici açıklama ile)
var GROUPS = [
  { key: 'orbit', title: 'Yörünge', list: ORBITS,
    help: 'Yörünge yüksekliği ömrü, güneş alma süresini ve yer istasyonuyla görüşme süresini belirler.',
    stats: function (o) { return 'Ömür ' + o.lifeMonths + ' ay · günde ' + o.contactMin + ' dk yer görüşmesi'; },
    desc: function (o) { return o.info; } },
  { key: 'launcher', title: 'Fırlatıcı', list: LAUNCHERS,
    help: 'Roket sadece belirli bir kütleyi ve belirli yörüngeleri taşır. Büyüdükçe pahalanır.',
    stats: function (l) { return l.cap + ' kg · $' + fmt(l.cost, 2) + 'M'; },
    desc: function (l) { return l.info; } },
  { key: 'structure', title: 'Gövde', list: STRUCTURES,
    help: 'Gövde her şeyin taşındığı iskelettir; boyutu enstrüman sayısını sınırlar.',
    stats: function (s) { return s.mass + ' kg · ' + s.slots + ' yuva · $' + fmt(s.cost, 2) + 'M'; },
    desc: function (s) { return s.info; } },
  { key: 'solar', title: 'Güneş paneli', list: SOLARS,
    help: 'Panel güç üretir. Üretim, yörüngenin güneşte kaldığı süreye bağlıdır.',
    stats: function (s) { return s.mass + ' kg · ' + s.peakW + ' W tepe · $' + fmt(s.cost, 2) + 'M'; },
    desc: function () { return ''; } },
  { key: 'battery', title: 'Batarya', list: BATTERIES,
    help: 'Uydu her turda dünyanın gölgesine girer. Batarya o sırada sistemi çalışır tutar.',
    stats: function (b) { return b.mass + ' kg · $' + fmt(b.cost, 2) + 'M'; },
    desc: function () { return ''; } },
  { key: 'comms', title: 'Haberleşme', list: COMMS,
    help: 'Hızlı telsiz günde daha çok veri indirir ama daha çok güç, kütle ve para ister.',
    stats: function (c) { return c.mass + ' kg · ' + c.power + ' W · $' + fmt(c.cost, 2) + 'M'; },
    desc: function () { return ''; } },
  { key: 'adcs', title: 'Yönelim kontrolü', list: ADCS,
    help: 'Kamera gibi enstrümanlar hedefe hassas bakmalıdır; kaba yönelim yetmez.',
    stats: function (a) { return a.mass + ' kg · ' + a.power + ' W · $' + fmt(a.cost, 2) + 'M'; },
    desc: function () { return ''; } },
  { key: 'instruments', title: 'Bilimsel enstrümanlar', list: INSTRUMENTS, multi: true,
    help: 'Enstrüman bilim değeri katar ama kütle, güç, veri ve maliyet de ekler.',
    stats: function (i) {
      return i.mass + ' kg · ' + i.power + ' W · ' + i.dataMB + ' MB/gün · bilim ' + i.science +
        (i.precise ? ' · hassas yönelim ister' : '') + ' · $' + fmt(i.cost, 2) + 'M';
    },
    desc: function () { return ''; } }
];

function calc() {
  var s = byId(STRUCTURES, design.structure), sol = byId(SOLARS, design.solar),
      bat = byId(BATTERIES, design.battery), com = byId(COMMS, design.comms),
      adc = byId(ADCS, design.adcs), lau = byId(LAUNCHERS, design.launcher),
      orb = byId(ORBITS, design.orbit);
  var ins = design.instruments.map(function (id) { return byId(INSTRUMENTS, id); });

  var r = { s: s, sol: sol, bat: bat, com: com, adc: adc, lau: lau, orb: orb, ins: ins };
  var sum = function (f) { return ins.reduce(function (a, i) { return a + f(i); }, 0); };

  r.mass = s.mass + sol.mass + bat.mass + com.mass + adc.mass + sum(function (i) { return i.mass; });
  r.massLimit = Math.min(MISSION.mass, lau.cap);
  r.consume = s.power + com.power + adc.power + sum(function (i) { return i.power; });
  r.generate = sol.peakW * orb.sun * 0.6;
  r.eclipseWh = r.consume * orb.eclipseH;
  r.ops = MISSION.opsCostPerMonth * MISSION.lifeMonths;
  r.cost = s.cost + sol.cost + bat.cost + com.cost + adc.cost + lau.cost + r.ops +
    sum(function (i) { return i.cost; });
  r.dataGen = sum(function (i) { return i.dataMB; });
  r.downlink = com.kbps * orb.contactMin * 60 / 8000;
  r.science = sum(function (i) { return i.science; });
  r.needsPrecise = ins.some(function (i) { return i.precise; });
  return r;
}

function checks(r) {
  return [
    { ok: r.mass <= MISSION.mass, label: 'Kütle sınırı',
      txt: fmt(r.mass) + ' / ' + MISSION.mass + ' kg',
      why: 'Uydu görev sınırı olan ' + MISSION.mass + ' kg\'ı aşıyor. Daha hafif parça seç veya enstrüman çıkarın.' },
    { ok: r.mass <= r.lau.cap, label: 'Fırlatıcı kapasitesi',
      txt: fmt(r.mass) + ' / ' + r.lau.cap + ' kg',
      why: r.lau.name + ' sadece ' + r.lau.cap + ' kg taşıyabilir. Daha güçlü roket veya daha hafif uydu gerekir.' },
    { ok: r.lau.orbits.indexOf(r.orb.id) >= 0, label: 'Fırlatıcı bu yörüngeye ulaşır',
      txt: r.lau.orbits.indexOf(r.orb.id) >= 0 ? 'Evet' : 'Hayır',
      why: r.lau.name + ' bu yörüngeye çıkaramaz. Başka yörünge veya daha güçlü roket seç.' },
    { ok: r.cost <= MISSION.budget, label: 'Bütçe',
      txt: '$' + fmt(r.cost, 2) + 'M / $' + fmt(MISSION.budget, 2) + 'M',
      why: 'Bütçe aşıldı. Pahalı parçaları (roket, X-bant, spektrometre) gözden geçirin.' },
    { ok: r.generate >= r.consume, label: 'Güç dengesi',
      txt: fmt(r.generate) + ' W üretim / ' + fmt(r.consume) + ' W tüketim',
      why: 'Panel, tüketimi karşılayamıyor. Daha büyük panel, daha güneşli yörünge veya daha az tüketim gerekir.' },
    { ok: r.bat.wh >= r.eclipseWh, label: 'Gölge (tutulma) için batarya',
      txt: r.bat.wh + ' Wh / ' + fmt(r.eclipseWh) + ' Wh gerekli',
      why: 'Uydu dünyanın gölgesinde kalınca batarya bitiyor. Daha büyük batarya veya daha az tüketim gerekir.' },
    { ok: r.downlink >= r.dataGen, label: 'Veri indirme',
      txt: fmt(r.downlink) + ' MB/gün indirme / ' + fmt(r.dataGen) + ' MB/gün üretim',
      why: 'Enstrümanlar indirebildiğinden fazla veri üretiyor. Daha hızlı telsiz veya daha az veri üreten enstrüman seç.' },
    { ok: r.orb.lifeMonths >= MISSION.lifeMonths, label: 'Görev ömrü',
      txt: r.orb.lifeMonths + ' / ' + MISSION.lifeMonths + ' ay',
      why: 'Bu yörüngede uydu ' + MISSION.lifeMonths + ' ay dayanmaz (atmosfer sürtünmesi). Daha yüksek yörünge seç.' },
    { ok: design.instruments.length <= r.s.slots, label: 'Enstrüman yuvası',
      txt: design.instruments.length + ' / ' + r.s.slots,
      why: 'Gövdede bu kadar enstrümana yer yok. Daha büyük gövde seç veya enstrüman çıkarın.' },
    { ok: !r.sol.needsBig || r.s.bigPanel, label: 'Panel gövdeye sığıyor',
      txt: (!r.sol.needsBig || r.s.bigPanel) ? 'Evet' : 'Hayır',
      why: '3U gövde büyük paneli taşıyamaz. 6U gövde veya küçük panel seç.' },
    { ok: !r.needsPrecise || r.adc.precise, label: 'Yönelim hassasiyeti',
      txt: (!r.needsPrecise || r.adc.precise) ? 'Yeterli' : 'Yetersiz',
      why: 'Seçtiğiniz enstrüman hedefe hassas bakmalı. Reaksiyon tekerleği gerekir.' },
    { ok: r.science >= MISSION.minScience, label: 'Bilim değeri',
      txt: r.science + ' / ' + MISSION.minScience,
      why: 'Görevin hedefine ulaşmak için yeterli bilim değeri yok. Daha fazla veya daha değerli enstrüman ekleyin.' }
  ];
}

function bar(label, used, limit, unit, higherIsWorse) {
  var pct = limit > 0 ? Math.min(100, used / limit * 100) : 100;
  var over = used > limit;
  return '<div class="bar"><div class="bar-top"><span>' + label + '</span><b class="' + (over ? 'bad' : '') + '">' +
    fmt(used) + ' / ' + fmt(limit) + ' ' + unit + '</b></div>' +
    '<div class="track"><div class="fill ' + (over ? 'over' : '') + '" style="width:' + pct + '%"></div></div></div>';
}

var step = 0;

// Aşamalar gerçekten sıralıdır: önce fırlatma, sonra uzay aracı, sonra bilim yükü
var STAGES = [
  { name: 'Fırlatma', keys: ['orbit', 'launcher'],
    intro: 'Roket ve yörünge birlikte çalışır. Her roket yalnızca belli bir kütleyi, belli yörüngelere taşıyabilir.' },
  { name: 'Uzay aracı', keys: ['structure', 'solar', 'battery', 'comms', 'adcs'],
    intro: 'Gövdeyi, gücü, haberleşmeyi ve yönelimi seç. Her parça kütle, güç ve para harcar.' },
  { name: 'Bilim yükü', keys: ['instruments'],
    intro: 'Enstrümanlar görevin amacı, ama hepsi güç, veri ve para ister. Seçtikçe şema değişir.' }
];

// Karşılaştırma tablosu sütunları: [başlık, birim, değer]
var COLS = {
  orbit: [['Ömür', 'ay', function (o) { return o.lifeMonths; }],
          ['Yer görüşmesi', 'dk/gün', function (o) { return o.contactMin; }],
          ['Güneşte kalma', '%', function (o) { return Math.round(o.sun * 100); }]],
  launcher: [['Kapasite', 'kg', function (l) { return l.cap; }],
             ['Maliyet', '$M', function (l) { return fmt(l.cost, 2); }]],
  structure: [['Kütle', 'kg', function (s) { return fmt(s.mass); }],
              ['Yuva', 'adet', function (s) { return s.slots; }],
              ['Maliyet', '$M', function (s) { return fmt(s.cost, 2); }]],
  solar: [['Kütle', 'kg', function (s) { return fmt(s.mass); }],
          ['Tepe güç', 'W', function (s) { return s.peakW; }],
          ['Maliyet', '$M', function (s) { return fmt(s.cost, 2); }]],
  battery: [['Kütle', 'kg', function (b) { return fmt(b.mass); }],
            ['Kapasite', 'Wh', function (b) { return b.wh; }],
            ['Maliyet', '$M', function (b) { return fmt(b.cost, 2); }]],
  comms: [['Kütle', 'kg', function (c) { return fmt(c.mass); }],
          ['Güç', 'W', function (c) { return c.power; }],
          ['Hız', 'kbps', function (c) { return c.kbps; }],
          ['Maliyet', '$M', function (c) { return fmt(c.cost, 2); }]],
  adcs: [['Kütle', 'kg', function (a) { return fmt(a.mass); }],
         ['Güç', 'W', function (a) { return a.power; }],
         ['Hassas', '', function (a) { return a.precise ? 'evet' : 'hayır'; }],
         ['Maliyet', '$M', function (a) { return fmt(a.cost, 2); }]],
  instruments: [['Kütle', 'kg', function (i) { return fmt(i.mass); }],
                ['Güç', 'W', function (i) { return i.power; }],
                ['Veri', 'MB/gün', function (i) { return i.dataMB; }],
                ['Bilim', 'puan', function (i) { return i.science; }],
                ['Hassas', '', function (i) { return i.precise ? 'evet' : 'hayır'; }],
                ['Maliyet', '$M', function (i) { return fmt(i.cost, 2); }]]
};

function groupByKey(k) { return GROUPS.filter(function (g) { return g.key === k; })[0]; }

function renderOptions() {
  var st = STAGES[step];
  var html = '<nav class="stages">';
  STAGES.forEach(function (x, i) {
    html += '<button class="step ' + (i === step ? 'cur' : '') + '" data-step="' + i + '"' +
      (i === step ? ' aria-current="step"' : '') + '>' + x.name + '</button>';
  });
  html += '</nav><p class="stage-intro">' + st.intro + '</p>';

  st.keys.forEach(function (key) {
    var g = groupByKey(key), cols = COLS[key];
    html += '<section class="group"><h3>' + g.title + '</h3><p class="help">' + g.help +
      (g.multi ? ' Birden fazla seçebilirsin.' : '') + '</p><div class="cards">';
    g.list.forEach(function (item) {
      var sel = g.multi ? design.instruments.indexOf(item.id) >= 0 : design[g.key] === item.id;
      var d = g.desc(item);
      html += '<button type="button" class="opt card ' + (sel ? 'sel' : '') + '" data-key="' + g.key + '" data-id="' + item.id +
        '" aria-pressed="' + sel + '"><b>' + item.name + '</b>' + (d ? '<em>' + d + '</em>' : '') + '<span class="chips">';
      cols.forEach(function (c) {
        html += '<i>' + c[0] + ' <strong>' + c[2](item) + (c[1] ? ' ' + c[1] : '') + '</strong></i>';
      });
      html += '</span></button>';
    });
    html += '</div></section>';
  });

  html += '<div class="nav"><button class="btn ghost navbtn" data-dir="-1"' + (step === 0 ? ' disabled' : '') + '>Geri</button>' +
    (step < STAGES.length - 1
      ? '<button class="btn navbtn" data-dir="1">Sonraki: ' + STAGES[step + 1].name + '</button>'
      : '<span class="hint">Son aşama. Kontrolleri gözden geçirip incelemeye gönder.</span>') + '</div>';
  document.getElementById('options').innerHTML = html;
}

function renderSide() {
  var r = calc(), cs = checks(r);
  var side = '<h3>Kaynaklar</h3>' +
    bar('Kütle', r.mass, r.massLimit, 'kg') +
    bar('Güç tüketimi', r.consume, r.generate, 'W') +
    bar('Bütçe', r.cost, MISSION.budget, '$M') +
    bar('Veri üretimi / indirme', r.dataGen, r.downlink, 'MB/gün') +
    bar('Gerekli ömür / yörünge ömrü', MISSION.lifeMonths, r.orb.lifeMonths, 'ay') +
    '<div class="bar-top"><span>Bilim değeri</span><b>' + r.science + ' (hedef ' + MISSION.minScience + ')</b></div>';

  var failed = cs.filter(function (c) { return !c.ok; });
  side += '<h3 class="mt">Kontroller</h3><ul class="checks">';
  cs.forEach(function (c) {
    side += '<li class="' + (c.ok ? 'ok' : 'no') + '"><div class="ck"><span>' + c.label + '</span><b>' +
      (c.ok ? 'Uygun' : 'Sorun') + '</b></div><small>' + c.txt + '</small>' + (c.ok ? '' : '<p>' + c.why + '</p>') + '</li>';
  });
  side += '</ul><button id="submitDesign" class="btn">İncelemeye gönder</button>' +
    '<div id="review" class="review hidden"></div>';
  document.getElementById('side').innerHTML = side;
  document.getElementById('submitDesign').addEventListener('click', function () { review(failed.length); });
}

function review(failCount) {
  var el = document.getElementById('review');
  el.classList.remove('hidden');
  if (failCount === 0) {
    el.className = 'review good';
    el.innerHTML = '<b>Tasarım onaylandı!</b><p>Kurul tasarımını onayladı. Sıradaki adım fırlatma ve görev simülasyonu.</p>';
  } else {
    el.className = 'review badr';
    el.innerHTML = '<b>Tasarım reddedildi.</b><p>' + failCount + ' sorun var. Kırmızı maddeleri düzeltip tekrar gönder.</p>';
  }
}

function render() { renderOptions(); renderSide(); drawCraft('craftDesign'); }

function initDesign() {
  var host = document.getElementById('options');
  if (host.dataset.ready) { render(); return; }
  host.dataset.ready = '1';
  host.addEventListener('click', function (e) {
    var st = e.target.closest('.step');
    if (st) { step = +st.dataset.step; render(); return; }
    var nv = e.target.closest('.navbtn');
    if (nv) { step = Math.max(0, Math.min(STAGES.length - 1, step + +nv.dataset.dir)); render(); return; }
    var btn = e.target.closest('.opt');
    if (!btn) return;
    var key = btn.dataset.key, id = btn.dataset.id;
    if (key === 'instruments') {
      var i = design.instruments.indexOf(id);
      if (i >= 0) design.instruments.splice(i, 1); else design.instruments.push(id);
    } else {
      design[key] = id;
    }
    render();
  });
  render();
}
