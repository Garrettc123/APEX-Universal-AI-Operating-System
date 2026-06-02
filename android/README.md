# APEX OS — Android Command Dashboard

A native **Kotlin + Jetpack Compose** app that turns the APEX Universal AI
Operating System into a personal, GitHub-Mobile-style command center on your
phone. It connects to the APEX FastAPI backend and lets you watch and drive
your whole business infrastructure from one screen.

## What it does (V1)

- **Live KPI cards** — intelligence level, healthy-vs-total systems, total
  revenue, and annual projection.
- **Systems list** — every managed system with a color-coded health bar
  (worst health surfaced first), status, and performance.
- **One-tap cycles** — trigger an **Evolve**, **Optimize**, or **Revenue**
  cycle on the backend and watch every card update.
- **Repointable backend** — set your own backend URL in Settings (gear icon)
  so the app can talk to a local server or a deployed one.

## Architecture

```
MainActivity ─▶ DashboardScreen (Compose)
                     │
                     ▼
              DashboardViewModel ──▶ ApexRepository ──▶ Retrofit/Moshi ──▶ FastAPI /api/*
                                          ▲
                                     SettingsStore (base URL, SharedPreferences)
```

- `data/` — `ApexApi` (Retrofit), `ApexRepository`, `SettingsStore`, models.
- `ui/dashboard/` — `DashboardViewModel` (StateFlow UI state) + `DashboardScreen`.
- `ui/theme/` — dark, GitHub-inspired Material 3 theme.

## Backend it talks to

Endpoints added to the FastAPI app in this repo (`src/dashboard_api.py`):

| Method | Path                  | Purpose                              |
| ------ | --------------------- | ------------------------------------ |
| GET    | `/api/overview`       | KPI snapshot                         |
| GET    | `/api/systems`        | Per-system health rows               |
| GET    | `/api/revenue`        | Revenue totals + per-strategy split  |
| POST   | `/api/cycle/evolve`   | Run one self-evolution cycle         |
| POST   | `/api/cycle/optimize` | Run one optimization pass            |
| POST   | `/api/cycle/revenue`  | Run one revenue-generation cycle     |

Run the backend from the repo root:

```bash
pip install -r requirements.txt
python main.py            # serves on http://0.0.0.0:8000
```

## Build & run the app

The Gradle wrapper JAR is intentionally not committed. Generate it once, or
just open the `android/` folder in Android Studio (it sets the wrapper up for
you).

```bash
cd android
gradle wrapper            # one-time: creates ./gradlew
./gradlew assembleDebug   # builds app/build/outputs/apk/debug/app-debug.apk
./gradlew installDebug    # build + install on a connected device/emulator
```

### Pointing the app at your backend

- **Emulator → server on this machine:** default `http://10.0.2.2:8000/`
  already works.
- **Physical phone:** open Settings (gear icon) and enter
  `http://<your-computer-LAN-IP>:8000/`, or your deployed HTTPS URL.

Requirements: Android Studio (Koala+), JDK 17, Android SDK with API 34,
`minSdk` 26 (Android 8.0+).
