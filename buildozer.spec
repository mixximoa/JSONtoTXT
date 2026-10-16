[app]
title = CadastreRTK
package.name = cadastretotxt
package.domain = org.geodesy
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Необхідні бібліотеки для роботи нашого додатку
requirements = python3,kivy==2.3.0,pillow,plyer

orientation = portrait
fullscreen = 0

# Дозволи для Android на запис файлів
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
