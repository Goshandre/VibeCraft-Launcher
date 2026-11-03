import json, os, threading, webbrowser, urllib.request, urllib.error, subprocess, sys, uuid, time, re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

APP_NAME = "VibeCraft Launcher"
APP_VERSION = "2.2 Free Cosmetics Beta"
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
        self.root.geometry("880x600")
        self.root.minsize(760, 520)
        self.root.configure(bg=BG)
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
        loader_row=tk.Frame(left,bg=PANEL); loader_row.pack(fill="x",pady=(2,4))
        tk.Button(loader_row,text="Установить Fabric",command=lambda:self.install_loader("Fabric"),bg="#30335c",fg=WHITE,relief="flat",pady=7).pack(side="left",fill="x",expand=True,padx=(0,4))
        tk.Button(loader_row,text="Установить Forge",command=lambda:self.install_loader("Forge"),bg="#30335c",fg=WHITE,relief="flat",pady=7).pack(side="left",fill="x",expand=True,padx=(4,0))
        tk.Button(left, text="▶  ИГРАТЬ", command=self.launch_game,
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
        tk.Button(right, text="Выбрать плащ VibeCraft", command=self.choose_cape, bg="#493078", fg=WHITE, relief="flat", pady=8).pack(fill="x", padx=20, pady=(6, 0))
        tk.Button(right, text="✨ Эффекты и частицы", command=self.cosmetics_effects_dialog, bg="#30335c", fg=WHITE, relief="flat", pady=8).pack(fill="x", padx=20, pady=(6, 0))
        self.cosmetic_status = tk.Label(right, text="Косметика сохраняется локально", font=("Segoe UI", 8), fg="#d4c4ff", bg="#17182f", justify="left", wraplength=205)
        self.cosmetic_status.pack(anchor="w", padx=20, pady=(8, 0))
        tk.Label(right, text="Скины и плащи бесплатны. PNG сохраняются локально; для показа в игре нужен совместимый мод.",
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
        footer.pack(fill="x", padx=24, pady=(4, 10))
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
                error_text = str(e)
                self.root.after(0, lambda msg=error_text: messagebox.showerror("Ошибка установки", msg))
        threading.Thread(target=worker, daemon=True).start()

    def _choose_texture(self, kind, title):
        path = filedialog.askopenfilename(title=title, filetypes=[("PNG images", "*.png")])
        if not path: return
        try:
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

    def cosmetics_effects_dialog(self):
        """Save free cosmetic preferences; rendering requires a compatible game mod."""
        win = tk.Toplevel(self.root)
        win.title("VibeCraft — бесплатная косметика")
        win.geometry("430x430")
        win.configure(bg=BG)
        win.resizable(False, False)
        tk.Label(win, text="БЕСПЛАТНЫЕ ЭФФЕКТЫ", font=("Segoe UI", 15, "bold"), fg=WHITE, bg=BG).pack(pady=(18, 6))
        tk.Label(win, text="Настройки сохраняются в профиле VibeCraft.\nДля отображения в игре потребуется совместимый мод.",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG, justify="center").pack(pady=(0, 14))
        choices = [
            ("aura_enabled", "Аура вокруг персонажа"),
            ("footstep_particles", "Частицы при ходьбе"),
            ("jump_particles", "Частицы при прыжке"),
            ("join_effect", "Эффект появления"),
            ("color_effect", "Цветные эффекты"),
            ("extra_animations", "Дополнительные анимации"),
        ]
        vars_ = {}
        for key, title in choices:
            var = tk.BooleanVar(value=bool(self.config.get("cosmetics", {}).get(key, False)))
            vars_[key] = var
            tk.Checkbutton(win, text=title, variable=var, bg=BG, fg=WHITE, selectcolor=PANEL,
                           activebackground=BG, activeforeground=WHITE, font=("Segoe UI", 10)).pack(anchor="w", padx=48, pady=5)
        def save():
            self.config.setdefault("cosmetics", {}).update({key: var.get() for key, var in vars_.items()})
            self.save_config()
            self.cosmetic_status.config(text="Скин/плащ и настройки эффектов сохранены локально.\nИгровой мод пока не подключён.")
            self.status.set("Настройки бесплатной косметики сохранены.")
            messagebox.showinfo("VibeCraft", "Настройки сохранены. В этой Beta они ещё не отображаются в Minecraft: для этого нужен отдельный совместимый клиентский мод.", parent=win)
            win.destroy()
        tk.Button(win, text="СОХРАНИТЬ", command=save, bg=PURPLE, fg=WHITE, relief="flat", pady=9).pack(fill="x", padx=38, pady=20)

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
        version=self.version_var.get().strip()
        if not version or version.startswith("Загрузка"):
            messagebox.showwarning("Версия", "Сначала выбери версию Minecraft."); return
        if self.game_process and self.game_process.poll() is None:
            messagebox.showinfo("Minecraft", "Игра уже запущена."); return
        user=self.current_user['username']
        if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", user):
            messagebox.showerror("Никнейм", "Для Minecraft нужен ник из 3–16 латинских букв, цифр или _. "); return
        self.status.set("Проверяю Minecraft. Если версии нет — она будет скачана автоматически…")
        def worker():
            try:
                MC_DIR.mkdir(parents=True,exist_ok=True)
                if not mcl.utils.is_minecraft_version_installed(version, str(MC_DIR)):
                    self.set_status(f"Скачиваю Minecraft {version}…")
                    mcl.install.install_minecraft_version(version, str(MC_DIR))
                options={"username":user,"uuid":uuid.uuid3(uuid.NAMESPACE_DNS,"OfflinePlayer:"+user).hex,"token":""}
                command=mcl.command.get_minecraft_command(version,str(MC_DIR),options=options)
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
                startup = None
                if sys.platform == "win32":
                    startup = subprocess.STARTUPINFO()
                    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startup.wShowWindow = 0
                self.game_process=subprocess.Popen(command,cwd=str(MC_DIR),creationflags=flags,startupinfo=startup)
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
        if mcl is None: messagebox.showerror("Зависимость", "Установи зависимости."); return
        version=self.version_var.get().strip()
        def worker():
            try:
                if loader=="Fabric":
                    if not hasattr(mcl,"fabric"): raise RuntimeError("Эта версия minecraft-launcher-lib не содержит Fabric API.")
                    mcl.fabric.install_fabric(version,str(MC_DIR))
                elif loader=="Forge":
                    if not hasattr(mcl,"forge"): raise RuntimeError("Эта версия minecraft-launcher-lib не содержит Forge API.")
                    mcl.forge.install_forge_version(version,str(MC_DIR))
                self.set_status(f"{loader} для Minecraft {version} установлен.")
                self.root.after(0,lambda:messagebox.showinfo("Готово",f"{loader} установлен. Выбери созданный профиль загрузчика в списке версий."))
            except Exception as e:
                self.set_status(f"Ошибка установки {loader}: {e}")
                error_text = str(e)
                self.root.after(0,lambda msg=error_text:messagebox.showerror(f"Установка {loader}",msg))
        self.status.set(f"Устанавливаю {loader}…")
        threading.Thread(target=worker,daemon=True).start()

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
