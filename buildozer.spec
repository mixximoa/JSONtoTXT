[app]
title = CadastreRTK
package.name = cadastretotxt
package.domain = org.geodesy
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Жорстко вказуємо python3==3.11.6 та hostpython3==3.11.6, щоб не качало Python 3.14!
requirements = hostpython3==3.11.6,python3==3.11.6,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Фіксуємо стабільний реліз python-for-android (до появи Python 3.14)
p4a.branch = v2024.01.21

[buildozer]
log_level = 1
warn_on_root = 0
