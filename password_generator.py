# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import string
import secrets
import random
import json
import os

class ToolTip:
    def __init__(self, widget, text_callback, theme_manager):
        self.widget = widget
        self.text_callback = text_callback
        self.theme_manager = theme_manager
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        text = self.text_callback()
        if not text: return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        theme_colors = self.theme_manager.get_current_theme_colors()
        bg_color = theme_colors.get('TOOLTIP_BG', '#3a3f4b')
        fg_color = theme_colors.get('TOOLTIP_FG', '#abb2bf')

        label = tk.Label(self.tooltip_window, text=text, justify='left',
                         background=bg_color, foreground=fg_color, relief='solid', borderwidth=1,
                         font=("Segoe UI", 9, "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class PasswordGeneratorApp:
    COPY_ICON = "⎘"
    COPIED_ICON = "✓"
    GENERATE_ICON = "↻"
    CLEAR_ICON = "🗑️"
    HISTORY_ICON = "🕒"
    THEME_LIGHT_ICON = "☀️"
    THEME_DARK_ICON = "🌙"

    I18N = {
        'ar': {
            'window_title': "مولد كلمات السر الاحترافي", 'header': "مولد كلمات السر",
            'copy_tooltip': "نسخ إلى الحافظة", 'length_label': "طول كلمة المرور",
            'upper_label': "أحرف كبيرة (ABC)", 'lower_label': "أحرف صغيرة (abc)",
            'digits_label': "أرقام (123)", 'symbols_label': "رموز (@#$)",
            'strength_label': "قوة كلمة المرور: ", 'strength_weak': "ضعيفة",
            'strength_medium': "متوسطة", 'strength_strong': "قوية", 'strength_vstrong': "قوية جداً",
            'history_header': "سجل كلمات المرور", 'history_copy_tooltip': "نسخ كلمة المرور هذه",
            'clear_history_tooltip': "مسح سجل كلمات المرور", 'clear_confirm_title': "تأكيد المسح",
            'clear_confirm_message': "هل أنت متأكد أنك تريد مسح سجل كلمات المرور بشكل نهائي؟",
            'generate_button': "توليد كلمة مرور جديدة", 'generate_tooltip': "إنشاء كلمة مرور جديدة",
            'select_char_type': "اختر نوع أحرف واحد على الأقل", 'lang_button': "English",
            'theme_tooltip': "تبديل الوضع"
        },
        'en': {
            'window_title': "Professional Password Generator", 'header': "Password Generator",
            'copy_tooltip': "Copy to Clipboard", 'length_label': "Password Length",
            'upper_label': "Uppercase (ABC)", 'lower_label': "Lowercase (abc)",
            'digits_label': "Numbers (123)", 'symbols_label': "Symbols (@#$)",
            'strength_label': "Password Strength: ", 'strength_weak': "Weak",
            'strength_medium': "Medium", 'strength_strong': "Strong", 'strength_vstrong': "Very Strong",
            'history_header': "Password History", 'history_copy_tooltip': "Copy this password",
            'clear_history_tooltip': "Clear password history", 'clear_confirm_title': "Confirm Deletion",
            'clear_confirm_message': "Are you sure you want to permanently delete the password history?",
            'generate_button': "Generate New Password", 'generate_tooltip': "Create a new password",
            'select_char_type': "Select at least one character type", 'lang_button': "العربية",
            'theme_tooltip': "Toggle Theme"
        }
    }
    
    THEMES = {
        'dark': {
            'BG': "#1e1e1e", 'FRAME': "#252526", 'TEXT': "#cccccc", 'ACCENT': "#c586c0", 'ACCENT_ACTIVE': "#b570b0",
            'BORDER': "#3c3c3c", 'FLASH': "#3c3c3c", 'TOOLTIP_BG': '#3a3f4b', 'TOOLTIP_FG': '#abb2bf'
        },
        'light': {
            'BG': "#f5f5f5", 'FRAME': "#ffffff", 'TEXT': "#212121", 'ACCENT': "#007acc", 'ACCENT_ACTIVE': "#005f9e",
            'BORDER': "#dcdcdc", 'FLASH': "#e0e0e0", 'TOOLTIP_BG': '#ffffff', 'TOOLTIP_FG': '#212121'
        }
    }

    def __init__(self, root):
        self.root = root
        self.config_file = 'config.json'
        self.load_config()
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.apply_theme()
        self.update_ui_language()
        self.generate_password(add_to_history=False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f: config = json.load(f)
            self.current_lang = config.get('language', 'ar')
            self.current_theme = config.get('theme', 'dark')
            self.password_history = config.get('history', [])
            self.length_var = tk.IntVar(value=config.get('length', 18))
            self.include_upper = tk.BooleanVar(value=config.get('upper', True))
            self.include_lower = tk.BooleanVar(value=config.get('lower', True))
            self.include_digits = tk.BooleanVar(value=config.get('digits', True))
            self.include_symbols = tk.BooleanVar(value=config.get('symbols', True))
        except (FileNotFoundError, json.JSONDecodeError):
            self.current_lang, self.current_theme = 'ar', 'dark'
            self.password_history = []
            self.length_var = tk.IntVar(value=18)
            self.include_upper, self.include_lower, self.include_digits, self.include_symbols = (tk.BooleanVar(value=True) for _ in range(4))

    def save_config(self):
        config = {
            'language': self.current_lang, 'theme': self.current_theme,
            'length': self.length_var.get(), 'upper': self.include_upper.get(),
            'lower': self.include_lower.get(), 'digits': self.include_digits.get(),
            'symbols': self.include_symbols.get(), 'history': self.password_history
        }
        with open(self.config_file, 'w', encoding='utf-8') as f: json.dump(config, f, indent=4, ensure_ascii=False)

    def on_closing(self): self.save_config(); self.root.destroy()
    def setup_window(self): self.root.geometry("480x750"); self.root.resizable(False, False)
    def get_current_theme_colors(self): return self.THEMES[self.current_theme]

    def setup_styles(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.FONT_FAMILY = "Segoe UI"
        # FIX: Set initial theme color to avoid AttributeError before apply_theme is called
        colors = self.get_current_theme_colors()
        self.BG_COLOR = colors['BG']
        
    def apply_theme(self):
        colors = self.get_current_theme_colors()
        self.BG_COLOR = colors['BG'] # Update instance attribute
        BG, FRAME, TEXT, ACCENT, ACCENT_ACTIVE, BORDER, FLASH = colors['BG'], colors['FRAME'], colors['TEXT'], colors['ACCENT'], colors['ACCENT_ACTIVE'], colors['BORDER'], colors['FLASH']
        self.root.configure(bg=BG)
        self.style.configure('.', background=BG, foreground=TEXT, font=(self.FONT_FAMILY, 11), borderwidth=0)
        self.style.configure('TFrame', background=BG)
        self.style.configure('Card.TFrame', background=FRAME, relief='solid', borderwidth=1, bordercolor=BORDER)
        self.style.configure('Header.TLabel', font=(self.FONT_FAMILY, 18, 'bold'), background=BG)
        self.style.configure('Sub.TLabel', background=FRAME, font=(self.FONT_FAMILY, 12, 'bold'))
        self.style.configure('Result.TEntry', fieldbackground=BG, foreground=ACCENT, borderwidth=0, font=('Consolas', 16))
        self.style.configure('Flash.Result.TEntry', fieldbackground=FLASH, foreground=ACCENT, borderwidth=0, font=('Consolas', 16))
        self.style.configure('Action.TButton', background=FRAME, foreground=TEXT, font=(self.FONT_FAMILY, 16))
        self.style.map('Action.TButton', background=[('active', BG)])
        self.style.configure('Generate.TButton', font=(self.FONT_FAMILY, 14, 'bold'), background=ACCENT, foreground="#ffffff", padding=15)
        self.style.map('Generate.TButton', background=[('active', ACCENT_ACTIVE)])
        self.style.configure('Options.TCheckbutton', background=FRAME, font=(self.FONT_FAMILY, 11), padding=(5, 10))
        self.style.map('Options.TCheckbutton', indicatorcolor=[('selected', ACCENT)])
        self.style.configure("Horizontal.TScale", background=FRAME)
        self.style.configure('History.TLabel', background=FRAME, foreground=TEXT, font=('Consolas', 11))
        self.style.configure('HistoryCopy.TButton', background=FRAME, foreground=TEXT, font=(self.FONT_FAMILY, 10), padding=2)
        self.style.map('HistoryCopy.TButton', background=[('active', BG)])
        self.style.configure('Lang.TButton', font=(self.FONT_FAMILY, 9), padding=5, background=FRAME, foreground=TEXT)
        self.style.map('Lang.TButton', background=[('active', BG)])
        self.style.configure('TSeparator', background=BORDER)
        self.style.configure("Vertical.TScrollbar", troughcolor=BG, bordercolor=BG, background=FRAME, arrowcolor=TEXT)
        self.style.map("Vertical.TScrollbar", background=[('active', ACCENT_ACTIVE)])
        
        self.theme_button.config(text=self.THEME_LIGHT_ICON if self.current_theme == 'dark' else self.THEME_DARK_ICON)
        if hasattr(self, 'history_canvas'): self.history_canvas.config(bg=FRAME)
        if hasattr(self, 'history_header'): self.history_header.configure(background=BG)

    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="25"); self.main_frame.pack(expand=True, fill='both')
        
        # Bottom frame for the generate button (fixed at the bottom)
        bottom_frame = ttk.Frame(self.main_frame); bottom_frame.pack(side='bottom', fill='x', pady=(15, 0))
        self.generate_button = ttk.Button(bottom_frame, command=self.generate_password, style='Generate.TButton'); self.generate_button.pack(fill='x')
        self.generate_tooltip = ToolTip(self.generate_button, lambda: self.I18N[self.current_lang]['generate_tooltip'], self)

        # Content frame for everything else
        content_frame = ttk.Frame(self.main_frame); content_frame.pack(fill='both', expand=True)

        # Header
        top_header_frame = ttk.Frame(content_frame); top_header_frame.pack(fill='x', pady=(0, 15))
        self.lang_button = ttk.Button(top_header_frame, command=self.toggle_language, style='Lang.TButton')
        self.theme_button = ttk.Button(top_header_frame, command=self.toggle_theme, style='Lang.TButton')
        self.header_label = ttk.Label(top_header_frame, style='Header.TLabel', anchor='center')
        ToolTip(self.theme_button, lambda: self.I18N[self.current_lang]['theme_tooltip'], self)
        
        # Result
        self.result_frame = ttk.Frame(content_frame, style='Card.TFrame', padding=8); self.result_frame.pack(fill='x', pady=10)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.result_frame, textvariable=self.password_var, style='Result.TEntry', state='readonly', justify='center')
        self.copy_button = ttk.Button(self.result_frame, text=self.COPY_ICON, style='Action.TButton', command=self.copy_to_clipboard, width=3)
        self.copy_tooltip = ToolTip(self.copy_button, lambda: self.I18N[self.current_lang]['copy_tooltip'], self)
        
        # Options
        self.options_container = ttk.Frame(content_frame, padding="20", style='Card.TFrame'); self.options_container.pack(fill='x', pady=10)
        self.length_frame = ttk.Frame(self.options_container, style='Card.TFrame'); self.length_frame.pack(fill='x', pady=(0, 5))
        self.length_title_label = ttk.Label(self.length_frame, style='Sub.TLabel')
        self.length_display_var = tk.StringVar()
        self.length_value_label = ttk.Label(self.length_frame, textvariable=self.length_display_var, style='Sub.TLabel')
        self.length_slider = ttk.Scale(self.options_container, from_=8, to=32, orient='horizontal', variable=self.length_var, command=self.update_length_label)
        self.length_slider.pack(fill='x', pady=(5, 20))
        self.chk_upper = ttk.Checkbutton(self.options_container, style='Options.TCheckbutton', variable=self.include_upper, command=self.on_option_change)
        self.chk_lower = ttk.Checkbutton(self.options_container, style='Options.TCheckbutton', variable=self.include_lower, command=self.on_option_change)
        self.chk_digits = ttk.Checkbutton(self.options_container, style='Options.TCheckbutton', variable=self.include_digits, command=self.on_option_change)
        self.chk_symbols = ttk.Checkbutton(self.options_container, style='Options.TCheckbutton', variable=self.include_symbols, command=self.on_option_change)
        
        # Strength
        self.strength_label = ttk.Label(content_frame, font=(self.FONT_FAMILY, 10), anchor='center'); self.strength_label.pack(fill='x', pady=(15, 5))
        self.strength_canvas = tk.Canvas(content_frame, height=6, highlightthickness=0, relief='flat'); self.strength_canvas.pack(fill='x', pady=(0, 10))
        
        # History
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=10)
        history_header_frame = ttk.Frame(content_frame); history_header_frame.pack(fill='x', pady=(5, 5))
        self.history_header = ttk.Label(history_header_frame, style='Sub.TLabel', background=self.BG_COLOR)
        self.clear_history_button = ttk.Button(history_header_frame, text=self.CLEAR_ICON, style='HistoryCopy.TButton', command=self.clear_history)
        self.clear_history_tooltip = ToolTip(self.clear_history_button, lambda: self.I18N[self.current_lang]['clear_history_tooltip'], self)
        history_container = ttk.Frame(content_frame, style='Card.TFrame'); history_container.pack(fill='both', expand=True, pady=(0, 0))
        self.history_canvas = tk.Canvas(history_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_canvas.yview)
        self.scrollable_history_frame = ttk.Frame(self.history_canvas, style='Card.TFrame')
        self.scrollable_history_frame.bind("<Configure>", lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))
        self.history_canvas.create_window((0, 0), window=self.scrollable_history_frame, anchor="nw")
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        self.history_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    def toggle_language(self): self.current_lang = 'en' if self.current_lang == 'ar' else 'ar'; self.update_ui_language()
    def toggle_theme(self): self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'; self.apply_theme(); self.update_ui_language()

    def update_ui_language(self):
        lang = self.I18N[self.current_lang]
        colors = self.get_current_theme_colors()
        self.root.title(lang['window_title'])
        self.lang_button.config(text=lang['lang_button'])
        self.header_label.config(text=lang['header'])
        self.length_title_label.config(text=lang['length_label'])
        self.length_value_label.config(foreground=colors['ACCENT'])
        self.chk_upper.config(text=lang['upper_label'])
        self.chk_lower.config(text=lang['lower_label'])
        self.chk_digits.config(text=lang['digits_label'])
        self.chk_symbols.config(text=lang['symbols_label'])
        self.history_header.config(text=f"{self.HISTORY_ICON} {lang['history_header']}")
        self.generate_button.config(text=f"{lang['generate_button']} {self.GENERATE_ICON}")
        self.update_strength_indicator(self.length_var.get(), self.get_types_score())
        self.update_history_display()
        is_rtl = self.current_lang == 'ar'
        for w in [self.lang_button, self.theme_button, self.header_label, self.copy_button, self.password_entry, self.length_value_label, self.length_title_label, self.history_header, self.clear_history_button]: w.pack_forget()
        for chk in [self.chk_upper, self.chk_lower, self.chk_digits, self.chk_symbols]: chk.pack_forget()
        if is_rtl:
            self.lang_button.pack(side='left', anchor='n', padx=(0, 5)); self.theme_button.pack(side='left', anchor='n')
            self.header_label.pack(side='right', expand=True, fill='x')
            self.copy_button.pack(side='left', padx=(0, 8)); self.password_entry.pack(side='right', fill='x', expand=True, ipady=10, padx=(8, 0))
            self.length_value_label.pack(side='left'); self.length_title_label.pack(side='right')
            for chk in [self.chk_upper, self.chk_lower, self.chk_digits, self.chk_symbols]: chk.pack(anchor='e')
            self.clear_history_button.pack(side='left', padx=5); self.history_header.pack(side='right', expand=True, fill='x')
        else:
            self.lang_button.pack(side='right', anchor='n', padx=(5, 0)); self.theme_button.pack(side='right', anchor='n')
            self.header_label.pack(side='left', expand=True, fill='x')
            self.password_entry.pack(side='left', fill='x', expand=True, ipady=10, padx=(8, 0)); self.copy_button.pack(side='right', padx=(8, 0))
            self.length_title_label.pack(side='left'); self.length_value_label.pack(side='right')
            for chk in [self.chk_upper, self.chk_lower, self.chk_digits, self.chk_symbols]: chk.pack(anchor='w')
            self.history_header.pack(side='left', expand=True, fill='x'); self.clear_history_button.pack(side='right', padx=5)

    def on_option_change(self): self.generate_password(add_to_history=False)
    
    def update_length_label(self, value):
        self.length_display_var.set(str(int(float(value))))
        self.generate_password(add_to_history=False)
        
    def get_types_score(self): return sum([self.include_upper.get(), self.include_lower.get(), self.include_digits.get(), self.include_symbols.get()])

    def generate_password(self, add_to_history=True):
        current_pass = self.password_var.get()
        if add_to_history and current_pass and self.I18N['ar']['select_char_type'] not in current_pass and self.I18N['en']['select_char_type'] not in current_pass:
            if len(self.password_history) >= 10: self.password_history.pop(0)
            if current_pass not in self.password_history: self.password_history.append(current_pass)
            self.update_history_display()
        length = self.length_var.get()
        pool, guaranteed = [], []
        options = {self.include_upper.get(): string.ascii_uppercase, self.include_lower.get(): string.ascii_lowercase, self.include_digits.get(): string.digits, self.include_symbols.get(): "!@#$%^&*()_+-=[]{}|;:'\",.<>/?"}
        for enabled, charset in options.items():
            if enabled: pool.extend(charset); guaranteed.append(secrets.choice(charset))
        if not pool:
            self.password_var.set(self.I18N[self.current_lang]['select_char_type'])
            self.update_strength_indicator(length, 0)
            return
        rem_len = length - len(guaranteed)
        password_list = guaranteed + [secrets.choice(pool) for _ in range(rem_len if rem_len > 0 else 0)]
        random.shuffle(password_list)
        self.password_var.set("".join(password_list))
        self.update_strength_indicator(length, self.get_types_score())
        self.password_entry.config(style='Flash.Result.TEntry')
        self.root.after(150, lambda: self.password_entry.config(style='Result.TEntry'))

    def clear_history(self):
        lang = self.I18N[self.current_lang]
        if messagebox.askyesno(lang['clear_confirm_title'], lang['clear_confirm_message']):
            self.password_history.clear()
            self.update_history_display()

    def update_history_display(self):
        for w in self.scrollable_history_frame.winfo_children(): w.destroy()
        is_rtl = self.current_lang == 'ar'
        for p in reversed(self.password_history):
            item = ttk.Frame(self.scrollable_history_frame, style='Card.TFrame')
            item.pack(fill='x', pady=2, padx=2)
            lbl = ttk.Label(item, text=p, style='History.TLabel')
            btn = ttk.Button(item, text=self.COPY_ICON, style='HistoryCopy.TButton', command=lambda p_copy=p: self.copy_to_clipboard(p_copy))
            ToolTip(btn, lambda: self.I18N[self.current_lang]['history_copy_tooltip'], self)
            if is_rtl: btn.pack(side='left', padx=5); lbl.pack(side='right', padx=5, expand=True, fill='x')
            else: lbl.pack(side='left', padx=5, expand=True, fill='x'); btn.pack(side='right', padx=5)

    def update_strength_indicator(self, length, types_score):
        self.strength_canvas.delete("all")
        score = types_score + (2 if length >= 16 else 1 if length >= 12 else 0)
        lang = self.I18N[self.current_lang]
        colors = self.THEMES[self.current_theme]
        strength_colors = {"weak": "#e06c75", "medium": "#d19a66", "strong": "#98c379", "vstrong": colors['ACCENT']}
        text, color, width_pct = lang['strength_weak'], strength_colors["weak"], 0.25
        if score >= 5: text, color, width_pct = lang['strength_vstrong'], strength_colors["vstrong"], 1.0
        elif score >= 4: text, color, width_pct = lang['strength_strong'], strength_colors["strong"], 0.75
        elif score >= 3: text, color, width_pct = lang['strength_medium'], strength_colors["medium"], 0.5
        self.strength_label.config(text=lang['strength_label'] + text)
        w = self.strength_canvas.winfo_width()
        self.strength_canvas.config(bg=colors['FRAME'])
        self.strength_canvas.create_rectangle(0, 0, (w if w > 1 else 400) * width_pct, 6, fill=color, outline="")

    def copy_to_clipboard(self, password_to_copy=None):
        is_main = password_to_copy is None
        if is_main: password_to_copy = self.password_var.get()
        if password_to_copy and self.I18N['ar']['select_char_type'] not in password_to_copy and self.I18N['en']['select_char_type'] not in password_to_copy:
            self.root.clipboard_clear()
            self.root.clipboard_append(password_to_copy)
            if is_main: self.copy_button.config(text=self.COPIED_ICON); self.root.after(1500, lambda: self.copy_button.config(text=self.COPY_ICON))

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()
