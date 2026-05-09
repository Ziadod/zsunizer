import math
import random
import time
import threading
from tkinter import filedialog
import customtkinter as ctk
import osrparse
from osrparse import Replay

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ZsunizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("zsu!nizer - Replay Humanizer & Editor")
        self.geometry("480x400")
        self.resizable(False, False)
        
        self.replay_data = None
        self.input_filepath = ""
        self.input_filename = ""

        font_title = ctk.CTkFont(size=28, weight="bold")
        font_bold = ctk.CTkFont(weight="bold")
        font_log = ctk.CTkFont(family="Consolas", size=11)

        self.title_label = ctk.CTkLabel(self, text="zsu!nizer", font=font_title)
        self.title_label.pack(pady=(20, 0))
        
        self.subtitle_label = ctk.CTkLabel(self, text="osu! Replay Humanizer & Editor", text_color="gray")
        self.subtitle_label.pack(pady=(0, 2))

        self.log_container = ctk.CTkFrame(self, fg_color="transparent")
        self.log_container.pack(side="bottom", pady=(0, 15), fill="x")

        self.dynamic_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dynamic_frame.pack(fill="both", expand=True)

        self.select_btn = ctk.CTkButton(self.dynamic_frame, text="Select .osr File", command=self.select_file, width=200, height=40)
        self.select_btn.pack(pady=30)

        self.file_label = ctk.CTkLabel(self.dynamic_frame, text="", font=font_bold)
        
        self.settings_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        
        self.name_label = ctk.CTkLabel(self.settings_frame, text="Player Name:")
        self.name_entry = ctk.CTkEntry(self.settings_frame, width=220)
        
        self.mods_label = ctk.CTkLabel(self.settings_frame, text="Mods:", font=font_bold)
        self.mods_grid = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        
        self.mod_states = {}
        self.mod_buttons = {}
        
        mod_layout = [
            ["EZ", "NF", "HT", "", ""],
            ["HR", "SD", "DT", "HD", "FL"],
            ["RX", "AP", "SO", "", ""]
        ]
        
        self.mod_map = {
            "NF": 1, "EZ": 2, "HD": 8, "HR": 16, "SD": 32, "DT": 64,
            "RX": 128, "HT": 256, "NC": 512, "FL": 1024, "SO": 4096, "AP": 8192, "PF": 16384
        }
        
        for r_idx, row in enumerate(mod_layout):
            for c_idx, mod_name in enumerate(row):
                if mod_name:
                    self.mod_states[mod_name] = 0
                    btn = ctk.CTkButton(self.mods_grid, text=mod_name, width=55, height=28,
                                        fg_color="transparent", border_width=1, border_color="#555555",
                                        hover_color="#333333", text_color="#aaaaaa",
                                        command=lambda m=mod_name: self.toggle_mod(m))
                    btn.grid(row=r_idx, column=c_idx, padx=7, pady=6, sticky="w")
                    self.mod_buttons[mod_name] = btn
        
        self.slider_label = ctk.CTkLabel(self.dynamic_frame, text="Humanize Amount: 5.0", font=font_bold)
        self.intensity_slider = ctk.CTkSlider(self.dynamic_frame, from_=0.5, to=10.0, command=self.update_slider_label, width=250)
        self.intensity_slider.set(5.0)
        
        self.info_label = ctk.CTkLabel(self.dynamic_frame, text="Higher values increase cursor sway, edge hits, and overall human error.", font=ctk.CTkFont(size=11), text_color="#444444")

        self.action_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        self.convert_btn = ctk.CTkButton(self.action_frame, text="Convert & Save", command=self.start_conversion, width=150, height=35)
        self.cancel_btn = ctk.CTkButton(self.action_frame, text="Cancel", command=self.cancel_action, width=100, height=35, fg_color="#e06c75", hover_color="#be5046")

        self.log_box = ctk.CTkTextbox(self.log_container, width=430, height=110, font=font_log)
        self.log_box.pack(pady=(0, 5))
        
        self.log_box.tag_config("SYSTEM", foreground="#abb2bf")
        self.log_box.tag_config("PROCESS", foreground="#56b6c2")
        self.log_box.tag_config("SUCCESS", foreground="#98c379")
        self.log_box.tag_config("ERROR", foreground="#e06c75")

        self.log_box.insert("0.0", "[SYSTEM] Ready. Please select a replay file.\n", "SYSTEM")
        self.log_box.configure(state="disabled")

        self.clear_btn = ctk.CTkButton(self.log_container, text="Clear Logs", command=self.clear_logs, width=90, height=24, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1, border_color="#555555", text_color="#aaaaaa", hover_color="#333333")
        self.clear_btn.pack(anchor="e", padx=25)

    def set_mod_state(self, mod_name, state):
        self.mod_states[mod_name] = state
        btn = self.mod_buttons[mod_name]

        if state == 0:
            btn.configure(fg_color="transparent", text=mod_name, border_color="#555555", text_color="#aaaaaa", hover_color="#333333")
        elif state == 1:
            btn.configure(fg_color="#1f538d", text=mod_name, border_color="#1f538d", text_color="white", hover_color="#14375e")
        elif state == 2:
            alt_name = "PF" if mod_name == "SD" else "NC"
            btn.configure(fg_color="#8A2BE2", text=alt_name, border_color="#8A2BE2", text_color="white", hover_color="#6A1B9A")

    def toggle_mod(self, mod_name):
        state = self.mod_states[mod_name]
        
        if mod_name in ["SD", "DT"]:
            new_state = (state + 1) % 3
        else:
            new_state = (state + 1) % 2

        self.set_mod_state(mod_name, new_state)

        if new_state > 0:
            if mod_name == "EZ": self.set_mod_state("HR", 0)
            elif mod_name == "HR": self.set_mod_state("EZ", 0)
            elif mod_name == "HT": self.set_mod_state("DT", 0)
            elif mod_name == "DT": self.set_mod_state("HT", 0)
            elif mod_name == "RX": self.set_mod_state("AP", 0)
            elif mod_name == "AP": self.set_mod_state("RX", 0)

    def log(self, message, tag="SYSTEM"):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n", tag)
        self.log_box.see("end") 
        self.log_box.configure(state="disabled")

    def clear_logs(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        self.log_box.configure(state="disabled")

    def update_slider_label(self, value):
        self.slider_label.configure(text=f"Humanize Amount: {value:.1f}")

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("osu! Replay", "*.osr")])
        if not filepath:
            self.log("[SYSTEM] File selection cancelled.", "SYSTEM")
            return
            
        self.input_filepath = filepath
        self.input_filename = filepath.split("/")[-1]
        
        try:
            self.replay_data = Replay.from_path(self.input_filepath)
        except Exception as e:
            self.log(f"[ERROR] Could not load replay: {str(e)}", "ERROR")
            return

        self.select_btn.pack_forget()
        self.geometry("480x720")
        
        self.file_label.configure(text=self.input_filename)
        
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.replay_data.username)
        
        for m in self.mod_states:
            self.set_mod_state(m, 0)
            
        current_mods = getattr(self.replay_data.mods, "value", self.replay_data.mods)
        if not isinstance(current_mods, int):
            try:
                current_mods = int(current_mods)
            except ValueError:
                current_mods = 0
                
        if (current_mods & self.mod_map["PF"]) == self.mod_map["PF"]:
            self.set_mod_state("SD", 2)
        elif (current_mods & self.mod_map["SD"]) == self.mod_map["SD"]:
            self.set_mod_state("SD", 1)

        if (current_mods & self.mod_map["NC"]) == self.mod_map["NC"]:
            self.set_mod_state("DT", 2)
        elif (current_mods & self.mod_map["DT"]) == self.mod_map["DT"]:
            self.set_mod_state("DT", 1)

        for mod_name in ["EZ", "NF", "HT", "HR", "HD", "FL", "RX", "AP", "SO"]:
            if (current_mods & self.mod_map[mod_name]) == self.mod_map[mod_name]:
                self.set_mod_state(mod_name, 1)
        
        self.file_label.pack(pady=(15, 5))
        
        self.settings_frame.pack(pady=5)
        self.name_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.mods_label.grid(row=1, column=0, columnspan=2, pady=(15, 0))
        self.mods_grid.grid(row=2, column=0, columnspan=2, pady=5)
        
        self.slider_label.pack(pady=(15, 0))
        self.intensity_slider.pack(pady=5)
        self.info_label.pack(pady=(0, 10))
        
        self.action_frame.pack(pady=10)
        self.convert_btn.grid(row=0, column=0, padx=10)
        self.cancel_btn.grid(row=0, column=1, padx=10)
        
        self.log(f"[FILE] Loaded: {self.input_filename}", "SYSTEM")

    def start_conversion(self):
        self.convert_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.intensity_slider.configure(state="disabled")
        self.name_entry.configure(state="disabled")
        
        self.log("[SYSTEM] Preparing to convert file...", "SYSTEM")
        
        self.replay_data.username = self.name_entry.get()
        
        new_mods = 0
        for mod_name, state in self.mod_states.items():
            if state == 1:
                new_mods |= self.mod_map[mod_name]
            elif state == 2:
                if mod_name == "SD":
                    new_mods |= (self.mod_map["SD"] | self.mod_map["PF"])
                elif mod_name == "DT":
                    new_mods |= (self.mod_map["DT"] | self.mod_map["NC"])
                
        if hasattr(osrparse, 'Mod'):
            try:
                self.replay_data.mods = osrparse.Mod(new_mods)
            except ValueError:
                self.replay_data.mods = new_mods
        else:
            self.replay_data.mods = new_mods
            
        threading.Thread(target=self.process_replay, daemon=True).start()

    def process_replay(self):
        try:
            self.log("[PROCESS] Applying edits and injecting human movement...", "PROCESS")
            time.sleep(0.5) 
            
            intensity = self.intensity_slider.get()
            raw_data = self.replay_data.replay_data
            
            current_time = 0
            target_drift_x, target_drift_y = 0.0, 0.0
            current_drift_x, current_drift_y = 0.0, 0.0
            frames_modified = 0
            
            for i, event in enumerate(raw_data):
                is_tuple = isinstance(event, (list, tuple))
                
                td = event[0] if is_tuple else event.time_delta
                ex = event[1] if is_tuple else event.x
                ey = event[2] if is_tuple else event.y
                ek = event[3] if is_tuple else event.keys
                
                current_time += td
                
                if td > 0:
                    if random.random() < 0.08:
                        target_drift_x = random.uniform(-intensity * 1.8, intensity * 1.8)
                        target_drift_y = random.uniform(-intensity * 1.8, intensity * 1.8)
                    
                    current_drift_x += (target_drift_x - current_drift_x) * 0.15
                    current_drift_y += (target_drift_y - current_drift_y) * 0.15
                    
                    spin_x, spin_y = 0.0, 0.0
                    if ek == 0:
                        phase = current_time / 120.0
                        spin_mag = intensity * 2.5
                        spin_x = math.sin(phase) * spin_mag
                        spin_y = math.cos(phase) * spin_mag
                    
                    jitter_x = random.uniform(-intensity * 0.4, intensity * 0.4)
                    jitter_y = random.uniform(-intensity * 0.4, intensity * 0.4)
                    
                    ex += current_drift_x + spin_x + jitter_x
                    ey += current_drift_y + spin_y + jitter_y
                    frames_modified += 1
                
                if is_tuple:
                    if isinstance(event, list):
                        event[1], event[2] = ex, ey
                    else:
                        raw_data[i] = (td, ex, ey, ek)
                else:
                    event.x = ex
                    event.y = ey
            
            time.sleep(0.5) 
            self.log(f"[SUCCESS] Edits applied and {frames_modified} frames humanized!", "SUCCESS")
            
            self.after(0, self.export_file)

        except Exception as e:
            self.log(f"[ERROR] {str(e)}", "ERROR")
            self.after(0, self.reset_buttons)

    def reset_buttons(self):
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="normal")
        self.intensity_slider.configure(state="normal")
        self.name_entry.configure(state="normal")

    def export_file(self):
        default_name = "Modified_" + self.input_filename
        filepath = filedialog.asksaveasfilename(defaultextension=".osr", filetypes=[("osu! Replay", "*.osr")], initialfile=default_name)
        
        if filepath:
            try:
                self.log("[PROCESS] Saving modified replay to disk...", "PROCESS")
                self.replay_data.write_path(filepath)
                self.log(f"[SUCCESS] Exported: {filepath.split('/')[-1]}", "SUCCESS")
                self.reset_ui()
            except Exception as e:
                self.log(f"[ERROR] Export failed: {str(e)}", "ERROR")
                self.reset_buttons()
        else:
            self.log("[SYSTEM] Save cancelled.", "SYSTEM")
            self.reset_buttons()

    def cancel_action(self):
        self.log("[SYSTEM] Action cancelled. Reverting to file selection.", "SYSTEM")
        self.reset_ui()

    def reset_ui(self):
        self.replay_data = None
        self.input_filepath = ""
        self.input_filename = ""
        
        self.file_label.pack_forget()
        self.settings_frame.pack_forget()
        self.slider_label.pack_forget()
        self.intensity_slider.pack_forget()
        self.info_label.pack_forget()
        self.action_frame.pack_forget()
        self.convert_btn.grid_forget()
        self.cancel_btn.grid_forget()
        
        self.geometry("480x400")
        self.select_btn.pack(pady=40)
        
        self.reset_buttons()

if __name__ == "__main__":
    app = ZsunizerApp()
    app.mainloop()