import tkinter as tk
from tkinter import filedialog, Canvas, messagebox, colorchooser, simpledialog
import numpy as np
import pydicom
from PIL import Image, ImageTk, ImageDraw
import os


class CTImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("CT Scan Viewer and Editor")

        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open Folder", command=self.open_folder)
        self.file_menu.add_command(label="Save", command=self.save_image)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.menu_bar.add_command(label="Pencil", command=self.use_pencil)
        self.menu_bar.add_command(label="Eraser", command=self.use_eraser)
        self.menu_bar.add_command(label="Choose Color", command=self.choose_color)

        # Добавляем команду "Line Width", при нажатии на которую появляется окно ввода толщины линии
        self.menu_bar.add_command(label="Line Width", command=self.ask_line_width)

        self.canvas = Canvas(root, width=600, height=600, bg="white")
        self.canvas.pack()

        self.image = None
        self.tk_image = None
        self.image_files = []
        self.current_index = 0
        self.drawn_objects = []

        self.tool = "pencil"
        self.pencil_color = "black"
        self.line_width = 5

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<MouseWheel>", self.scroll_images)
        self.canvas.bind("<Button-4>", self.scroll_images)
        self.canvas.bind("<Button-5>", self.scroll_images)

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
        self.canvas.delete("all")
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

        if event.num == 4 or event.delta > 0:
            self.current_index = (self.current_index - 1) % len(self.image_files)
        elif event.num == 5 or event.delta < 0:
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

    def ask_line_width(self):
        # Всплывающее окно для ввода толщины линии
        line_width = simpledialog.askinteger("Line Width", "Enter line width (1-20):", minvalue=1, maxvalue=20, initialvalue=self.line_width)
        if line_width:
            self.line_width = line_width

    def paint(self, event):
        color = self.pencil_color if self.tool == "pencil" else "white"

        if self.tool == "eraser":
            items = self.canvas.find_overlapping(event.x - self.line_width, event.y - self.line_width, event.x + self.line_width, event.y + self.line_width)
            for item in items:
                if item in self.drawn_objects:
                    self.canvas.delete(item)
                    self.drawn_objects.remove(item)
        else:
            obj = self.canvas.create_oval(event.x - self.line_width, event.y - self.line_width, event.x + self.line_width, event.y + self.line_width, fill=color,
                                          outline=color)
            self.drawn_objects.append(obj)

    def save_image(self):
        if not self.image:
            messagebox.showerror("Error", "No image to save.")
            return

        final_image = self.image.copy()
        draw = ImageDraw.Draw(final_image)

        for obj in self.drawn_objects:
            coords = self.canvas.coords(obj)
            color = self.canvas.itemcget(obj, 'fill')

            draw.ellipse([coords[0], coords[1], coords[2], coords[3]], fill=color, outline=color)

        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png"), ("JPEG Files", "*.jpg;*.jpeg")])
        if save_path:
            final_image.save(save_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = CTImageEditor(root)
    root.mainloop()
