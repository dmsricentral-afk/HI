[app]
title = Ranaya Manpower
package.name = ranayamanpower
package.domain = org.ranayasilks

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0

# database.py, manpower_data.py, main.py all pure Python - sqlite3 is
# part of the Python standard library and bundled by python-for-android
# automatically, so it does not need to be listed separately.
requirements = python3==3.11.8,kivy==2.3.0

orientation = portrait
fullscreen = 0

# No custom icon set - buildozer uses its default Kivy icon.
# Drop a 512x512 icon.png in this folder and add this line to brand it:
# icon.filename = %(source.dir)s/icon.png

# Minimal permissions - this app only reads/writes its own private
# SQLite database and CSV export, both inside app-private storage
# (App.user_data_dir), so no storage permission is required.
android.permissions = INTERNET

android.api = 34
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
