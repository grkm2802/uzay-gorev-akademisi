// Ekran yönetimi: intro -> brief -> design
function show(id) {
  document.querySelectorAll('.screen').forEach(function (s) {
    s.classList.toggle('active', s.id === id);
  });
  document.body.classList.toggle('in-intro', id === 'intro');
  window.scrollTo(0, 0);
  if (id === 'brief') { document.getElementById('dialogText').textContent = DIALOG; drawCraft('craftBrief'); }
}

var DIALOG = 'Hoş geldin, stajyer! İlk işin küçük bir uydu: tek bir ölçüm yapacak ve altı ay dayanacak. ' +
  'Bütçe sınırlı, her kilogram ve her watt hesaplı. Önce roketi ve yörüngeyi seç, sonra uyduyu parça parça kur. Hazır olunca tasarıma geçelim.';

// --- Giriş videosu ---
var video = document.getElementById('introVideo');
var startOverlay = document.getElementById('startOverlay');
var skipBtn = document.getElementById('skipBtn');
var fallback = document.getElementById('introFallback');
var videoFailed = false;

function endIntro() {
  video.pause();
  show('brief');
}

video.addEventListener('ended', endIntro);
video.addEventListener('error', function () { videoFailed = true; });

document.getElementById('startBtn').addEventListener('click', function () {
  startOverlay.classList.add('hidden');
  if (videoFailed || video.error) {
    fallback.classList.remove('hidden');
    skipBtn.classList.remove('hidden');
    skipBtn.textContent = 'Devam ›';
    return;
  }
  skipBtn.classList.remove('hidden');
  video.play().catch(function () {
    videoFailed = true;
    fallback.classList.remove('hidden');
  });
});

skipBtn.addEventListener('click', endIntro);

// --- Diğer ekranlar ---
document.getElementById('toDesign').addEventListener('click', function () { show('design'); initDesign(); });
document.getElementById('backBrief').addEventListener('click', function () { show('brief'); });
