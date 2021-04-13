from queue import Queue
from cam_modules.uvctypes import *
import numpy as np
import cv2

class ThermalCamera:
    def __init__(self):

        self.BUF_SIZE = 2
        self.q = Queue(self.BUF_SIZE)
        self.PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(self.py_frame_callback)
        self.ctx = POINTER(uvc_context)()
        self.dev = POINTER(uvc_device)()
        self.devh = POINTER(uvc_device_handle)()
        self.ctrl = uvc_stream_ctrl()
        self.init_thermal_data_frames()

    def py_frame_callback(self, frame, userptr):

        array_pointer = cast(frame.contents.data, POINTER(c_uint16 * (frame.contents.width * frame.contents.height)))
        data = np.frombuffer(
            array_pointer.contents, dtype=np.dtype(np.uint16)
        ).reshape(
            frame.contents.height, frame.contents.width
        )
        if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
            return

        if not self.q.full():
            self.q.put(data)

    def init_thermal_data_frames(self):
        res = libuvc.uvc_init(byref(self.ctx), 0)
        if res < 0:
            print("uvc_init error")
            exit(1)

        try:
            res = libuvc.uvc_find_device(self.ctx, byref(self.dev), PT_USB_VID, PT_USB_PID, 0)
            if res < 0:
                print("uvc_find_device error")
                exit(1)

            try:
                res = libuvc.uvc_open(self.dev, byref(self.devh))
                if res < 0:
                    print("uvc_open error")
                    exit(1)

                print("device opened!")

                print_device_info(self.devh)
                print_device_formats(self.devh)
                set_manual_ffc(self.devh)
                frame_formats = uvc_get_frame_formats_by_guid(self.devh, VS_FMT_GUID_Y16)
                if len(frame_formats) == 0:
                    print("device does not support Y16")
                    exit(1)

                libuvc.uvc_get_stream_ctrl_format_size(self.devh, byref(self.ctrl), UVC_FRAME_FORMAT_Y16,
                                                       frame_formats[0].wWidth, frame_formats[0].wHeight,
                                                       int(1e7 / frame_formats[0].dwDefaultFrameInterval)
                                                       )

            except Exception as e:
                print("Error while opening camera")
                print(e)
                libuvc.uvc_unref_device(self.dev)
        except Exception as e:
            print("Error while opening camera")
            print(e)
            libuvc.uvc_exit(self.ctx)

    def read_thermal_data(self):
        res = libuvc.uvc_start_streaming(self.devh, byref(self.ctrl), self.PTR_PY_FRAME_CALLBACK, None, 0)
        if res < 0:
            print("uvc_start_streaming failed: {0}".format(res))
            exit(1)

        try:
            while True:
                data = self.q.get(True, 500)
                if data is not None:
                    yield data
        except Exception as e:
            print("Error while reading from camera")
            print(e)
        finally:
            print("______________STOPPED_____________________")
            libuvc.uvc_stop_streaming(self.devh)

    def raw_to_8bit(self, data):
        cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
        np.right_shift(data, 8, data)
        return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

    def performffc(self):
        perform_manual_ffc(self.devh)

    def print_shutter_info(self):
        print_shutter_info(self.devh)

    def setmanualffc(self):
        set_manual_ffc(self.devh)

    def setautoffc(self):
        set_auto_ffc(self.devh)