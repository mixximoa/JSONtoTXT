import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from plyer import filechooser
from PIL import Image, ImageDraw


class CadastreConverterApp(App):

  def build(self):
    self.layout = BoxLayout(orientation="vertical", padding=20, spacing=15)

    self.label_info = Label(
        text=(
            "Конвертер ДЗК (JSON -> TXT / JPG)\nдля RTK-ровера\nНатисніть кнопку"
            " нижче, щоб обрати JSON"
        ),
        size_hint=(1, 0.2),
        halign="center",
    )
    self.layout.add_widget(self.label_info)

    self.btn_choose = Button(
        text="Обрати JSON файл",
        size_hint=(1, 0.15),
        background_color=(0.1, 0.5, 0.8, 1),
    )
    self.btn_choose.bind(on_release=self.open_file_picker)
    self.layout.add_widget(self.btn_choose)

    self.preview_image = KivyImage(size_hint=(1, 0.65))
    self.layout.add_widget(self.preview_image)

    return self.layout

  def open_file_picker(self, instance):
    filechooser.open_file(
        on_selection=self.on_file_selected, filters=[("*.json",)]
    )

  def on_file_selected(self, selection):
    if not selection:
      return
    json_path = selection[0]
    try:
      txt_path, jpg_path = self.convert_cadastre(json_path)
      self.label_info.text = (
          "Успішно збережено поряд з JSON:\n"
          f"TXT: {os.path.basename(txt_path)}\n"
          f"JPG: {os.path.basename(jpg_path)}"
      )
      self.preview_image.source = jpg_path
      self.preview_image.reload()
    except Exception as e:
      self.label_info.text = f"Помилка обробки: {str(e)}"

  def convert_cadastre(self, json_path):
    out_dir = os.path.dirname(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
      data = json.load(f)

    cadnum = data.get("properties", {}).get("cadnum", "cadastre_plot")
    base_name = cadnum.replace(":", "")

    coords_raw = data["coordinates"][0][0]
    points = (
        coords_raw[:-1] if coords_raw[0] == coords_raw[-1] else coords_raw
    )

    # 1. Створення TXT для контролера (Номер, X_Північ, Y_Схід, 0)
    txt_path = os.path.join(out_dir, f"{base_name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
      for idx, pt in enumerate(points, 1):
        f.write(f"{idx},{pt[1]:.2f},{pt[0]:.2f},0\n")

    # 2. Рендеринг JPG схеми
    img_size = 1200
    padding = 160
    img = Image.new("RGB", (img_size, img_size), "white")
    draw = ImageDraw.Draw(img)

    ys = [p[0] for p in points]
    xs = [p[1] for p in points]
    min_y, max_y = min(ys), max(ys)
    min_x, max_x = min(xs), max(xs)

    span_y = max(max_y - min_y, 0.001)
    span_x = max(max_x - min_x, 0.001)
    scale = (img_size - 2 * padding) / max(span_y, span_x)

    # Геодезична орієнтація: Y (Схід) -> горизонтально, X (Північ) -> вертикально вгору
    pixel_points = []
    for y, x in points:
      px = padding + (y - min_y) * scale
      py = (img_size - padding) - (x - min_x) * scale
      pixel_points.append((px, py))

    # Малювання контуру ділянки
    draw.polygon(pixel_points, outline=(20, 33, 61), width=4)

    # Кадастровий номер по центру
    center_px = sum(p[0] for p in pixel_points) / len(pixel_points)
    center_py = sum(p[1] for p in pixel_points) / len(pixel_points)
    draw.text((center_px, center_py), cadnum, fill="black", anchor="mm")

    # Точки та їх нумерація
    for idx, (px, py) in enumerate(pixel_points, 1):
      s = 6
      draw.rectangle(
          [px - s, py - s, px + s, py + s],
          fill="white",
          outline=(20, 33, 61),
          width=2,
      )
      dx = (px - center_px) * 0.12
      dy = (py - center_py) * 0.12
      draw.text((px + dx, py + dy), str(idx), fill="black", anchor="mm")

    jpg_path = os.path.join(out_dir, f"{base_name}.jpg")
    img.save(jpg_path, quality=95)
    return txt_path, jpg_path


if __name__ == "__main__":
  CadastreConverterApp().run()
