import customtkinter as ctk
from view.SliderWidget import SliderWidget
from threading import Thread

class TrackingFrame(ctk.CTkFrame):
    def __init__(self,master):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.title = ctk.CTkLabel(self, text="Cell Tracking", fg_color="gray30", corner_radius=6)
        self.title.grid(row=0,column=0, padx=10, pady=(10, 0), sticky="ew")

        self.slider = SliderWidget(self, from_=0, to=1, base_value=0.2, name="IOU Threshold")
        self.slider.grid(row=1,column=0, padx=10, pady=(10, 0), sticky="ew")

        self.launchbutton = ctk.CTkButton(self, text="Launch Tracking", command=self.launchTracking)
        self.launchbutton.grid(row=3, column=0, padx=10, pady=10, sticky="sew")

    def launchTracking(self):
        #settings = self.settings.get()
        if(self.master.omnipose_frame.run is None):
            print("ERROR: Cant track because Omnipose segmentation isnt done. Launch Omnipose first.")
            return
        
        Thread(target=self.master.omnipose_frame.run.launchTracking, args=[self.slider.get()]).start() 