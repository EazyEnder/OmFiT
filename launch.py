"""
This is the Executable Script of the software. 
"""

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Segment data using omnipose",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model", help="Base model")
    parser.add_argument("-cm", "--custom_model", default="continuity1706_2000_3", help="Custom model")
    args = parser.parse_args()
    config = vars(args)
    print(config)

    from Main import OmniposeRun

    model = config['model']
    if model is None:
        model = "bact_phase_omni"

    custom_model = config['custom_model']
    if not(custom_model is None):
        model = None

    #custom_model="continuity1706_2000_3"
    run = OmniposeRun(model=model,custom_model=custom_model)
    run.run()

    #run.launchTracking(tracking=False,verifying=False)

#Make video using ffmpeg
#ffmpeg -framerate 20 -i export_%d.jpg -c:v libx264 -r 20 -pix_fmt yuv420p export.mp4