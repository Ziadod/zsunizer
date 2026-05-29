import math
import random
import threading
import zipfile
import hashlib
from tkinter import filedialog
import customtkinter as Ctk
import osrparse
from osrparse import Replay

Ctk.set_appearance_mode("Dark")
Ctk.set_default_color_theme("blue")

class ToolTip:
    def __init__(self, Widget, Text):
        self.Widget = Widget
        self.Text = Text
        self.TooltipWindow = None
        self.Id = None
        self.Widget.bind("<Enter>", self.Enter)
        self.Widget.bind("<Leave>", self.Leave)

    def Enter(self, Event=None):
        self.Schedule()

    def Leave(self, Event=None):
        self.Unschedule()
        self.Hide()

    def Schedule(self):
        self.Unschedule()
        self.Id = self.Widget.after(300, self.Show)

    def Unschedule(self):
        if self.Id:
            self.Widget.after_cancel(self.Id)
            self.Id = None

    def Show(self):
        if self.TooltipWindow:
            return
        X = self.Widget.winfo_rootx() + 15
        Y = self.Widget.winfo_rooty() + self.Widget.winfo_height() + 10
        self.TooltipWindow = Tw = Ctk.CTkToplevel(self.Widget)
        Tw.wm_overrideredirect(True)
        Tw.wm_geometry(f"+{X}+{Y}")
        Tw.attributes("-topmost", True)
        Label = Ctk.CTkLabel(Tw, text=self.Text, fg_color="#2b2b2b", corner_radius=4, padx=8, pady=4, text_color="#e5e5e5", font=Ctk.CTkFont(size=11))
        Label.pack()

    def Hide(self):
        if self.TooltipWindow:
            self.TooltipWindow.destroy()
            self.TooltipWindow = None

class ZsunizerApp(Ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("zsu!nizer - Replay Humanizer & Editor")
        self.geometry("850x680")
        self.resizable(False, False)

        self.ReplayData = None
        self.HitObjects = []
        self.InputFilepath = ""
        self.InputFilename = ""

        FontTitle = Ctk.CTkFont(size=28, weight="bold")
        FontHeader = Ctk.CTkFont(size=16, weight="bold")
        FontBold = Ctk.CTkFont(weight="bold")
        FontLog = Ctk.CTkFont(family="Consolas", size=11)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.HeaderFrame = Ctk.CTkFrame(self, fg_color="transparent")
        self.HeaderFrame.grid(row=0, column=0, columnspan=2, pady=(15, 5), sticky="ew")

        self.TitleLabel = Ctk.CTkLabel(self.HeaderFrame, text="zsu!nizer", font=FontTitle)
        self.TitleLabel.pack()
        self.SubtitleLabel = Ctk.CTkLabel(self.HeaderFrame, text="osu! Replay Humanizer & Editor", text_color="gray")
        self.SubtitleLabel.pack()

        self.LeftPanel = Ctk.CTkFrame(self, corner_radius=10)
        self.LeftPanel.grid(row=1, column=0, padx=(15, 7.5), pady=15, sticky="nsew")

        self.RightPanel = Ctk.CTkFrame(self, corner_radius=10)
        self.RightPanel.grid(row=1, column=1, padx=(7.5, 15), pady=15, sticky="nsew")

        self.ProjectLabel = Ctk.CTkLabel(self.LeftPanel, text="Project Files", font=FontHeader)
        self.ProjectLabel.pack(pady=(15, 10))

        self.SelectBtn = Ctk.CTkButton(self.LeftPanel, text="Load Replay (.osr)", command=self.SelectFile, height=32)
        self.SelectBtn.pack(pady=(0, 5), padx=20, fill="x")
        self.FileLabel = Ctk.CTkLabel(self.LeftPanel, text="No Replay Loaded", font=FontBold, text_color="#e06c75")
        self.FileLabel.pack(pady=(0, 10))

        self.BeatmapBtn = Ctk.CTkButton(self.LeftPanel, text="Load Beatmap (.osu / .osz)", command=self.LoadBeatmap, height=32, state="disabled")
        self.BeatmapBtn.pack(pady=(0, 5), padx=20, fill="x")

        self.BeatmapLabel = Ctk.CTkLabel(self.LeftPanel, text="Optional: Enhances slider logic", font=Ctk.CTkFont(size=11))
        self.BeatmapLabel.pack(pady=(0, 2))

        self.WarningLabel = Ctk.CTkLabel(self.LeftPanel, text="", text_color="#e06c75", font=Ctk.CTkFont(size=11, weight="bold"))
        self.WarningLabel.pack(pady=(0, 10))

        self.NameFrame = Ctk.CTkFrame(self.LeftPanel, fg_color="transparent")
        self.NameFrame.pack(pady=(0, 15), padx=20, fill="x")
        self.NameLabel = Ctk.CTkLabel(self.NameFrame, text="Player Name:")
        self.NameLabel.pack(side="left", padx=(0, 10))
        self.NameEntry = Ctk.CTkEntry(self.NameFrame)
        self.NameEntry.pack(side="left", fill="x", expand=True)

        self.ParamsLabel = Ctk.CTkLabel(self.LeftPanel, text="Humanize Parameters", font=FontHeader)
        self.ParamsLabel.pack(pady=(10, 15))

        self.SlidersFrame = Ctk.CTkFrame(self.LeftPanel, fg_color="transparent")
        self.SlidersFrame.pack(fill="x", padx=20)

        self.DriftLabel = Ctk.CTkLabel(self.SlidersFrame, text="Sloppy Aim (Drift): 2.0")
        self.DriftLabel.pack()
        self.DriftSlider = Ctk.CTkSlider(self.SlidersFrame, from_=0.0, to=10.0, command=lambda V: self.DriftLabel.configure(text=f"Sloppy Aim (Drift): {V:.1f}"))
        self.DriftSlider.set(2.0)
        self.DriftSlider.pack(pady=(0, 15), fill="x")

        self.ShakeLabel = Ctk.CTkLabel(self.SlidersFrame, text="Hand Shake (Tremor): 1.5")
        self.ShakeLabel.pack()
        self.ShakeSlider = Ctk.CTkSlider(self.SlidersFrame, from_=0.0, to=10.0, command=lambda V: self.ShakeLabel.configure(text=f"Hand Shake (Tremor): {V:.1f}"))
        self.ShakeSlider.set(1.5)
        self.ShakeSlider.pack(pady=(0, 15), fill="x")

        self.IdleLabel = Ctk.CTkLabel(self.SlidersFrame, text="Idle Wandering (Key Up): 3.0")
        self.IdleLabel.pack()
        self.IdleSlider = Ctk.CTkSlider(self.SlidersFrame, from_=0.0, to=10.0, command=lambda V: self.IdleLabel.configure(text=f"Idle Wandering (Key Up): {V:.1f}"))
        self.IdleSlider.set(3.0)
        self.IdleSlider.pack(pady=(0, 15), fill="x")

        self.LazyLabel = Ctk.CTkLabel(self.SlidersFrame, text="Lazy Tracking (Slider Cheese): 5.0")
        self.LazyLabel.pack()
        self.LazySlider = Ctk.CTkSlider(self.SlidersFrame, from_=0.0, to=10.0, command=lambda V: self.LazyLabel.configure(text=f"Lazy Tracking (Slider Cheese): {V:.1f}"))
        self.LazySlider.set(5.0)
        self.LazySlider.pack(fill="x")

        self.ModsHeader = Ctk.CTkLabel(self.RightPanel, text="Modifiers", font=FontHeader)
        self.ModsHeader.pack(pady=(15, 10))

        self.ModsGrid = Ctk.CTkFrame(self.RightPanel, fg_color="transparent")
        self.ModsGrid.pack(pady=(0, 20))

        self.ModStates = {}
        self.ModButtons = {}
        self.ModTooltips = {}

        ModLayout = [
            ["EZ", "NF", "HT", "", ""],
            ["HR", "SD", "DT", "HD", "FL"],
            ["RX", "AP", "SO", "", ""]
        ]

        self.ModMap = {
            "NF": 1, "EZ": 2, "HD": 8, "HR": 16, "SD": 32, "DT": 64,
            "RX": 128, "HT": 256, "NC": 512, "FL": 1024, "SO": 4096, "AP": 8192, "PF": 16384
        }
        self.ModNamesFull = {
            "EZ": "Easy", "NF": "No Fail", "HT": "Half Time",
            "HR": "Hard Rock", "SD": "Sudden Death", "PF": "Perfect", "DT": "Double Time",
            "NC": "Nightcore", "HD": "Hidden", "FL": "Flashlight", "RX": "Relax",
            "AP": "Autopilot", "SO": "Spun Out"
        }

        for RIdx, Row in enumerate(ModLayout):
            for CIdx, ModName in enumerate(Row):
                if ModName:
                    self.ModStates[ModName] = 0
                    Btn = Ctk.CTkButton(self.ModsGrid, text=ModName, width=50, height=32,
                                        fg_color="transparent", border_width=1, border_color="#555555",
                                        hover_color="#333333", text_color="#aaaaaa",
                                        command=lambda M=ModName: self.ToggleMod(M))
                    Btn.grid(row=RIdx, column=CIdx, padx=5, pady=5)
                    self.ModButtons[ModName] = Btn
                    TooltipObj = ToolTip(Btn, self.ModNamesFull.get(ModName, ModName))
                    self.ModTooltips[ModName] = TooltipObj

        self.ActionsHeader = Ctk.CTkLabel(self.RightPanel, text="Render Output", font=FontHeader)
        self.ActionsHeader.pack(pady=(0, 10))

        self.ActionFrame = Ctk.CTkFrame(self.RightPanel, fg_color="transparent")
        self.ActionFrame.pack(fill="x", padx=20, pady=(0, 15))

        self.ConvertBtn = Ctk.CTkButton(self.ActionFrame, text="Convert & Save", command=self.StartConversion, height=36)
        self.ConvertBtn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.CancelBtn = Ctk.CTkButton(self.ActionFrame, text="Reset", command=self.ResetUi, height=36)
        self.CancelBtn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.LogContainer = Ctk.CTkFrame(self.RightPanel, fg_color="transparent")
        self.LogContainer.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.LogBox = Ctk.CTkTextbox(self.LogContainer, font=FontLog)
        self.LogBox.pack(fill="both", expand=True, pady=(0, 5))

        self.LogBox.tag_config("SYSTEM", foreground="#abb2bf")
        self.LogBox.tag_config("PROCESS", foreground="#56b6c2")
        self.LogBox.tag_config("SUCCESS", foreground="#98c379")
        self.LogBox.tag_config("ERROR", foreground="#e06c75")

        self.LogBox.insert("0.0", "[SYSTEM] Ready. Please load a replay file.\n", "SYSTEM")
        self.LogBox.configure(state="disabled")

        self.ClearBtn = Ctk.CTkButton(self.LogContainer, text="Clear Console", command=self.ClearLogs, height=24, font=Ctk.CTkFont(size=11), fg_color="transparent", border_width=1, border_color="#555555", text_color="#aaaaaa", hover_color="#333333")
        self.ClearBtn.pack(anchor="e")

        self.SetUIState("Startup")

    def SafeLog(self, Message, Tag="SYSTEM"):
        self.after(0, lambda: self.Log(Message, Tag))

    def Log(self, Message, Tag="SYSTEM"):
        self.LogBox.configure(state="normal")
        self.LogBox.insert("end", Message + "\n", Tag)
        self.LogBox.see("end")
        self.LogBox.configure(state="disabled")

    def SetUIState(self, Mode):
        IsActive = (Mode == "Ready")
        MainActive = (Mode in ["Startup", "Ready"])

        UiState = "normal" if IsActive else "disabled"
        MainState = "normal" if MainActive else "disabled"

        DimText = "#555555"
        ActiveText = "#DCE4EE"
        DimBtnBg = "#262626"
        
        self.ParamsLabel.configure(text_color=ActiveText if IsActive else DimText)
        self.ModsHeader.configure(text_color=ActiveText if IsActive else DimText)
        self.ActionsHeader.configure(text_color=ActiveText if IsActive else DimText)

        self.NameLabel.configure(text_color=ActiveText if IsActive else DimText)
        self.DriftLabel.configure(text_color=ActiveText if IsActive else DimText)
        self.ShakeLabel.configure(text_color=ActiveText if IsActive else DimText)
        self.IdleLabel.configure(text_color=ActiveText if IsActive else DimText)
        self.LazyLabel.configure(text_color=ActiveText if IsActive else DimText)
        self.BeatmapLabel.configure(text_color="gray" if IsActive else DimText)

        self.SelectBtn.configure(state=MainState)
        self.NameEntry.configure(state=UiState)
        self.DriftSlider.configure(state=UiState)
        self.ShakeSlider.configure(state=UiState)
        self.IdleSlider.configure(state=UiState)
        self.LazySlider.configure(state=UiState)

        if IsActive:
            self.BeatmapBtn.configure(state="normal", fg_color="#444444", text_color=ActiveText)
            self.ConvertBtn.configure(state="normal", fg_color="#1f538d", text_color=ActiveText)
            self.CancelBtn.configure(state="normal", fg_color="#e06c75", text_color=ActiveText)
        else:
            self.BeatmapBtn.configure(state="disabled", fg_color=DimBtnBg, text_color=DimText)
            self.ConvertBtn.configure(state="disabled", fg_color=DimBtnBg, text_color=DimText)
            self.CancelBtn.configure(state="disabled", fg_color=DimBtnBg, text_color=DimText)

        for ModName, Btn in self.ModButtons.items():
            Btn.configure(state=UiState)
            if Mode == "Startup":
                Btn.configure(fg_color="transparent", border_color="#333333", text_color=DimText)
            elif Mode == "Ready":
                self.SetModState(ModName, self.ModStates[ModName])

    def SetModState(self, ModName, State):
        self.ModStates[ModName] = State
        Btn = self.ModButtons[ModName]

        if State == 0:
            Btn.configure(fg_color="transparent", text=ModName, border_color="#555555", text_color="#aaaaaa", hover_color="#333333")
        elif State == 1:
            Btn.configure(fg_color="#1f538d", text=ModName, border_color="#1f538d", text_color="white", hover_color="#14375e")
        elif State == 2:
            AltName = "PF" if ModName == "SD" else "NC"
            Btn.configure(fg_color="#8A2BE2", text=AltName, border_color="#8A2BE2", text_color="white", hover_color="#6A1B9A")

        CurrentBtnText = Btn.cget("text")
        self.ModTooltips[ModName].Text = self.ModNamesFull.get(CurrentBtnText, CurrentBtnText)

    def ToggleMod(self, ModName):
        State = self.ModStates[ModName]
        if ModName in ["SD", "DT"]:
            NewState = (State + 1) % 3
        else:
            NewState = (State + 1) % 2
        self.SetModState(ModName, NewState)

        if NewState > 0:
            if ModName == "EZ": self.SetModState("HR", 0)
            elif ModName == "HR": self.SetModState("EZ", 0)
            elif ModName == "HT": self.SetModState("DT", 0)
            elif ModName == "DT": self.SetModState("HT", 0)
            elif ModName == "RX": self.SetModState("AP", 0)
            elif ModName == "AP": self.SetModState("RX", 0)

    def ClearLogs(self):
        self.LogBox.configure(state="normal")
        self.LogBox.delete("0.0", "end")
        self.LogBox.configure(state="disabled")

    def LoadBeatmap(self):
        Filepath = filedialog.askopenfilename(filetypes=[("osu! Beatmap", "*.osu *.osz")])
        if not Filepath:
            return

        try:
            Lines = []
            if Filepath.endswith('.osz'):
                if not self.ReplayData:
                    self.Log("[ERROR] Load a replay first to match the correct difficulty from the .osz!", "ERROR")
                    return

                with zipfile.ZipFile(Filepath, 'r') as Z:
                    Found = False
                    for Filename in Z.namelist():
                        if Filename.endswith('.osu'):
                            Content = Z.read(Filename)
                            FileHash = hashlib.md5(Content).hexdigest()
                            if FileHash == self.ReplayData.beatmap_hash:
                                Lines = Content.decode('utf-8', errors='ignore').splitlines()
                                Found = True
                                break
                    if not Found:
                        self.Log("[ERROR] Matching difficulty not found in the .osz file.", "ERROR")
                        self.WarningLabel.configure(text="⚠️ Error: Beatmap does not match Replay Hash!", text_color="#e06c75")
                        return
            else:
                with open(Filepath, 'r', encoding='utf-8', errors='ignore') as F:
                    Lines = F.readlines()

            InHitobjects = False
            self.HitObjects = []

            for Line in Lines:
                Line = Line.strip()
                if Line == "[HitObjects]":
                    InHitobjects = True
                    continue
                if InHitobjects and Line:
                    Parts = Line.split(',')
                    if len(Parts) >= 5:
                        TimeMs = int(Parts[2])
                        TypeFlag = int(Parts[3])

                        ObjType = "circle"
                        if TypeFlag & 2: ObjType = "slider"
                        elif TypeFlag & 8: ObjType = "spinner"

                        self.HitObjects.append({'time': TimeMs, 'type': ObjType})

            if self.HitObjects:
                self.HitObjects.sort(key=lambda X: X['time'])
                self.Log(f"[FILE] Beatmap attached: {len(self.HitObjects)} objects parsed.", "SYSTEM")

                NameShort = Filepath.split('/')[-1]
                if len(NameShort) > 30: NameShort = NameShort[:27] + "..."
                self.BeatmapLabel.configure(text=f"Loaded: {NameShort}", text_color="#98c379")
                self.WarningLabel.configure(text="(Note: Map must match the replay)", text_color="#e5c07b")
            else:
                self.HitObjects = []
                self.Log("[ERROR] No readable hit objects found.", "ERROR")

        except Exception as E:
            self.HitObjects = []
            self.Log(f"[ERROR] Failed to parse beatmap: {str(E)}", "ERROR")

    def SelectFile(self):
        Filepath = filedialog.askopenfilename(filetypes=[("osu! Replay", "*.osr")])
        if not Filepath:
            self.Log("[SYSTEM] File selection cancelled.", "SYSTEM")
            return

        self.InputFilepath = Filepath
        self.InputFilename = Filepath.split("/")[-1]
        self.HitObjects = []

        try:
            self.ReplayData = Replay.from_path(self.InputFilepath)
        except Exception as E:
            self.Log(f"[ERROR] Could not load replay: {str(E)}", "ERROR")
            return

        NameShort = self.InputFilename
        if len(NameShort) > 25: NameShort = NameShort[:22] + "..."

        self.FileLabel.configure(text=NameShort, text_color="#98c379")
        self.SelectBtn.configure(text="Change Replay (.osr)")
        
        self.BeatmapLabel.configure(text="Optional: Enhances slider logic", text_color="gray")
        self.WarningLabel.configure(text="")

        self.SetUIState("Ready")

        self.NameEntry.delete(0, "end")
        self.NameEntry.insert(0, self.ReplayData.username)

        for M in self.ModStates: self.SetModState(M, 0)

        CurrentMods = getattr(self.ReplayData.mods, "value", self.ReplayData.mods)
        if not isinstance(CurrentMods, int):
            try: CurrentMods = int(CurrentMods)
            except ValueError: CurrentMods = 0

        if (CurrentMods & self.ModMap["PF"]) == self.ModMap["PF"]: self.SetModState("SD", 2)
        elif (CurrentMods & self.ModMap["SD"]) == self.ModMap["SD"]: self.SetModState("SD", 1)
        if (CurrentMods & self.ModMap["NC"]) == self.ModMap["NC"]: self.SetModState("DT", 2)
        elif (CurrentMods & self.ModMap["DT"]) == self.ModMap["DT"]: self.SetModState("DT", 1)

        for ModName in ["EZ", "NF", "HT", "HR", "HD", "FL", "RX", "AP", "SO"]:
            if (CurrentMods & self.ModMap[ModName]) == self.ModMap[ModName]:
                self.SetModState(ModName, 1)

        self.Log(f"[FILE] Loaded: {self.InputFilename}", "SYSTEM")

    def StartConversion(self):
        self.SetUIState("Processing")
        self.Log("[SYSTEM] Preparing to convert file...", "SYSTEM")

        self.ReplayData.username = self.NameEntry.get()
        NewMods = 0
        for ModName, State in self.ModStates.items():
            if State == 1:
                NewMods |= self.ModMap[ModName]
            elif State == 2:
                if ModName == "SD": NewMods |= (self.ModMap["SD"] | self.ModMap["PF"])
                elif ModName == "DT": NewMods |= (self.ModMap["DT"] | self.ModMap["NC"])

        if hasattr(osrparse, 'Mod'):
            try: self.ReplayData.mods = osrparse.Mod(NewMods)
            except ValueError: self.ReplayData.mods = NewMods
        else:
            self.ReplayData.mods = NewMods

        threading.Thread(target=self.ProcessReplay, daemon=True).start()

    def ProcessReplay(self):
        try:
            self.SafeLog("[PROCESS] Applying humanized movement...", "PROCESS")

            DriftVal = self.DriftSlider.get()
            ShakeVal = self.ShakeSlider.get()
            IdleVal = self.IdleSlider.get()
            LazyVal = self.LazySlider.get() / 10.0

            RawData = self.ReplayData.replay_data

            CurrentTime = 0
            TargetDriftX, TargetDriftY = 0.0, 0.0
            CurrentDriftX, CurrentDriftY = 0.0, 0.0
            FramesModified = 0

            LazyX, LazyY = None, None

            ObjIdx = 0
            TotalObjs = len(self.HitObjects)
            CurrentObjType = None

            for I, Event in enumerate(RawData):
                IsTuple = isinstance(Event, (list, tuple))
                Td = Event[0] if IsTuple else Event.time_delta
                Ex = Event[1] if IsTuple else Event.x
                Ey = Event[2] if IsTuple else Event.y
                Ek = Event[3] if IsTuple else Event.keys

                if LazyX is None:
                    LazyX, LazyY = Ex, Ey

                CurrentTime += Td

                if TotalObjs > 0:
                    while ObjIdx < TotalObjs - 1 and CurrentTime >= self.HitObjects[ObjIdx + 1]['time'] - 150:
                        ObjIdx += 1
                    CurrentObjType = self.HitObjects[ObjIdx]['type']

                if Td > 0:
                    IsSlider = False
                    if Ek > 0:
                        if TotalObjs > 0:
                            IsSlider = (CurrentObjType == "slider")
                        else:
                            IsSlider = True

                    if IsSlider:
                        Alpha = max(0.05, min(1.0, 1.0 - (LazyVal * 0.85)))
                        LazyX += (Ex - LazyX) * Alpha
                        LazyY += (Ey - LazyY) * Alpha

                        Dist = math.hypot(Ex - LazyX, Ey - LazyY)
                        MaxDist = LazyVal * 35.0
                        if Dist > MaxDist and Dist > 0:
                            Ratio = MaxDist / Dist
                            LazyX = Ex - (Ex - LazyX) * Ratio
                            LazyY = Ey - (Ey - LazyY) * Ratio

                        Ex, Ey = LazyX, LazyY
                    else:
                        LazyX, LazyY = Ex, Ey

                    if random.random() < 0.05:
                        TargetDriftX = random.uniform(-DriftVal * 2.0, DriftVal * 2.0)
                        TargetDriftY = random.uniform(-DriftVal * 2.0, DriftVal * 2.0)

                    CurrentDriftX += (TargetDriftX - CurrentDriftX) * 0.1
                    CurrentDriftY += (TargetDriftY - CurrentDriftY) * 0.1

                    TSec = CurrentTime / 1000.0
                    ShakeX = (math.sin(TSec * 11) + math.cos(TSec * 17)) * (ShakeVal * 0.8)
                    ShakeY = (math.cos(TSec * 13) + math.sin(TSec * 19)) * (ShakeVal * 0.8)

                    IdleX, IdleY = 0.0, 0.0
                    if Ek == 0:
                        IdleX = math.sin(TSec * 2.5) * IdleVal * 3.0
                        IdleY = math.sin(TSec * 3.1) * IdleVal * 3.0

                    Ex += CurrentDriftX + ShakeX + IdleX
                    Ey += CurrentDriftY + ShakeY + IdleY
                    FramesModified += 1

                if IsTuple:
                    if isinstance(Event, list):
                        Event[1] = Ex
                        Event[2] = Ey
                    else:
                        RawData[I] = (Td, Ex, Ey, Ek)
                else:
                    Event.x = Ex
                    Event.y = Ey

            self.SafeLog(f"[SUCCESS] {FramesModified} frames humanized!", "SUCCESS")
            self.after(0, self.ExportFile)

        except Exception as E:
            self.SafeLog(f"[ERROR] {str(E)}", "ERROR")
            self.after(0, lambda: self.SetUIState("Ready"))

    def ExportFile(self):
        DefaultName = "Humanized_" + self.InputFilename
        Filepath = filedialog.asksaveasfilename(defaultextension=".osr", filetypes=[("osu! Replay", "*.osr")], initialfile=DefaultName)

        if Filepath:
            try:
                self.Log("[PROCESS] Saving modified replay to disk...", "PROCESS")
                self.ReplayData.write_path(Filepath)
                self.Log(f"[SUCCESS] Exported: {Filepath.split('/')[-1]}", "SUCCESS")
                self.SetUIState("Ready")
            except Exception as E:
                self.Log(f"[ERROR] Export failed: {str(E)}", "ERROR")
                self.SetUIState("Ready")
        else:
            self.Log("[SYSTEM] Save cancelled.", "SYSTEM")
            self.SetUIState("Ready")

    def ResetUi(self):
        self.ReplayData = None
        self.InputFilepath = ""
        self.InputFilename = ""
        self.HitObjects = []

        self.FileLabel.configure(text="No Replay Loaded", text_color="#e06c75")
        self.SelectBtn.configure(text="Load Replay (.osr)")

        self.BeatmapLabel.configure(text="Optional: Enhances slider logic", text_color="gray")
        self.WarningLabel.configure(text="")

        self.NameEntry.delete(0, "end")

        for M in self.ModStates:
            self.SetModState(M, 0)

        self.DriftSlider.set(2.0)
        self.DriftLabel.configure(text="Sloppy Aim (Drift): 2.0")
        self.ShakeSlider.set(1.5)
        self.ShakeLabel.configure(text="Hand Shake (Tremor): 1.5")
        self.IdleSlider.set(3.0)
        self.IdleLabel.configure(text="Idle Wandering (Key Up): 3.0")
        self.LazySlider.set(5.0)
        self.LazyLabel.configure(text="Lazy Tracking (Slider Cheese): 5.0")

        self.Log("[SYSTEM] Application reset to default state.", "SYSTEM")
        self.SetUIState("Startup")

if __name__ == "__main__":
    App = ZsunizerApp()
    App.mainloop()