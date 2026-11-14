// Oyun verisi (basitleştirilmiş, eğitim amaçlı değerler).
// mass: kg, power: W (tüketim), cost: milyon $

var MISSION = {
  name: "Öğrenci CubeSat'i",
  budget: 2.5,        // $M
  mass: 12,           // kg
  lifeMonths: 6,
  minScience: 40,
  opsCostPerMonth: 0.05
};

var ORBITS = [
  { id: 'leo400', name: 'Alçak yörünge · 400 km', lifeMonths: 3, contactMin: 28, sun: 0.62, eclipseH: 0.6,
    info: 'Yere yakın: görüntü net ama atmosfer sürtünmesi uyduyu aşağı çeker, ömür kısadır.' },
  { id: 'leo600', name: 'Alçak yörünge · 600 km', lifeMonths: 12, contactMin: 34, sun: 0.62, eclipseH: 0.6,
    info: 'Sürtünme az, ömür uzun. Yer istasyonunu daha uzun görür.' },
  { id: 'sso700', name: 'Güneşle eş zamanlı · 700 km', lifeMonths: 24, contactMin: 32, sun: 0.9, eclipseH: 0.2,
    info: 'Neredeyse hep güneşte kalır (daha çok güç), ama daha güçlü bir roket ister.' }
];

var LAUNCHERS = [
  { id: 'rideshare', name: 'Paylaşımlı fırlatma', cap: 10, cost: 0.4, orbits: ['leo400', 'leo600'],
    info: 'Ucuz, ama sadece 10 kg taşır ve yörüngeyi sen seçemezsin.' },
  { id: 'small', name: 'Küçük roket', cap: 40, cost: 0.9, orbits: ['leo400', 'leo600', 'sso700'],
    info: 'Daha fazla kütle ve her yörünge, ama pahalı.' },
  { id: 'medium', name: 'Orta roket', cap: 100, cost: 1.6, orbits: ['leo400', 'leo600', 'sso700'],
    info: 'Çok güçlü; bu bütçe için gereğinden büyük.' }
];

var STRUCTURES = [
  { id: '3u', name: '3U gövde', mass: 4.0, power: 1, cost: 0.15, slots: 2, bigPanel: false,
    info: 'Küçük ve ucuz. 2 enstrüman yuvası, büyük panel taşıyamaz.' },
  { id: '6u', name: '6U gövde', mass: 7.0, power: 1, cost: 0.30, slots: 4, bigPanel: true,
    info: 'Daha geniş: 4 yuva ve büyük panel, ama ağır.' }
];

var SOLARS = [
  { id: 'small', name: 'Küçük güneş paneli', mass: 0.6, peakW: 20, cost: 0.10, needsBig: false },
  { id: 'large', name: 'Büyük güneş paneli', mass: 1.4, peakW: 45, cost: 0.25, needsBig: true }
];

var BATTERIES = [
  { id: 'small', name: 'Küçük batarya (10 Wh)', mass: 0.5, wh: 10, cost: 0.05 },
  { id: 'large', name: 'Büyük batarya (40 Wh)', mass: 1.2, wh: 40, cost: 0.12 }
];

var COMMS = [
  { id: 'uhf', name: 'UHF telsiz · 9.6 kbps', mass: 0.3, power: 2, cost: 0.05, kbps: 9.6 },
  { id: 's', name: 'S-bant · 256 kbps', mass: 0.6, power: 6, cost: 0.15, kbps: 256 },
  { id: 'x', name: 'X-bant · 2000 kbps', mass: 1.1, power: 12, cost: 0.40, kbps: 2000 }
];

var ADCS = [
  { id: 'mag', name: 'Manyetik tork (kaba yönelim)', mass: 0.3, power: 0.5, cost: 0.05, precise: false },
  { id: 'rw', name: 'Reaksiyon tekerleği (hassas yönelim)', mass: 0.9, power: 3, cost: 0.20, precise: true }
];

var INSTRUMENTS = [
  { id: 'cam', name: 'Görünür kamera', mass: 1.0, power: 4, cost: 0.20, dataMB: 40, science: 30, precise: true },
  { id: 'ir', name: 'Kızılötesi sensör', mass: 1.5, power: 6, cost: 0.35, dataMB: 20, science: 40, precise: true },
  { id: 'mag', name: 'Manyetometre', mass: 0.4, power: 1, cost: 0.10, dataMB: 2, science: 15, precise: false },
  { id: 'rad', name: 'Radyasyon dedektörü', mass: 0.5, power: 1.5, cost: 0.12, dataMB: 3, science: 15, precise: false },
  { id: 'spec', name: 'Spektrometre', mass: 2.0, power: 8, cost: 0.50, dataMB: 80, science: 55, precise: true }
];
