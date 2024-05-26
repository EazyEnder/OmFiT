import sys
import customtkinter as ctk
import tkinter as tk
class ConsoleOutput(ctk.CTkFrame):
    def __init__(self,master):
        super().__init__(master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)
        self.grid_columnconfigure(0, weight=1)
        self.title = ctk.CTkLabel(self, text="Console Output", fg_color="gray30", corner_radius=6)
        self.title.grid(row=0,column=0, padx=10, pady=(10, 0), sticky="nsew")

        console_text = ctk.CTkTextbox(self, wrap=tk.WORD)
        console_text.grid(row=1,column=0, padx=10, pady=(10, 10), sticky="nsew")
        console_text.configure(scrollbar_button_color="", scrollbar_button_hover_color="")
        #font_spec = ("Cascadia Code", 12)  # Font family and size

        sys.stdout = self.ConsoleRedirector(console_text)
        sys.stderr = self.ConsoleRedirector(console_text)

    class ConsoleRedirector:
        def __init__(self, widget):
            self.widget = widget

        def write(self, text):
            self.widget.insert(tk.END, text+"\n")
            self.widget.see(tk.END)

        def flush(self):
            pass
        