import json, os, threading, webbrowser, urllib.request, urllib.error, subprocess, sys, uuid, time, re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

APP_NAME = "VibeCraft Launcher"
APP_VERSION = "2.5"
GITHUB_REPO = "Goshandre/VibeCraft-Launcher"
MC_DIR = Path.home() / "VibeCraft" / ".minecraft"
CONFIG = Path.home() / "VibeCraft" / "config.json"

from vibecraft_accounts import AccountStore, AccountError
from vibecraft_cosmetics import import_texture, can_use_custom_cape, CosmeticError

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
        self.root.geometry("980x700")
        self.root.minsize(820, 620)
        self.root.configure(bg="#0b0d1b")
        self.root.option_add("*Font", ("Segoe UI", 10))
        self.config = self.load_config()
        self.accounts = AccountStore()
        self.current_user = None
        self.versions = []
        saved_user = self.config.get("session_username")
        if saved_user:
            try:
                self.current_user = self.accounts.get_user(saved_user)
            except AccountError:
                self.config.pop("session_username", None)
                self.save_config()
        self.music_window = None
        self.music_images = []
        self.game_process = None
        self.session_user = None
        self.build_ui()
        self.refresh_account()
        self.check_updates()
        self.load_versions()

    def load_config(self):
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            return {"skin_path": "", "cape_path": "", "elytra_path": "", "ram_gb": 4}

    def save_config(self):
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(self.config, indent=2), encoding="utf-8")

    def build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=28, pady=(24, 14))
        tk.Label(top, text="Vibe", font=("Segoe UI", 28, "bold"), fg=WHITE, bg=BG).pack(side="left")
        tk.Label(top, text="CRAFT", font=("Segoe UI", 28, "bold"), fg=BLUE, bg=BG).pack(side="left")
        tk.Label(top, text=f"LAUNCHER  v{APP_VERSION}", font=("Segoe UI", 10, "bold"),
                 fg=MUTED, bg=BG).pack(side="right", pady=14)

        body = tk.Frame(self.root, bg=PANEL, highlightbackground="#34365d", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=28, pady=10)
        left = tk.Frame(body, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=28, pady=28)
        right = tk.Frame(body, bg="#15172d", width=270, highlightbackground="#30345d", highlightthickness=1)
        right.pack(side="right", fill="y", padx=(0, 0))
        right.pack_propagate(False)

        tk.Label(left, text="ТВОЯ ИГРА. ТВОЙ ВАЙБ.", font=("Segoe UI", 22, "bold"),
                 fg=WHITE, bg=PANEL).pack(anchor="w")
        tk.Label(left, text="Выбери версию Minecraft Java Edition", font=("Segoe UI", 10),
                 fg=MUTED, bg=PANEL).pack(anchor="w", pady=(6, 18))

        tk.Label(left, text="ВЕРСИЯ И ЗАГРУЗЧИК", font=("Segoe UI", 9, "bold"),
                 fg="#8fcaff", bg=PANEL).pack(anchor="w", pady=(4, 7))
        row = tk.Frame(left, bg=PANEL); row.pack(fill="x")
        self.version_var = tk.StringVar(value="Загрузка списка версий…")
        self.version_box = ttk.Combobox(row, textvariable=self.version_var, state="readonly", width=36)
        self.version_box.pack(side="left", ipady=8, fill="x", expand=True)
        tk.Button(row, text="⟳", command=self.load_versions, bg=PURPLE, fg="white",
                  relief="flat", padx=14, pady=7).pack(side="left", padx=8)

        self.status = tk.StringVar(value="Готов к работе.")
        tk.Label(left, textvariable=self.status, wraplength=460, justify="left",
                 font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(20, 10))

        style = ttk.Style()
        try:
            style.theme_use("clam")
            style.configure("Vibe.Horizontal.TProgressbar", troughcolor="#101126",
                            background=PURPLE, bordercolor="#101126", lightcolor=PURPLE,
                            darkcolor=PURPLE)
        except tk.TclError:
            pass
        self.progress = ttk.Progressbar(left, mode="determinate", maximum=100,
                                        style="Vibe.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 16))
        tk.Label(left, text="В списке версии отмечены как Vanilla, Forge или Fabric. Обнови список кнопкой ⟳.",
                 font=("Segoe UI", 8), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(2, 4))
        tk.Button(left, text="▶  ИГРАТЬ", command=self.launch_game,
                  bg="#8b5cf6", fg="white", activebackground="#a78bfa",
                  activeforeground="white", cursor="hand2",
                  font=("Segoe UI", 13, "bold"), relief="flat", pady=15,
                  bd=0).pack(fill="x", pady=7)
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
        tk.Button(right, text="Выбрать плащ VibeCraft", command=self.choose_cape, bg="#493078", fg=WHITE, relief="flat", pady=8).pack(fill="x", padx=20, pady=(6, 0))
        self.cosmetic_status = tk.Label(right, text="Косметика сохраняется локально", font=("Segoe UI", 8), fg="#d4c4ff", bg="#17182f", justify="left", wraplength=205)
        self.cosmetic_status.pack(anchor="w", padx=20, pady=(8, 0))
        tk.Label(right, text="PNG пока сохраняются локально. Для отображения в Minecraft нужна интеграция с игровым модом.",
                 font=("Segoe UI", 9), fg=MUTED, bg="#17182f", justify="left").pack(
            anchor="w", padx=20, pady=(10, 22))
        tk.Label(right, text="АККАУНТ", font=("Segoe UI", 12, "bold"), fg=WHITE,
                 bg="#17182f").pack(anchor="w", padx=20, pady=(0, 8))
        self.account_label = tk.Label(right, text="Не выполнен вход", font=("Segoe UI", 9), fg=MUTED, bg="#17182f", wraplength=205, justify="left")
        self.account_label.pack(anchor="w", padx=20, pady=(0, 6))
        self.account_action = tk.Button(right, text="Войти / Регистрация", command=self.account_dialog, bg="#30335c", fg=WHITE, relief="flat", pady=8)
        self.account_action.pack(fill="x", padx=20, pady=(0, 8))
        self.logout_action = tk.Button(right, text="Выйти из аккаунта", command=self.logout, bg="#493078", fg=WHITE, relief="flat", pady=7)
        self.logout_action.pack(fill="x", padx=20, pady=(0, 8))
        self.logout_action.pack_forget()
        tk.Button(right, text="Управление ролями (владелец)", command=self.moderation_dialog, bg="#30335c", fg=WHITE, relief="flat", pady=8).pack(fill="x", padx=20, pady=(8,0))
        tk.Label(right, text="Офлайн-профиль работает только на серверах, разрешающих offline-mode. Microsoft-вход требует настройки OAuth.",
                 font=("Segoe UI", 9), fg=MUTED, bg="#17182f", justify="left").pack(
            anchor="w", padx=20, pady=(8, 0))

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=28, pady=(5, 12))
        tk.Label(footer, text="Неофициальный проект • Minecraft принадлежит Mojang/Microsoft",
                 font=("Segoe UI", 8), fg="#77799c", bg=BG).pack(side="left")
        tk.Button(footer, text="ВЫХОД", command=self.exit_launcher,
                  bg="#542d48", fg=WHITE, activebackground="#713b5f",
                  relief="flat", padx=20, pady=7).pack(side="right")

    def set_status(self, text):
        self.root.after(0, lambda: self.status.set(text))

    def load_versions(self):
        if mcl is None:
            self.status.set("Не установлены зависимости. Запусти install_dependencies.bat.")
            return
        self.status.set("Загружаю каталог Minecraft, Forge и Fabric…")
        def worker():
            try:
                from urllib.request import Request, urlopen
                def get_json(url):
                    req = Request(url, headers={"User-Agent": "VibeCraft-Launcher/2.4"})
                    with urlopen(req, timeout=25) as response:
                        return json.loads(response.read().decode("utf-8"))

                # Mojang manifest is the source of truth for Java versions.
                manifest = get_json("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
                versions = [v["id"] for v in manifest.get("versions", [])
                            if v.get("type") == "release" and v.get("id")]
                latest = manifest.get("latest", {}).get("release")
                fabric_games = set()
                forge_games = set()
                errors = []
                try:
                    fabric_data = get_json("https://meta.fabricmc.net/v2/versions/game")
                    fabric_games = {v.get("version") for v in fabric_data
                                    if v.get("version") and v.get("stable", True)}
                except Exception as exc:
                    errors.append("Fabric: " + str(exc))
                try:
                    promos = get_json("https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json").get("promos", {})
                    for key in promos:
                        if key.endswith(("-recommended", "-latest")):
                            game_ver = key.rsplit("-", 1)[0]
                            forge_games.add(game_ver)
                except Exception as exc:
                    errors.append("Forge: " + str(exc))

                catalog = []
                for ver in versions:
                    catalog.append(f"{ver}  |  Vanilla")
                    if ver in forge_games:
                        catalog.append(f"{ver}  |  Forge")
                    if ver in fabric_games:
                        catalog.append(f"{ver}  |  Fabric")

                def done():
                    self.versions = versions
                    self.version_box["values"] = catalog
                    preferred = self.version_var.get().strip()
                    if preferred not in catalog:
                        preferred = f"{latest}  |  Vanilla" if latest else (catalog[0] if catalog else "")
                    self.version_var.set(preferred)
                    msg = f"Загружено: {len(versions)} версий Minecraft, {len(catalog)} вариантов с загрузчиками."
                    if errors:
                        msg += " Не удалось получить часть метаданных: " + " | ".join(errors)
                    self.status.set(msg)
                self.root.after(0, done)
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda: self.status.set("Не удалось загрузить каталог: " + msg))
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
                error_text = str(e)
                self.root.after(0, lambda msg=error_text: messagebox.showerror("Ошибка установки", msg))
        threading.Thread(target=worker, daemon=True).start()

    def _choose_texture(self, kind, title):
        path = filedialog.askopenfilename(title=title, filetypes=[("PNG images", "*.png")])
        if not path: return
        try:
            if kind == "cape" and not can_use_custom_cape(self.current_user):
                raise CosmeticError("Свой плащ открывается с ранга Профи (25 часов). До этого действует стартовый плащ VibeCraft.")
            stored = import_texture(path, MC_DIR, kind)
            key = {"skin":"skin_path", "cape":"cape_path", "elytra":"elytra_path"}[kind]
            self.config[key] = str(stored); self.save_config()
            label = {"skin":"Скин", "cape":"Плащ", "elytra":"Элитры"}[kind]
            self.cosmetic_status.config(text=f"{label} сохранены: {stored.name}\nНужен совместимый игровой мод.")
            self.status.set(f"{label} PNG проверен и сохранён.")
            messagebox.showinfo("VibeCraft", f"{label} сохранены.\n\nЭто пока подготовленный PNG. Для отображения в одиночной игре нужен клиентский мод, а для отображения другим игрокам — серверная синхронизация.")
        except (CosmeticError, OSError) as exc: messagebox.showerror("Не удалось выбрать косметику", str(exc))

    def choose_skin(self): self._choose_texture("skin", "Выбери скин Minecraft PNG")
    def choose_cape(self): self._choose_texture("cape", "Выбери плащ Minecraft PNG 64×32")
    def choose_elytra(self): self._choose_texture("elytra", "Выбери текстуру элитр PNG 64×32")

    def account_dialog(self):
        win = tk.Toplevel(self.root); win.title("Аккаунт VibeCraft"); win.geometry("360x330"); win.configure(bg=BG); win.resizable(False, False)
        tk.Label(win, text="ВХОД / РЕГИСТРАЦИЯ", fg=WHITE, bg=BG, font=("Segoe UI", 14, "bold")).pack(pady=14)
        fields = {}
        for label, key, secret in (("Никнейм", "username", False), ("Пароль", "password", True), ("Ключ владельца (только при первой настройке)", "bootstrap", True)):
            tk.Label(win, text=label, fg=MUTED, bg=BG).pack(anchor="w", padx=24)
            ent=tk.Entry(win, show="•" if secret else "", width=38); ent.pack(padx=24, pady=(2,8)); fields[key]=ent
        def register():
            try:
                user=self.accounts.register(fields['username'].get(), fields['password'].get(), fields['bootstrap'].get() or None)
                self.current_user=user
                self.config["session_username"] = user["username"]; self.save_config()
                self.refresh_account(); messagebox.showinfo("VibeCraft", f"Аккаунт создан: {user['rank']}", parent=win); win.destroy()
            except AccountError as e: messagebox.showerror("Не удалось зарегистрироваться", str(e), parent=win)
        def login():
            try:
                self.current_user=self.accounts.authenticate(fields['username'].get(), fields['password'].get())
                self.config["session_username"] = self.current_user["username"]; self.save_config()
                self.refresh_account(); win.destroy()
            except AccountError as e: messagebox.showerror("Ошибка входа", str(e), parent=win)
        bar=tk.Frame(win,bg=BG); bar.pack(pady=10)
        tk.Button(bar,text="Войти",command=login,bg=PURPLE,fg=WHITE,relief="flat",padx=18,pady=8).pack(side="left",padx=5)
        tk.Button(bar,text="Регистрация",command=register,bg=BLUE,fg=BG,relief="flat",padx=18,pady=8).pack(side="left",padx=5)
        tk.Label(win,text="Локальный профиль этого компьютера. Не вводи здесь пароль Microsoft.",fg=MUTED,bg=BG,wraplength=310).pack(padx=18,pady=5)

    def refresh_account(self):
        if self.current_user:
            u=self.accounts.get_user(self.current_user['username']); self.current_user=u
            self.account_label.config(text=f"{u['username']}\n{u['rank']}\nИгровое время: {u['hours']:.1f} ч")
            self.account_action.pack_forget()
            self.logout_action.pack(fill="x", padx=20, pady=(0, 8))
        else:
            self.account_label.config(text="Не выполнен вход")
            self.logout_action.pack_forget()
            self.account_action.pack(fill="x", padx=20, pady=(0, 8))

    def logout(self):
        self.current_user = None
        self.config.pop("session_username", None)
        self.save_config()
        self.refresh_account()
        self.status.set("Вы вышли из аккаунта VibeCraft.")

    def exit_launcher(self):
        try:
            if self.game_process and self.game_process.poll() is None:
                if not messagebox.askyesno("Minecraft запущен", "Minecraft ещё работает. Закрыть только лаунчер?"):
                    return
        except Exception:
            pass
        self.root.destroy()

    def open_game_folder(self):
        MC_DIR.mkdir(parents=True, exist_ok=True)
        import subprocess, sys
        try:
            if sys.platform == "win32": os.startfile(str(MC_DIR))
            else: webbrowser.open(MC_DIR.as_uri())
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def launch_game(self):
        if mcl is None:
            messagebox.showerror("Нет зависимости", "Установи зависимости через install_dependencies.bat."); return
        if self.current_user is None:
            messagebox.showwarning("Нужен профиль", "Сначала войди или зарегистрируй локальный профиль VibeCraft."); self.account_dialog(); return
        selected_entry=self.version_var.get().strip()
        if not selected_entry or selected_entry.startswith("Загрузка"):
            messagebox.showwarning("Версия", "Сначала выбери версию Minecraft."); return
        try:
            version, selected_loader = [part.strip() for part in selected_entry.split("|", 1)]
        except ValueError:
            version, selected_loader = selected_entry, "Vanilla"
        if selected_loader not in ("Vanilla", "Forge", "Fabric"):
            messagebox.showerror("Версия", "Неизвестный вариант загрузчика."); return
        if self.game_process and self.game_process.poll() is None:
            messagebox.showinfo("Minecraft", "Игра уже запущена."); return
        user=self.current_user['username']
        if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", user):
            messagebox.showerror("Никнейм", "Для Minecraft нужен ник из 3–16 латинских букв, цифр или _. "); return
        self.status.set("Проверяю Minecraft. Если версии нет — она будет скачана автоматически…")
        def worker():
            try:
                MC_DIR.mkdir(parents=True,exist_ok=True)
                launch_id = version
                if selected_loader in ("Fabric", "Forge"):
                    # minecraft-launcher-lib 8.x объединяет загрузчики в mod_loader.
                    # Старые mcl.fabric / mcl.forge вызовы были устаревшими и
                    # давали несовместимость форматов версий Forge.
                    try:
                        loader_api = mcl.mod_loader.get_mod_loader(selected_loader.lower())
                    except Exception as exc:
                        raise RuntimeError(
                            f"Не удалось подключить загрузчик {selected_loader}. "
                            f"Проверь minecraft-launcher-lib 8.x: {exc}"
                        ) from exc

                    self.set_status(f"Устанавливаю {selected_loader} для Minecraft {version}…")
                    try:
                        launch_id = loader_api.install(version, str(MC_DIR))
                    except Exception as exc:
                        raise RuntimeError(
                            f"Установка {selected_loader} для Minecraft {version} не удалась. "
                            f"Возможно, этот загрузчик не поддерживает выбранную версию. Подробности: {exc}"
                        ) from exc

                    if not launch_id:
                        # Some library builds return None; resolve the installed profile.
                        installed_versions = mcl.utils.get_installed_versions(str(MC_DIR))
                        candidates = [
                            item.get("id") for item in installed_versions
                            if item.get("id") and version in item.get("id")
                            and selected_loader.lower() in item.get("id", "").lower()
                        ]
                        if not candidates:
                            raise RuntimeError(
                                f"{selected_loader} установщик завершился, но профиль не найден."
                            )
                        launch_id = candidates[0]
                installed_versions = mcl.utils.get_installed_versions(str(MC_DIR))
                if selected_loader == "Vanilla" and not any(item.get("id") == version for item in installed_versions):
                    self.set_status(f"Скачиваю Minecraft {version}…")
                    mcl.install.install_minecraft_version(version, str(MC_DIR))
                    installed_versions = mcl.utils.get_installed_versions(str(MC_DIR))
                    if not any(item.get("id") == version for item in installed_versions):
                        raise RuntimeError(f"Не удалось установить Minecraft {version}. Проверь подключение и журнал.")
                options={"username":user,"uuid":uuid.uuid3(uuid.NAMESPACE_DNS,"OfflinePlayer:"+user).hex,"token":""}
                command=mcl.command.get_minecraft_command(launch_id,str(MC_DIR),options=options)
                # Hide only the Java console. Do not pass SW_HIDE via STARTUPINFO:
                # it can make the actual Minecraft GUI window start hidden on Windows.
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
                self.game_process=subprocess.Popen(command,cwd=str(MC_DIR),creationflags=flags)
                self.root.after(0, self.root.iconify)
                self.set_status("Minecraft запущен. Лаунчер свёрнут.")
                started=time.monotonic()
                while self.game_process.poll() is None: time.sleep(5)
                elapsed=max(0,int(time.monotonic()-started))
                self.accounts.add_playtime(user,elapsed)
                self.root.after(0,self.refresh_account)
                self.set_status(f"Minecraft закрыт. Учтено игрового времени: {elapsed//60} мин.")
                self.root.after(0, self.root.deiconify)
            except Exception as e:
                self.set_status("Не удалось запустить игру: "+str(e))
                error_text = str(e)
                self.root.after(0,lambda msg=error_text:messagebox.showerror("Ошибка запуска",msg))
        threading.Thread(target=worker,daemon=True).start()

    def install_loader(self, loader):
        # Kept for compatibility with older UI integrations.
        version = self.version_var.get().strip()
        if " | " in version:
            version = version.split(" | ", 1)[0].strip()
        self._install_selected_loader(version, loader)

    def _install_selected_loader(self, version, loader):
        if mcl is None:
            messagebox.showerror("Зависимость", "Установи зависимости через install_dependencies.bat.")
            return
        def worker():
            try:
                if loader == "Fabric":
                    if not hasattr(mcl, "fabric"):
                        raise RuntimeError("Fabric API отсутствует в установленной minecraft-launcher-lib.")
                    mcl.fabric.install_fabric(version, str(MC_DIR))
                elif loader == "Forge":
                    if not hasattr(mcl, "forge"):
                        raise RuntimeError("Forge API отсутствует в установленной minecraft-launcher-lib.")
                    get_versions = getattr(mcl.forge, "list_forge_versions", None) or getattr(mcl.forge, "get_forge_versions", None)
                    if get_versions is None:
                        raise RuntimeError("В minecraft-launcher-lib нет функции получения версий Forge.")
                    forge_versions = get_versions(version)
                    if not forge_versions:
                        raise RuntimeError(f"Для Minecraft {version} Forge-сборки не найдены.")
                    selected = forge_versions[0]
                    forge_id = (selected.get("id") or selected.get("version")) if isinstance(selected, dict) else str(selected)
                    mcl.forge.install_forge_version(forge_id, str(MC_DIR))
                self.set_status(f"{loader} для Minecraft {version} установлен.")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Готово", f"{loader} для Minecraft {version} установлен. Обнови список версий."
                ))
            except Exception as e:
                error_text = str(e)
                self.set_status(f"Ошибка установки {loader}: {error_text}")
                self.root.after(0, lambda msg=error_text: messagebox.showerror(f"Установка {loader}", msg))
        self.status.set(f"Устанавливаю {loader} для Minecraft {version}…")
        threading.Thread(target=worker, daemon=True).start()

    def moderation_dialog(self):
        if not self.current_user:
            messagebox.showwarning("VibeCraft", "Сначала войди в локальный аккаунт."); return
        if self.current_user.get("role")!="owner":
            messagebox.showwarning("Нет доступа", "Выдавать и снимать роль модератора может только владелец VibeCraft."); return
        win=tk.Toplevel(self.root); win.title("Управление ролями VibeCraft"); win.geometry("380x260"); win.configure(bg=BG)
        tk.Label(win,text="УПРАВЛЕНИЕ РОЛЯМИ",font=("Segoe UI",14,"bold"),fg=WHITE,bg=BG).pack(pady=14)
        name=tk.Entry(win,width=34); name.pack(pady=8); name.insert(0,"Никнейм пользователя")
        action=tk.StringVar(value="moderator")
        ttk.Combobox(win,textvariable=action,state="readonly",values=("moderator","player"),width=28).pack(pady=8)
        def apply():
            try:
                self.accounts.set_special_role(self.current_user['username'],name.get().strip(),None if action.get()=="player" else "moderator")
                messagebox.showinfo("VibeCraft","Роль обновлена.",parent=win)
            except AccountError as e: messagebox.showerror("Ошибка",str(e),parent=win)
        tk.Button(win,text="Применить",command=apply,bg=PURPLE,fg=WHITE,relief="flat",padx=20,pady=8).pack(pady=10)
        tk.Label(win,text="Владелец не может быть назначен через эту форму. Администратор отсутствует.",fg=MUTED,bg=BG,wraplength=330).pack(pady=5)

    def auth_notice(self):
        messagebox.showinfo("Microsoft", "Microsoft OAuth пока не реализован. Не вводи пароль Microsoft в лаунчер. Сейчас доступен только локальный офлайн-профиль; он не даёт доступа к online-mode=true серверам и не подтверждает владение Minecraft Java Edition.")

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
        """Check GitHub Releases in the background. If a ZIP asset exists, offer to download and install it."""
        def worker():
            try:
                url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                req = urllib.request.Request(url, headers={"User-Agent": "VibeCraft-Launcher", "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    release = json.loads(response.read().decode("utf-8"))
                latest = str(release.get("tag_name", "")).strip().lstrip("vV")
                current = APP_VERSION.strip().lstrip("vV")
                if not latest or latest.lower() == current.lower():
                    return
                # Avoid showing an update prompt for older releases; compare numeric version parts when possible.
                def parts(value):
                    match = re.match(r"^(\d+(?:\.\d+)*)(?:[-+].*)?$", value)
                    return tuple(int(x) for x in match.group(1).split(".")) if match else None
                lp, cp = parts(latest), parts(current)
                if lp is not None and cp is not None:
                    size=max(len(lp),len(cp)); lp=lp+(0,)*(size-len(lp)); cp=cp+(0,)*(size-len(cp))
                    if lp <= cp:
                        return
                self.root.after(0, lambda r=release: self.offer_update(r))
            except Exception:
                # No internet, no releases, or private repo: don't prevent the launcher from starting.
                return
        threading.Thread(target=worker, daemon=True).start()

    def offer_update(self, release):
        tag = str(release.get("tag_name", "новая версия"))
        assets = release.get("assets", []) or []
        zip_assets = [a for a in assets if str(a.get("name", "")).lower().endswith(".zip") and a.get("browser_download_url")]
        notes = str(release.get("body", "") or "")[:700]
        if zip_assets:
            prompt = f"Доступно обновление VibeCraft {tag}.\n\n{notes}\n\nСкачать и установить обновление сейчас?\nАккаунты и настройки в пользовательской папке сохранятся."
            if messagebox.askyesno("Обновление VibeCraft", prompt):
                threading.Thread(target=self._download_and_install_update, args=(zip_assets[0], tag), daemon=True).start()
        else:
            prompt = f"Доступна версия {tag}, но в GitHub Release нет ZIP-файла для автоматической установки.\n\nОткрыть страницу релиза?"
            if messagebox.askyesno("Обновление VibeCraft", prompt):
                webbrowser.open(release.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"))

    def _download_and_install_update(self, asset, tag):
        try:
            self.root.after(0, lambda: self.status.set(f"Скачивание обновления {tag}…"))
            updates_dir = Path.home() / "VibeCraft" / "updates"
            updates_dir.mkdir(parents=True, exist_ok=True)
            archive = updates_dir / f"VibeCraft-{re.sub(r'[^A-Za-z0-9._-]', '_', tag)}.zip"
            req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "VibeCraft-Launcher"})
            with urllib.request.urlopen(req, timeout=30) as response, open(archive, "wb") as target:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    target.write(chunk)
            # Validate archive before offering it to the updater.
            import zipfile
            with zipfile.ZipFile(archive, "r") as zf:
                bad = zf.testzip()
                if bad:
                    raise ValueError(f"Повреждён ZIP-архив: {bad}")
                if not any(Path(n).name.lower() == "vibecraft.py" for n in zf.namelist()):
                    raise ValueError("В архиве обновления не найден vibecraft.py. Проверь ZIP в GitHub Releases.")
            helper = Path(__file__).with_name("vibecraft_updater.py")
            if not helper.exists():
                raise FileNotFoundError("Не найден файл vibecraft_updater.py")
            message = f"Обновление {tag} скачано. Лаунчер закроется, обновится и запустится снова."
            self.root.after(0, lambda m=message: messagebox.showinfo("VibeCraft", m))
            subprocess.Popen([sys.executable, str(helper), str(archive), str(Path(__file__).resolve().parent), str(os.getpid())],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), close_fds=True)
            self.root.after(100, self.root.destroy)
        except Exception as exc:
            details = str(exc)
            self.root.after(0, lambda d=details: messagebox.showerror("Не удалось обновить VibeCraft", d))
            self.root.after(0, lambda: self.status.set("Не удалось установить обновление."))

def _show_fatal_error(exc_type, exc_value, exc_tb):
    import traceback
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        root = tk._default_root
        if root is not None:
            win = tk.Toplevel(root)
            win.title("VibeCraft • Ошибка")
            win.geometry("720x440")
            win.configure(bg=BG)
            tk.Label(win, text="ВОЗНИКЛА ОШИБКА", font=("Segoe UI", 16, "bold"),
                     fg="#ff7185", bg=BG).pack(anchor="w", padx=18, pady=(16, 8))
            tk.Label(win, text=str(exc_value), fg=WHITE, bg=BG, wraplength=680,
                     justify="left").pack(anchor="w", padx=18, pady=5)
            box = tk.Text(win, bg="#0c0d1b", fg="#d9dcff", insertbackground=WHITE,
                          wrap="word", height=13)
            box.pack(fill="both", expand=True, padx=18, pady=8)
            box.insert("1.0", details)
            box.configure(state="disabled")
            def copy_error():
                win.clipboard_clear(); win.clipboard_append(details)
                messagebox.showinfo("VibeCraft", "Текст ошибки скопирован.", parent=win)
            tk.Button(win, text="СКОПИРОВАТЬ ОШИБКУ", command=copy_error,
                      bg=PURPLE, fg=WHITE, relief="flat", pady=8).pack(pady=(0, 14))
            return
    except Exception:
        pass
    try:
        from tkinter import messagebox as mb
        mb.showerror("VibeCraft • Ошибка", details)
    except Exception:
        print(details, file=sys.stderr)

if __name__ == "__main__":
    sys.excepthook = _show_fatal_error
    root = tk.Tk()
    def _tk_callback_error(exc_type, exc_value, exc_tb):
        _show_fatal_error(exc_type, exc_value, exc_tb)
    root.report_callback_exception = _tk_callback_error
    try:
        app = VibeCraft(root)
        root.mainloop()
    except Exception:
        _show_fatal_error(*sys.exc_info())
