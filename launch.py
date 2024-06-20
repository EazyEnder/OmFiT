"""
This is the Executable Script of the software. 
"""

if __name__ == '__main__':
    from Main import OmniposeRun

    run = OmniposeRun(custom_model="continuity1706_2000_3")
    run.run()
    run = OmniposeRun(custom_model="from01706_2000_l")
    run.run()
    run = OmniposeRun(custom_model="from01906_2000")
    run.run()


    #run.launchTracking(tracking=False,verifying=False)

#Make video using ffmpeg
#ffmpeg -framerate 20 -i export_%d.jpg -c:v libx264 -r 20 -pix_fmt yuv420p export.mp4