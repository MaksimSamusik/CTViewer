import tkinter as tk
from tkinter import filedialog, Canvas, messagebox, colorchooser, Scale
from tkinter import simpledialog
import numpy as np
import pydicom
from PIL import Image, ImageTk, ImageDraw
import os


class CTImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("CT Scan Viewer and Editor")

        self.canvas = Canvas(root, width=600, height=600, bg="white")
        self.canvas.pack()

        self.image = None
        self.tk_image = None
        self.image_files = []
        self.current_index = 0
        self.drawn_objects = []  # Список для хранения нарисованных элементов

        self.btn_open = tk.Button(root, text="Open Folder", command=self.open_folder)
        self.btn_open.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_pencil = tk.Button(root, text="Pencil", command=self.use_pencil)
        self.btn_pencil.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_eraser = tk.Button(root, text="Eraser", command=self.use_eraser)
        self.btn_eraser.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_color = tk.Button(root, text="Choose Color", command=self.choose_color)
        self.btn_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_save = tk.Button(root, text="Save", command=self.save_image)
        self.btn_save.pack(side=tk.LEFT, padx=5, pady=5)

        self.line_width = Scale(root, from_=1, to=20, orient=tk.HORIZONTAL, label="Line Width")
        self.line_width.set(5)
        self.line_width.pack(side=tk.LEFT, padx=5, pady=5)

        self.tool = "pencil"
        self.pencil_color = "black"

        self.canvas.bind("<B1-Motion>", self.paint)

        # Привязка событий прокрутки для всех ОС
        self.canvas.bind("<MouseWheel>", self.scroll_images)  # Windows/macOS
        self.canvas.bind("<Button-4>", self.scroll_images)  # Linux (скролл вверх)
        self.canvas.bind("<Button-5>", self.scroll_images)  # Linux (скролл вниз)

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.image_files = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                                       f.lower().endswith((".dcm", ".png", ".jpg", ".jpeg"))])
            self.current_index = 0
            if self.image_files:
                self.load_image()
            else:
                messagebox.showerror("Error", "No valid images found in the folder")

    def load_image(self):
        if not self.image_files:
            return
        self.canvas.delete("all")  # Очистка холста при загрузке нового изображения
        self.drawn_objects.clear()

        file_path = self.image_files[self.current_index]
        if file_path.lower().endswith(".dcm"):
            try:
                dicom_data = pydicom.dcmread(file_path)
                image_array = dicom_data.pixel_array
                image_array = ((image_array - np.min(image_array)) / (
                        np.max(image_array) - np.min(image_array)) * 255).astype(np.uint8)
                self.image = Image.fromarray(image_array).convert("RGB")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load DICOM: {e}")
                return
        else:
            self.image = Image.open(file_path).convert("RGB")

        self.image = self.image.resize((600, 600))
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def scroll_images(self, event):
        if not self.image_files:
            return

        if event.num == 4 or event.delta > 0:  # Прокрутка вверх
            self.current_index = (self.current_index - 1) % len(self.image_files)
        elif event.num == 5 or event.delta < 0:  # Прокрутка вниз
            self.current_index = (self.current_index + 1) % len(self.image_files)

        self.load_image()

    def use_pencil(self):
        self.tool = "pencil"

    def use_eraser(self):
        self.tool = "eraser"

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose Pencil Color")[1]
        if color:
            self.pencil_color = color

    def paint(self, event):
        color = self.pencil_color if self.tool == "pencil" else "white"
        size = self.line_width.get()

        if self.tool == "eraser":
            items = self.canvas.find_overlapping(event.x - size, event.y - size, event.x + size, event.y + size)
            for item in items:
                if item in self.drawn_objects:  # Удаляем только нарисованные пользователем объекты
                    self.canvas.delete(item)
                    self.drawn_objects.remove(item)
        else:
            obj = self.canvas.create_oval(event.x - size, event.y - size, event.x + size, event.y + size, fill=color,
                                          outline=color)
            self.drawn_objects.append(obj)

    def save_image(self):
        if not self.image:
            messagebox.showerror("Error", "No image to save.")
            return

        # Создаем копию исходного изображения
        final_image = self.image.copy()
        draw = ImageDraw.Draw(final_image)  # Создаем объект для рисования на изображении

        # Переносим все нарисованные элементы с холста на изображение
        for obj in self.drawn_objects:
            coords = self.canvas.coords(obj)
            color = self.canvas.itemcget(obj, 'fill')
            size = self.line_width.get()

            # Рисуем круги, как в оригинальном изображении
            draw.ellipse([coords[0], coords[1], coords[2], coords[3]], fill=color, outline=color)

        # Сохранение изображения с изменениями
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png"), ("JPEG Files", "*.jpg;*.jpeg")])
        if save_path:
            final_image.save(save_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = CTImageEditor(root)
    root.mainloop()
