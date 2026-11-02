import json, os, threading, webbrowser, urllib.request, urllib.error
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

APP_NAME = "VibeCraft Launcher"
APP_VERSION = "1.5.49 Beta"
GITHUB_REPO = "YOUR_GITHUB_NAME/VibeCraft-Launcher"  # Replace after creating your repo
MC_DIR = Path.home() / "VibeCraft" / ".minecraft"
CONFIG = Path.home() / "VibeCraft" / "config.json"

try:
    import minecraft_launcher_lib as mcl
except ImportError:
    mcl = None

BG = "#111225"
PANEL = "#1b1d3a"
PURPLE = "#9b5cff"
BLUE = "#36a5ff"
WHITE = "#f4f3ff"
MUTED = "#b7b8d8"

class VibeCraft:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME}  •  v{APP_VERSION}")
        self.root.geometry("880x600")
        self.root.minsize(760, 520)
        self.root.configure(bg=BG)
        self.config = self.load_config()
        self.versions = []
        self.music_window = None
        self.music_images = []
        self.build_ui()
        self.check_updates()
        self.load_versions()

    def load_config(self):
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            return {"skin_path": "", "ram_gb": 4}

    def save_config(self):
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(self.config, indent=2), encoding="utf-8")

    def build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=24, pady=(22, 12))
        tk.Label(top, text="Vibe", font=("Segoe UI", 28, "bold"), fg=WHITE, bg=BG).pack(side="left")
        tk.Label(top, text="CRAFT", font=("Segoe UI", 28, "bold"), fg=BLUE, bg=BG).pack(side="left")
        tk.Label(top, text=f"LAUNCHER  v{APP_VERSION}", font=("Segoe UI", 10, "bold"),
                 fg=MUTED, bg=BG).pack(side="right", pady=14)

        body = tk.Frame(self.root, bg=PANEL, highlightbackground="#34365d", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=24, pady=8)
        left = tk.Frame(body, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=24, pady=24)
        right = tk.Frame(body, bg="#17182f", width=250)
        right.pack(side="right", fill="y", padx=(0, 0))
        right.pack_propagate(False)

        tk.Label(left, text="ТВОЯ ИГРА. ТВОЙ ВАЙБ.", font=("Segoe UI", 18, "bold"),
                 fg=WHITE, bg=PANEL).pack(anchor="w")
        tk.Label(left, text="Выбери версию Minecraft Java Edition", font=("Segoe UI", 10),
                 fg=MUTED, bg=PANEL).pack(anchor="w", pady=(6, 18))

        row = tk.Frame(left, bg=PANEL); row.pack(fill="x")
        self.version_var = tk.StringVar(value="Загрузка списка версий…")
        self.version_box = ttk.Combobox(row, textvariable=self.version_var, state="readonly", width=36)
        self.version_box.pack(side="left", ipady=6)
        tk.Button(row, text="⟳", command=self.load_versions, bg=PURPLE, fg="white",
                  relief="flat", padx=14, pady=7).pack(side="left", padx=8)

        self.status = tk.StringVar(value="Готов к работе.")
        tk.Label(left, textvariable=self.status, wraplength=460, justify="left",
                 font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(20, 10))

        self.progress = ttk.Progressbar(left, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 16))
        tk.Button(left, text="⬇  УСТАНОВИТЬ ВЕРСИЮ", command=self.install_version,
                  bg=BLUE, fg="#101226", activebackground="#70c0ff",
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=12).pack(fill="x", pady=4)
        tk.Button(left, text="▶  ИГРАТЬ", command=self.launch_notice,
                  bg=PURPLE, fg="white", activebackground="#b38aff",
                  font=("Segoe UI", 12, "bold"), relief="flat", pady=13).pack(fill="x", pady=4)
        tk.Button(left, text="Папка игры", command=self.open_game_folder,
                  bg="#2b2d50", fg=WHITE, relief="flat", pady=8).pack(fill="x", pady=4)
        tk.Button(left, text="♫  МУЗЫКА VIBECRAFT", command=self.open_music,
                  bg="#25264b", fg="#8fcaff", activebackground="#353866",
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=10).pack(fill="x", pady=(10, 4))

        tk.Label(right, text="ПРОФИЛЬ", font=("Segoe UI", 12, "bold"), fg=WHITE, bg="#17182f").pack(
            anchor="w", padx=20, pady=(24, 10))
        tk.Label(right, text="Скин Minecraft (PNG)", font=("Segoe UI", 10), fg=MUTED,
                 bg="#17182f").pack(anchor="w", padx=20)
        self.skin_label = tk.Label(right, text=Path(self.config.get("skin_path") or "Скин не выбран").name,
                                   wraplength=200, fg=WHITE, bg="#17182f")
        self.skin_label.pack(anchor="w", padx=20, pady=(5, 10))
        tk.Button(right, text="Выбрать PNG", command=self.choose_skin, bg="#30335c",
                  fg=WHITE, relief="flat", pady=8).pack(fill="x", padx=20)
        tk.Label(right, text="Скин пока сохраняется локально.\nДля применения в игре нужна\nавторизация и загрузка в профиль.",
                 font=("Segoe UI", 9), fg=MUTED, bg="#17182f", justify="left").pack(
            anchor="w", padx=20, pady=(10, 22))
        tk.Label(right, text="АККАУНТ", font=("Segoe UI", 12, "bold"), fg=WHITE,
                 bg="#17182f").pack(anchor="w", padx=20, pady=(0, 8))
        tk.Button(right, text="Войти через Microsoft", command=self.auth_notice,
                  bg="#30335c", fg=WHITE, relief="flat", pady=8).pack(fill="x", padx=20)
        tk.Label(right, text="Нужен аккаунт с правом\nиграть в Java Edition.",
                 font=("Segoe UI", 9), fg=MUTED, bg="#17182f", justify="left").pack(
            anchor="w", padx=20, pady=(8, 0))

        tk.Label(self.root, text="Прототип • неофициальный проект, не связан с Mojang или Microsoft",
                 font=("Segoe UI", 8), fg="#77799c", bg=BG).pack(pady=(4, 10))

    def set_status(self, text):
        self.root.after(0, lambda: self.status.set(text))

    def load_versions(self):
        if mcl is None:
            self.status.set("Не установлены зависимости. Запусти install_dependencies.bat.")
            return
        self.status.set("Получаю список версий с официального манифеста Minecraft…")
        def worker():
            try:
                items = mcl.utils.get_version_list()
                versions = [x["id"] for x in items]
                latest = mcl.utils.get_latest_version().get("release")
                def done():
                    self.versions = versions
                    self.version_box["values"] = versions
                    if latest in versions:
                        self.version_var.set(latest)
                    elif versions:
                        self.version_var.set(versions[0])
                    self.status.set(f"Загружено версий: {len(versions)}. Последний релиз: {latest or 'неизвестно'}.")
                self.root.after(0, done)
            except Exception as e:
                self.set_status(f"Не удалось получить список версий: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def install_version(self):
        if mcl is None:
            messagebox.showerror("Нет зависимости", "Запусти install_dependencies.bat.")
            return
        version = self.version_var.get()
        if not version or version.startswith("Загрузка"):
            messagebox.showwarning("Версия не выбрана", "Сначала загрузи список версий.")
            return
        self.progress["value"] = 0
        self.status.set(f"Устанавливаю Minecraft {version} и необходимые файлы…")
        def worker():
            try:
                MC_DIR.mkdir(parents=True, exist_ok=True)
                def set_progress(p): self.root.after(0, lambda: self.progress.configure(value=p))
                def download_cb(data):
                    if data.get("total"):
                        set_progress(100 * data.get("current", 0) / data["total"])
                callback = {
                    "setStatus": lambda s: self.set_status(str(s)),
                    "setProgress": set_progress,
                    "setMax": lambda m: None,
                    "set_current": lambda c: None,
                    "set_max": lambda m: None,
                    "set_progress": set_progress,
                    "download_callback": download_cb,
                }
                mcl.install.install_minecraft_version(version, str(MC_DIR), callback=callback)
                self.set_status(f"Minecraft {version} установлен. Java Runtime для версии будет управляться библиотекой при подготовке запуска.")
                self.root.after(0, lambda: messagebox.showinfo("Готово", f"Файлы Minecraft {version} загружены."))
            except Exception as e:
                self.set_status(f"Ошибка установки: {e}")
                self.root.after(0, lambda: messagebox.showerror("Ошибка установки", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def choose_skin(self):
        path = filedialog.askopenfilename(title="Выбери скин PNG", filetypes=[("PNG images", "*.png")])
        if path:
            self.config["skin_path"] = path
            self.save_config()
            self.skin_label.config(text=Path(path).name)
            self.status.set("Путь к PNG-скину сохранён локально.")

    def open_game_folder(self):
        MC_DIR.mkdir(parents=True, exist_ok=True)
        import subprocess, sys
        try:
            if sys.platform == "win32": os.startfile(str(MC_DIR))
            else: webbrowser.open(MC_DIR.as_uri())
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def launch_notice(self):
        messagebox.showinfo("Запуск игры",
            "Установка файлов доступна. Запуск игры появится после настройки безопасной авторизации Microsoft/Xbox и проверки владения Minecraft Java Edition. "
            "Лаунчер не будет обходить проверку лицензии или использовать фиктивный офлайн-аккаунт.")

    def auth_notice(self):
        messagebox.showinfo("Microsoft", "Для входа нужна регистрация публичного приложения OAuth и поддержка цепочки Microsoft → Xbox Live → Minecraft Services. "
            "Не вводи пароль Microsoft в это окно и не отправляй его разработчику. Эта часть ещё не подключена.")

    def open_music(self):
        if self.music_window and self.music_window.winfo_exists():
            self.music_window.lift()
            return
        win = tk.Toplevel(self.root)
        self.music_window = win
        win.title("VibeCraft • Музыка")
        win.geometry("760x650")
        win.minsize(600, 450)
        win.configure(bg=BG)
        header = tk.Frame(win, bg=BG)
        header.pack(fill="x", padx=22, pady=(20, 10))
        tk.Label(header, text="VIBE", font=("Segoe UI", 23, "bold"), fg=WHITE, bg=BG).pack(side="left")
        tk.Label(header, text="MUSIC", font=("Segoe UI", 23, "bold"), fg=BLUE, bg=BG).pack(side="left", padx=(6,0))
        tk.Label(win, text="Твой плейлист • добавь свои аудиофайлы для воспроизведения",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(anchor="w", padx=24, pady=(0,12))

        outer = tk.Frame(win, bg=PANEL)
        outer.pack(fill="both", expand=True, padx=20, pady=(0,16))
        canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        list_frame = tk.Frame(canvas, bg=PANEL)
        list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=list_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(1, width=e.width))

        tracks = [
            ("Aria Math", "Alterity", "aria_math_alterity.jpg", "aria_math_alterity"),
            ("Minecraft 2", "bxkq", "minecraft_2.jpg", "minecraft_2"),
            ("Living Mice", "OSRSBeatz", "living_mice.jpg", "living_mice"),
            ("Aria Math", "bxkq, Hardx", "aria_math_bxkq_hardx.jpg", "aria_math_bxkq_hardx"),
            ("Recollection", "Sx1nxwy", "recollection.jpg", "recollection"),
            ("Arch-Illager's Pigstep", "Hyper Potions", "arch_illagers_pigstep.jpg", "arch_illagers_pigstep"),
        ]
        self.music_images = []
        self.music_status = tk.StringVar(value="Выбери аудиофайл для трека, чтобы добавить его в плеер.")
        for title, artist, cover, key in tracks:
            row = tk.Frame(list_frame, bg="#202243", padx=10, pady=9)
            row.pack(fill="x", padx=10, pady=5)
            image_path = os.path.join(os.path.dirname(__file__), "music_covers", cover)
            try:
                img = Image.open(image_path).convert("RGB")
                img.thumbnail((68,68))
                photo = tk.PhotoImage(data=self._image_to_png_bytes(img))
                self.music_images.append(photo)
                tk.Label(row, image=photo, bg="#202243").pack(side="left", padx=(0,12))
            except Exception:
                tk.Label(row, text="♫", font=("Segoe UI", 22), fg=BLUE, bg="#202243", width=4).pack(side="left")
            names = tk.Frame(row, bg="#202243")
            names.pack(side="left", fill="x", expand=True)
            tk.Label(names, text=title, font=("Segoe UI", 12, "bold"), fg=WHITE, bg="#202243").pack(anchor="w")
            tk.Label(names, text=artist, font=("Segoe UI", 9), fg=MUTED, bg="#202243").pack(anchor="w")
            audio = self.config.get("music_files", {}).get(key, "")
            label = tk.Label(names, text=os.path.basename(audio) if audio else "Аудиофайл не выбран",
                             font=("Segoe UI", 8), fg="#9b9fc8", bg="#202243")
            label.pack(anchor="w", pady=(3,0))
            actions = tk.Frame(row, bg="#202243"); actions.pack(side="right")
            tk.Button(actions, text="Выбрать файл", command=lambda k=key,l=label: self.choose_music_file(k,l),
                      bg="#30335c", fg=WHITE, relief="flat", padx=8, pady=6).pack(pady=2)
            tk.Button(actions, text="▶ Открыть", command=lambda k=key: self.play_music_file(k),
                      bg=PURPLE, fg="white", relief="flat", padx=8, pady=6).pack(pady=2)
        tk.Label(win, textvariable=self.music_status, fg=MUTED, bg=BG, wraplength=700,
                 justify="left").pack(anchor="w", padx=24, pady=(0,18))

    @staticmethod
    def _image_to_png_bytes(img):
        import io, base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue())

    def choose_music_file(self, key, label):
        path = filedialog.askopenfilename(title="Выбери аудиофайл",
            filetypes=[("Аудиофайлы", "*.mp3 *.wav *.ogg *.flac *.m4a"), ("Все файлы", "*.*")])
        if path:
            self.config.setdefault("music_files", {})[key] = path
            self.save_config()
            label.config(text=os.path.basename(path))
            self.music_status.set("Файл сохранён в плейлисте.")

    def play_music_file(self, key):
        path = self.config.get("music_files", {}).get(key, "")
        if not path or not os.path.isfile(path):
            messagebox.showinfo("Аудиофайл не выбран",
                "Нажми «Выбрать файл» и укажи аудиофайл, который у тебя есть или разрешён к использованию.")
            return
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            if self.music_window and self.music_window.winfo_exists():
                self.music_status.set("Сейчас играет: " + os.path.basename(path))
        except ImportError:
            try:
                import subprocess, sys
                if sys.platform == "win32": os.startfile(path)
                else: webbrowser.open(Path(path).resolve().as_uri())
                self.music_status.set("Открыл аудиофайл в приложении по умолчанию. Установи pygame для встроенного плеера.")
            except Exception as e:
                messagebox.showerror("Не удалось открыть аудио", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка воспроизведения", str(e))

    def check_updates(self):
        if "YOUR_GITHUB_NAME" in GITHUB_REPO:
            return
        def worker():
            try:
                url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                req = urllib.request.Request(url, headers={"User-Agent": "VibeCraft-Launcher"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    release = json.loads(response.read().decode("utf-8"))
                latest = release.get("tag_name", "").lstrip("v")
                if latest and latest != APP_VERSION:
                    self.root.after(0, lambda: self.offer_update(release))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def offer_update(self, release):
        if messagebox.askyesno("Доступно обновление",
                f"Найдена версия {release.get('tag_name')}.\nОткрыть страницу загрузки?"):
            webbrowser.open(release.get("html_url", "https://github.com"))

if __name__ == "__main__":
    root = tk.Tk()
    app = VibeCraft(root)
    root.mainloop()
