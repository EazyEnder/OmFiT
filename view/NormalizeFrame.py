import customtkinter as ctk
from threading import Thread
from tkinter import filedialog
import numpy as np
from pathlib import Path
from Main import  BASE_DIR
from train import normalizeImgs,normalizeMasks

class NormalizeFrame(ctk.CTkFrame):
    def __init__(self,master):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.title = ctk.CTkLabel(self, text="Normalize masks", fg_color="gray30", corner_radius=6)
        self.title.grid(row=0,column=0, padx=10, pady=(10, 0), sticky="ew")

        self.folder_path = BASE_DIR
        self.browse_label = ctk.CTkLabel(self, text="Path: "+self.folder_path)
        self.browse_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.browse_button = ctk.CTkButton(self, text="Set path", command=self.browse_button)
        self.browse_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.launchmasksbutton = ctk.CTkButton(self, text="Launch masks ", command=self.launch)
        self.launchmasksbutton.grid(row=2, column=0, padx=10, pady=10, sticky="sew")

        self.title = ctk.CTkLabel(self, text="Normalize raw files", fg_color="gray30", corner_radius=6)
        self.title.grid(row=0,column=1, padx=10, pady=(10, 0), sticky="ew")

        self.folder_path_raw = BASE_DIR
        self.browse_label_raw = ctk.CTkLabel(self, text="Path: "+self.folder_path)
        self.browse_label_raw.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.browse_button_raw = ctk.CTkButton(self, text="Set path", command=self.browse_button_raw)
        self.browse_button_raw.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.launchrawsbutton = ctk.CTkButton(self, text="Launch raws ", command=self.launch_raw)
        self.launchrawsbutton.grid(row=2, column=1, padx=10, pady=10, sticky="sew")

    def browse_button(self):
        filename = filedialog.askdirectory()
        self.folder_path = filename
        self.browse_label.configure(text="Path: "+self.folder_path)
    def browse_button_raw(self):
        filename = filedialog.askdirectory()
        self.folder_path_raw = filename
        self.browse_label_raw.configure(text="Path: "+self.folder_path_raw)

    def launch(self):
        files = np.array([str(p) for p in Path(self.folder_path).glob("*.tif")])
        Thread(target=normalizeMasks, args=[files]).start() 
    def launch_raw(self):
        files = np.array([str(p) for p in Path(self.folder_path_raw).glob("*.tif")])
        Thread(target=normalizeImgs, args=[files]).start() 