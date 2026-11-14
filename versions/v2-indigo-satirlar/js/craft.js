// Uydu şeması: seçimlere göre kendiliğinden kurulan üstten görünüş.
// Parçalar kalıcı SVG öğeleridir; seçim değişince geçişle belirir, boyut değiştirir veya kaybolur.

var CRAFT = { cx: 200, cy: 125, bw: 120 };
var INS_ABBR = { cam: 'KAM', ir: 'IR', mag: 'MAG', rad: 'RAD', spec: 'SPK' };

function createCraft(el, uid) {
  el.innerHTML =
    '<svg viewBox="20 50 360 172" role="img" aria-label="Uydunun üstten görünüşü">' +
    '<defs><pattern id="cells' + uid + '" width="12" height="12" patternUnits="userSpaceOnUse">' +
    '<rect width="12" height="12" fill="#5B63E0"/><path d="M12 0H0V12" fill="none" stroke="#AEB4FF" stroke-width=".7"/></pattern></defs>' +
    '<rect data-p="pl" class="panel" fill="url(#cells' + uid + ')"/>' +
    '<rect data-p="pr" class="panel" fill="url(#cells' + uid + ')"/>' +
    '<rect data-p="body" class="body"/>' +
    '<g data-p="uhf" class="ant"><line x1="0" y1="0" x2="0" y2="-36"/><circle cx="0" cy="-38" r="3"/></g>' +
    '<g data-p="s" class="ant"><rect x="-16" y="-6" width="32" height="6"/><line x1="0" y1="-6" x2="0" y2="-22"/></g>' +
    '<g data-p="x" class="ant"><path d="M-30 -4 Q0 -46 30 -4 Z"/><line x1="0" y1="-4" x2="0" y2="0"/></g>' +
    '<g data-p="amag" class="adcs"><rect x="-13" y="-10" width="26" height="20" stroke-dasharray="3 2"/><line x1="-13" y1="-3" x2="13" y2="-3"/><line x1="-13" y1="3" x2="13" y2="3"/></g>' +
    '<g data-p="arw" class="adcs"><circle r="11"/><line x1="-11" y1="0" x2="11" y2="0"/><line x1="0" y1="-11" x2="0" y2="11"/></g>' +
    '<rect data-p="bat" class="bat"/>' +
    '<g data-p="ins"></g>' +
    '<text data-p="dim" class="dim" text-anchor="middle"></text>' +
    '<line data-p="dimline" class="dimline"/>' +
    '</svg><p class="craft-cap" data-p="cap"></p>';
}

function updateCraft(el, d) {
  var q = function (n) { return el.querySelector('[data-p="' + n + '"]'); };
  var C = CRAFT, six = d.structure === '6u';
  var h = six ? 80 : 40, yTop = C.cy - h / 2, x0 = C.cx - C.bw / 2;

  // gövde
  var b = q('body'); b.style.x = x0 + 'px'; b.style.y = yTop + 'px'; b.style.width = C.bw + 'px'; b.style.height = h + 'px';

  // paneller
  var big = d.solar === 'large', pw = big ? 100 : 56, ph = big ? 84 : 36;
  var bad = big && !six;
  var pl = q('pl'), pr = q('pr');
  [pl, pr].forEach(function (p) {
    p.style.width = pw + 'px'; p.style.height = ph + 'px'; p.style.y = (C.cy - ph / 2) + 'px';
    p.classList.toggle('bad', bad);
  });
  pl.style.x = (x0 - 4 - pw) + 'px';
  pr.style.x = (x0 + C.bw + 4) + 'px';

  // anten (yalnızca seçilen görünür)
  ['uhf', 's', 'x'].forEach(function (k) {
    var g = q(k); g.style.opacity = d.comms === k ? 1 : 0;
    g.style.transform = 'translate(' + C.cx + 'px,' + yTop + 'px)';
  });

  // yönelim
  q('amag').style.opacity = d.adcs === 'mag' ? 1 : 0;
  q('arw').style.opacity = d.adcs === 'rw' ? 1 : 0;
  q('amag').style.transform = 'translate(' + (x0 + 20) + 'px,' + C.cy + 'px)';
  q('arw').style.transform = 'translate(' + (x0 + 20) + 'px,' + C.cy + 'px)';

  // batarya
  var bw = d.battery === 'large' ? 26 : 14, bat = q('bat');
  bat.style.x = (x0 + C.bw - 10 - bw) + 'px'; bat.style.y = (C.cy - 15) + 'px'; bat.style.width = bw + 'px'; bat.style.height = '30px';

  // enstrümanlar: yuvaya sığmayan parça gövdenin dışına taşar ve kırmızı olur
  var slots = six ? 4 : 2, ins = q('ins');
  var html = '';
  d.instruments.forEach(function (id, i) {
    var col = i % 2, row = Math.floor(i / 2);
    var cx = x0 + 62 + col * 34;
    var cy = six ? C.cy - 20 + row * 40 : C.cy + row * 40;
    var over = i >= slots;
    html += '<g class="chip' + (over ? ' over' : '') + '" transform="translate(' + cx + ' ' + cy + ')">' +
      '<rect x="-14" y="-10" width="28" height="20"/><text y="3" text-anchor="middle">' + INS_ABBR[id] + '</text></g>';
  });
  ins.innerHTML = html;

  // ölçü yazısı
  var yb = yTop + h + 20 + ((!six && d.instruments.length > 2) ? 34 : 0);
  var dl = q('dimline'); dl.setAttribute('x1', x0); dl.setAttribute('x2', x0 + C.bw); dl.setAttribute('y1', yb - 8); dl.setAttribute('y2', yb - 8);
  var dm = q('dim'); dm.setAttribute('x', C.cx); dm.setAttribute('y', yb + 8);
  dm.textContent = six ? '6U: 30 × 20 cm' : '3U: 30 × 10 cm';

  // alt yazı
  var names = {
    comms: { uhf: 'UHF telsiz', s: 'S-bant telsiz', x: 'X-bant telsiz' },
    adcs: { mag: 'manyetik tork', rw: 'reaksiyon tekerleği' }
  };
  q('cap').textContent = (six ? '6U gövde' : '3U gövde') + ', ' + (big ? 'büyük' : 'küçük') + ' panel, ' +
    (d.battery === 'large' ? 'büyük' : 'küçük') + ' batarya, ' + names.comms[d.comms] + ', ' + names.adcs[d.adcs] +
    (d.instruments.length ? ', ' + d.instruments.length + ' enstrüman' : '');
}

function drawCraft(id) {
  var el = document.getElementById(id);
  if (!el) return;
  if (!el.dataset.ready) { createCraft(el, id); el.dataset.ready = '1'; }
  updateCraft(el, design);
}
