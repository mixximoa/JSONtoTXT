import json
import os
from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Fbo, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import platform


class CadastreConverterApp(App):

    def build(self):
        # Запит дозволів на Android під час запуску
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions(
                [
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                ]
            )

        self.layout = BoxLayout(orientation="vertical", padding=15, spacing=10)

        self.label_info = Label(
            text="Конвертер ДЗК (JSON -> TXT / JPG)\nОберіть JSON файл з кадастру",
            size_hint=(1, 0.15),
            halign="center",
            valign="middle",
        )
        self.label_info.bind(size=self.label_info.setter("text_size"))
        self.layout.add_widget(self.label_info)

        self.btn_choose = Button(
            text="Обрати JSON файл (Папка Download)",
            size_hint=(1, 0.12),
            background_color=(0.1, 0.45, 0.75, 1),
        )
        self.btn_choose.bind(on_release=self.show_filechooser)
        self.layout.add_widget(self.btn_choose)

        self.preview_image = KivyImage(size_hint=(1, 0.73))
        self.layout.add_widget(self.preview_image)

        return self.layout

    def show_filechooser(self, instance):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Стартова папка Download на Android
        start_path = "/storage/emulated/0/Download"
        if not os.path.exists(start_path):
            start_path = os.path.expanduser("~")

        self.fc = FileChooserListView(path=start_path, filters=["*.json"])
        content.add_widget(self.fc)

        btn_box = BoxLayout(size_hint=(1, 0.15), spacing=10)
        btn_select = Button(
            text="Конвертувати", background_color=(0.1, 0.6, 0.2, 1)
        )
        btn_cancel = Button(
            text="Скасувати", background_color=(0.7, 0.2, 0.2, 1)
        )

        btn_box.add_widget(btn_select)
        btn_box.add_widget(btn_cancel)
        content.add_widget(btn_box)

        self.popup = Popup(
            title="Оберіть JSON файл", content=content, size_hint=(0.95, 0.9)
        )
        btn_select.bind(on_release=self.on_file_selected)
        btn_cancel.bind(on_release=self.popup.dismiss)
        self.popup.open()

    def on_file_selected(self, instance):
        if not self.fc.selection:
            return
        json_path = self.fc.selection[0]
        self.popup.dismiss()

        try:
            txt_path, jpg_path = self.convert_cadastre(json_path)
            self.label_info.text = (
                f"Готово! Файли збережено у папці:\n{os.path.dirname(txt_path)}\n"
                f"{os.path.basename(txt_path)} та {os.path.basename(jpg_path)}"
            )
            self.preview_image.source = jpg_path
            self.preview_image.reload()
        except Exception as e:
            self.label_info.text = f"Помилка: {str(e)}"

    def convert_cadastre(self, json_path):
        out_dir = os.path.dirname(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cadnum = data.get("properties", {}).get("cadnum", "unknown")
        base_name = cadnum.replace(":", "")

        coords_raw = data["coordinates"][0][0]
        points = (
            coords_raw[:-1] if coords_raw[0] == coords_raw[-1] else coords_raw
        )

        # 1. Запис TXT-файлу для RTK контролера (Номер, X_Північ, Y_Схід, 0)
        txt_path = os.path.join(out_dir, f"{base_name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for idx, pt in enumerate(points, 1):
                y_east, x_north = pt[0], pt[1]
                f.write(f"{idx},{x_north:.2f},{y_east:.2f},0\n")

        # 2. Побудова JPG схеми вбудованим графічним рушієм Kivy Fbo
        img_size = 1000
        padding = 140
        fbo = Fbo(size=(img_size, img_size))

        ys = [p[0] for p in points]
        xs = [p[1] for p in points]
        min_y, max_y = min(ys), max(ys)
        min_x, max_x = min(xs), max(xs)

        span_y = max(max_y - min_y, 0.001)
        span_x = max(max_x - min_x, 0.001)
        scale = (img_size - 2 * padding) / max(span_y, span_x)

        offset_px = (img_size - span_y * scale) / 2.0
        offset_py = (img_size - span_x * scale) / 2.0

        # У Kivy вісь Y екрана вже йде знизу вгору (як геодезичний X Північ)
        pixel_points = []
        for y, x in points:
            px = offset_px + (y - min_y) * scale
            py = offset_py + (x - min_x) * scale
            pixel_points.append((px, py))

        center_px = sum(p[0] for p in pixel_points) / len(pixel_points)
        center_py = sum(p[1] for p in pixel_points) / len(pixel_points)

        with fbo:
            # Білий фон
            Color(1, 1, 1, 1)
            Rectangle( pos=(0, 0), size=(img_size, img_size))

            # Темно-синій контур ділянки
            Color(0.08, 0.13, 0.24, 1)
            flat_pts = []
            for px, py in pixel_points:
                flat_pts.extend([px, py])
            flat_pts.extend([pixel_points[0][0], pixel_points[0][1]])
            Line(points=flat_pts, width=2.2)

            # Квадратні маркери та номери поворотних точок
            for idx, (px, py) in enumerate(pixel_points, 1):
                s = 6
                Color(1, 1, 1, 1)
                Rectangle(pos=(px - s, py - s), size=(s * 2, s * 2))
                Color(0.08, 0.13, 0.24, 1)
                Line(rectangle=(px - s, py - s, s * 2, s * 2), width=1.5)

                # Зсув номера точки назовні від центру ділянки
                dx = px - center_px
                dy = py - center_py
                dist = max((dx**2 + dy**2) ** 0.5, 1.0)
                tx = px + (dx / dist) * 28
                ty = py + (dy / dist) * 28

                lbl = CoreLabel(text=str(idx), font_size=24, color=(0, 0, 0, 1))
                lbl.refresh()
                tex = lbl.texture
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=tex,
                    pos=(tx - tex.width / 2, ty - tex.height / 2),
                    size=tex.size,
                )

            # Кадастровий номер у центрі ділянки
            cad_lbl = CoreLabel(text=cadnum, font_size=24, color=(0, 0, 0, 1))
            cad_lbl.refresh()
            ctex = cad_lbl.texture
            Color(1, 1, 1, 1)
            Rectangle(
                texture=ctex,
                pos=(center_px - ctex.width / 2, center_py - ctex.height / 2),
                size=ctex.size,
            )

        fbo.draw()
        jpg_path = os.path.join(out_dir, f"{base_name}.jpg")
        fbo.texture.save(jpg_path, flipped=False)
        return txt_path, jpg_path


if __name__ == "__main__":
    CadastreConverterApp().run()
