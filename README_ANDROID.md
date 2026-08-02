# Manpower Allocation & Budget — Android App

A Kivy-based Android port of the standalone Manpower tool, with an
"HR Login" screen matching the desktop app. Same underlying business
logic and SQLite schema as `manpower_app.py` (the Windows/desktop
version) — only the UI was rewritten, because Tkinter (what the
desktop app uses) cannot run on Android at all. Kivy is the Python UI
framework that can.

## Files in this folder

```
kivy_app/
├── main.py                          # Kivy UI: Login, Dashboard, Staff Roster
├── manpower_data.py                 # Same CRUD/summary logic as the desktop
│                                       app's manpower_allocation.py, with the
│                                       Tkinter GUI class and openpyxl Excel
│                                       export removed (Android can't use
│                                       either) — nothing about how numbers
│                                       are calculated changed
├── database.py                      # Same SQLite + login/auth module used
│                                       by the desktop app, unchanged
├── buildozer.spec                   # Android packaging config
└── .github/workflows/build-apk.yml  # Builds the .apk automatically in
                                        GitHub's cloud — see below
```

## Why the actual .apk isn't attached here

Compiling an Android app needs the Android SDK, NDK, and Java build
tools — several gigabytes of downloads — plus a full `python-for-android`
build. I generated this in a **sandbox with no internet access**, so
there was no way to run that build here, even in principle. All the
source code is ready and tested (the data layer — login, all the
add/edit/delete/summary logic — has been run and verified); what's left
is strictly the packaging step, which needs to happen somewhere with
internet access. Two ways to do that:

## Option A — Build in the cloud with GitHub Actions (recommended, free, no setup)

1. Create a new GitHub repository and push this whole `kivy_app` folder
   to it (the `.github/workflows/build-apk.yml` file must stay at that
   exact path).
2. On GitHub, open the repo's **Actions** tab. The `Build Android APK`
   workflow runs automatically on push, or click **Run workflow** to
   trigger it by hand.
3. The build takes ~15–20 minutes the first time (it's compiling
   Python and Kivy for Android from source). When it finishes, open
   the completed run and download the **ranaya-manpower-apk** artifact
   — that's your `.apk`.
4. Copy that `.apk` to an Android phone (email, USB, Google Drive,
   whatever's convenient) and tap it to install. You'll need to allow
   "install unknown apps" for whichever app you used to open it —
   Android will prompt you the first time.

## Option B — Build locally on a Linux machine

Buildozer only builds on Linux (or WSL2 on Windows).

```bash
pip install buildozer cython
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf \
    libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev

cd kivy_app
buildozer android debug
```

The first run downloads the Android SDK/NDK automatically (several GB)
and can take 30–60 minutes. The finished file lands at
`bin/ranayamanpower-1.0-arm64-v8a_armeabi-v7a-debug.apk`.

## What's in the app

- **HR Login** — same `users` table and `verify_login()` as the
  desktop app. Default login: username `hr`, password `hr@123`,
  forced password change on first login.
- **Dashboard tab** — floor filter, budget summary tiles (allocated /
  current / vacant / budget / vacancy %), category breakdown list.
- **Staff Roster tab** — floor + department filters, tap any position
  to edit or delete it, "+ Add Position" for a new slot, and an
  "Export CSV" button (saves into the app's private storage — Excel
  export via openpyxl was left out of the mobile build to avoid a
  fragile Android dependency, but CSV opens fine in Sheets/Excel).
- **Logout** button in the header.

## Data storage on Android

The app creates its own `payroll.db` inside Android's app-private
storage (`App.user_data_dir` — this is standard, sandboxed per-app
storage that survives app updates but is removed if the app is
uninstalled). It is **separate** from the desktop app's `payroll.db` —
the two don't sync with each other automatically. If you need the
phone and desktop tool to share data, that would need a shared backend
(e.g. syncing the .db file manually, or a small server) rather than
each keeping its own local file — happy to help design that if it's
useful.

## Known limitations of this first mobile build

- No Excel export (CSV only) — see above.
- List rows use a simple tap-to-open detection; a fast scroll gesture
  can occasionally register as a tap. Minor annoyance, not a
  data-safety issue (it just reopens the edit form, nothing is changed
  unless you hit Save).
- Not tested on a real device yet since I can't run Android here —
  worth doing a full pass through every screen after your first build.
