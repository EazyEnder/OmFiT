import customtkinter
from tkinter import filedialog
import tkinter as tk
from view import ConsoleFrame
from view.TrackingFrame import TrackingFrame
from view.NormalizeFrame import NormalizeFrame
if __name__ == '__main__':
    from Main import OmniposeRun, BASE_DIR
from threading import Thread

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

class MainSettings(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.checkbox_1 = customtkinter.CTkCheckBox(self, text="Save masks")
        self.checkbox_1.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.checkbox_2 = customtkinter.CTkCheckBox(self, text="Save outlines")
        self.checkbox_2.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="w")
        
    def get(self):
        checked_checkboxes = [self.checkbox_1.get(),self.checkbox_2.get()]
        return checked_checkboxes
        

class OmniposeFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)

        self.run = None

        self.folder_path = BASE_DIR
        self.browse_label = customtkinter.CTkLabel(self, text="Path: "+self.folder_path)
        self.browse_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.browse_button = customtkinter.CTkButton(self, text="Set Data & Export path", command=self.browse_button)
        self.browse_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.settings = MainSettings(self)
        self.settings.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.button = customtkinter.CTkButton(self, text="Launch Omnipose", command=self.launchOmnipose)
        self.button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

    def launchOmnipose(self):
        settings = self.settings.get()
        run = OmniposeRun(saveMasks=settings[0]==1,saveOutlines=settings[1]==1)
        if(self.folder_path != "None"):
            run.basedir = self.folder_path
        Thread(target=run.run, args=[]).start() 
        self.run = run


    def browse_button(self):
        filename = filedialog.askdirectory()
        self.folder_path = filename
        self.browse_label.configure(text="Path: "+self.folder_path)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Omnipose Custom Tracker")
        self.geometry("1280x720")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.omnipose_frame = OmniposeFrame(self)
        self.omnipose_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.rowconfigure(1, weight=1)
        self.console_frame = ConsoleFrame.ConsoleOutput(self)
        self.console_frame.grid(row=1, column=0, padx=10, pady=(10, 10), sticky="nsew")

        self.tracking_frame = TrackingFrame(self)
        self.tracking_frame.grid(row=0,column=1, padx=10, pady=(10, 10), sticky="nsew")

        self.norm_frame = NormalizeFrame(self)
        self.norm_frame.grid(row=1,column=1, padx=10, pady=(10, 10), sticky="nsew")

import multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = App()
    app.mainloop()