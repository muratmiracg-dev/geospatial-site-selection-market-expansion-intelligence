# Geospatial Site Selection & Market Expansion Intelligence

İstanbul metropolitan alanındaki kurgusal **MarmaraMart** perakende zinciri için
geliştirilmiş, uçtan uca ve denetlenebilir bir lokasyon seçimi karar destek
platformudur. H3 mikro-bölgeleri, ağ tabanlı erişim, white-space analizi, Huff çekim
modeli, spatial cross-validation, SHAP, AHP ve kısıtlı lokasyon optimizasyonunu
birleştirir.

> **Yalnızca karar desteği içindir.** Tüm ticari sonuçlar deterministik sentetik
> veriden üretilmiştir. Kişisel veya hassas veri yoktur. Çıktılar saha, ticari,
> hukuki ve yatırım incelemesi gerektirir; yatırım tavsiyesi değildir.

## Doğrulanmış çalışma özeti

| Sonuç | Pipeline çıktısı |
|---|---:|
| H3 çözünürlük-8 mikro-bölge | 5.965 |
| Aday / mevcut mağaza / rakip / POI | 24 / 10 / 96 / 720 |
| Veri kalite kontrolü | 46 toplam; 44 geçti; 2 uyarı; 0 hata |
| Test / branch coverage | 13 geçti / %96,44 |
| Kilitli bağımlılık denetimi | 87 paket / 0 bilinen zafiyet |
| Spatial CV benchmark | 320 sentetik lokasyon, 33 spatial block |
| OOF MAE / RMSE / R² | 3,819 mn TL / 5,732 mn TL / 0,964 |
| En yüksek skorlu aday | C24 — Ikitelli Industry, 81,236/100 |
| Temel senaryo portföyü | C24, C18, C17, C07 |
| Kullanılan temel bütçe | 110,000 mn TL bütçeden 93,382 mn TL |
| İlave 10 dakikalık erişilebilir nüfus | 1.329.291 |
| Toplam pazar kapsama oranı | %23,125 |
| Beklenen portföy EBIT | 28,826 mn TL |

İki uyarı, analitik sınır dışında kalan yedi sentetik rakip ve on altı sentetik POI
noktasıdır. Spatial coverage kontrollerini test etmek amacıyla tutulmuş, kritik
olmayan uyarılardır.

## Kapsam

- WGS84 veri saklama, EPSG:32635 metrik hesaplama.
- Deterministik sentetik ticari veri ve mağaza performansı.
- Geometri, CRS, koordinat, duplicate, missing-value ve spatial join kontrolleri.
- 5/10/15 dakikalık sürüş ve yürüme ağ erişim alanları.
- Düz çizgi mesafesi ile ağ erişiminin açık karşılaştırması.
- Rakip, POI, ticari çekim, maliyet ve white-space göstergeleri.
- Huff/gravity müşteri paylaşımı ve cannibalization analizi.
- 12 km spatial block CV kullanan talep modeli ve SHAP açıklamaları.
- AHP skoru, faktör katkıları ve 750 ağırlık örnekli hassasiyet analizi.
- Bütçe, minimum mesafe, kapasite ve kapsama kısıtlı optimizasyon.
- İyimser, temel ve kötümser senaryolar.
- FastAPI, PostGIS, Prometheus/Grafana, Docker Compose ve Kubernetes.
- Etkileşimli haritalar, formül tabanlı Excel, PBIP başlangıç projesi, sunum ve PDF.

## Hızlı başlangıç

Python 3.12 gereklidir.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
site-intelligence run --config configs/base.yaml
uvicorn site_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Kalite kapıları:

```bash
ruff format --check .
ruff check .
pytest --cov=site_intelligence --cov-report=term-missing --cov-fail-under=90
python scripts/verify_artifacts.py
```

## Önemli sınırlılıklar

- Analitik çalışma alanı resmi bir idari sınır değildir.
- Ulaşım ağı canlı OSM yol grafiği değil, H3 komşuluk ve köprü bağlantılarından
  oluşturulmuş deterministik bir yaklaşımdır.
- Satış, maliyet, gelir ve demografi göstergeleri sentetiktir.
- Model metrikleri gerçek saha performansını temsil etmez.
- Kira teklifi, ruhsat, görünürlük, parsel erişimi, canlı trafik ve birim ekonomi
  doğrulanmadan yatırım kararı verilmemelidir.

Ayrıntılı yöntem için [docs/methodology.md](docs/methodology.md), yönetişim için
[docs/model_card.md](docs/model_card.md), operasyon için
[docs/monitoring_runbook.md](docs/monitoring_runbook.md) ve kaynak/lisans kaydı için
[docs/data_source_license_crosswalk.md](docs/data_source_license_crosswalk.md)
belgelerine bakın.

## Lisans

Projeye ait kod ve özgün dokümantasyon [MIT Lisansı](LICENSE) ile sunulur. Harici
veri, harita karoları ve yazılımlar kendi lisanslarına tabidir.
