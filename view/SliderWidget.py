import customtkinter as ctk
import numpy as np

class SliderWidget(ctk.CTkFrame):
    def __init__(self,master,name,from_=0,to=1,base_value=0.5):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=10)

        self.title = ctk.CTkLabel(self, text=name, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0,column=0, padx=10, pady=(10, 10), sticky="ew")

        self.value = base_value

        self.display_value = ctk.CTkLabel(self, text=str('{0:.2f}'.format(self.value)))
        self.display_value.grid(row=0,column=1, padx=10, pady=(10, 10), sticky="ew")

        def slider_listener(value):
            self.value = value
            self.display_value.configure(text=str('{0:.2f}'.format(self.value)))
        self.slider = ctk.CTkSlider(self, from_=from_, to=to, command=slider_listener)
        self.slider.grid(row=0,column=2, padx=10, pady=(10, 10), sticky="ew")
        self.slider.set(self.value)

    def get(self):
        return self.slider.get()