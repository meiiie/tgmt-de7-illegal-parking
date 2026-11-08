# Changelog

## 1.1.0 — 2026-11-09

First public Curb desktop release for Windows x64.

- Quick Install: one progress window, per-user installation, desktop/Start shortcuts, automatic launch, upgrade and uninstall support. Existing operational data remains separate from the application.
- Consistent Curb identity, Vietnamese interface, local fonts and icons, version and publisher metadata, About, support links and privacy-preserving diagnostics.
- Abyss Blue, Void Eclipse and Silver Mist palette. One navigation bar, action-led Vietnamese labels, contextual start conditions, and save-and-review-next within the current filters. Technical analysis details are expandable.
- Native backup restore into a new directory, with existing data preserved. Video/camera inputs, polygon rules, schedules, queued analysis, evidence review, reports and exports.
- Movement confirmation for already alerted stop episodes. MERL Test006 60-second development regression changes from six duplicate alerts to three distinct stop episodes using the same detections. Independent field accuracy is not established by this test.
- Self-contained CPU runtime, YOLO26s/n, FFmpeg and attributed 30-second MERL Street Scene sample. WebView2 and Visual C++ x64 are installed from Microsoft if missing; shared-runtime installation may require Windows elevation.
- Source, dependency notices, checksums and reproducible build instructions accompany distribution.

### Known limits

- One local operator and one inference worker. No LAN/multi-user mode, plate OCR, identity matching or automatic enforcement.
- The desktop runtime uses CPU. Throughput depends on the PC and camera; do not assume all configured frames can be processed live.
- Real RTSP camera deployment, nighttime/rain performance and independent detection accuracy require site-specific validation.
- Initial binary is unsigned. Windows may show an unknown-publisher/SmartScreen warning. No claim of trusted signing is made.

## 1.0.1 — local build, 2026-11-08

- Replaced the initial traffic-light sample with MERL Street Scene Test006, with attribution in evidence exports.
- Documented the occlusion duplicate-alert regression; retained the 60-second case for subsequent fixes.

## 1.0.0 — local build, 2026-11-08

- Initial local operations application and Windows desktop packaging. Original Gradio/research pipeline retained separately.
