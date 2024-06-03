"""
This is the Executable Script of the software. 
"""

if __name__ == '__main__':
    from Main import OmniposeRun

    run = OmniposeRun()
    run.run()
    run.launchTracking()

#Make video using ffmpeg
#ffmpeg -framerate 20 -i export_%d.jpg -c:v libx264 -r 20 -pix_fmt yuv420p export.mp4