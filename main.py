from cam_modules.thermal_camera_init import *
from cam_modules.uvctypes import *
import cv2

#### To stream thermal cam frames

cam_source = ThermalCamera()

for thermal_frame in cam_source.read_thermal_data():
    print(thermal_frame.shape)

    radiometric_image = cam_source.raw_to_8bit(thermal_frame)

    cv2.imshow("radio metric image", radiometric_image)
    cv2.waitKey(10)

# TODO whenever it requires
# To set ffc manual mode
cam_source.setmanualffc()

# To set ffc auto mode
cam_source.setautoffc()

# to view device shutter info
cam_source.print_shutter_info()

# To perform ffc
cam_source.performffc()
