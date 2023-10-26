# A really simple application example where we send webcam
# frames to Cornea's REST API. We are not using a database and
# we are just mapping the returned tags from the model to people's
# names.

import cv2
import requests

import base64

# Default display font for the output window.
DEFAULT_DISPLAY_FONT = cv2.FONT_HERSHEY_SIMPLEX
# Set this to the API URI you are using for your Cornea instance.
CORNEA_API_URI = "http://0.0.0.0:8000/model/detect_frame"

# Our array of people.
names = ["Person1", "Person2", "Person3"]


def main():
    # Create a webcam capture using OpenCV.
    cap = cv2.VideoCapture(0)
    # Set dimensions of the webcam.
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        # Read a frame from the capture.
        ret, img = cap.read()
        # Encode the incoming webcam image to JPG and then encode the image
        # to a base 64 bytestring.
        image = cv2.imencode('.jpg', img)[1]
        image_b64 = str(base64.b64encode(image), encoding='utf8')

        # Send request containing the encoded image to the API.
        res = requests.post(url=CORNEA_API_URI,
                            json={"frame": image_b64}).json()
        # Print returned JSON
        print(res)

        p = res["position"]
        # Create a blue rectangle around the detected face. The API will
        # return the face coordinates for the current frame before we show it
        # so we can use that as coordinate data.
        cv2.rectangle(
            img,
            (p["x"], p["y"]),
            ((p["x"] + p["w"]), (p["y"] + p["h"])),
            (255, 0, 0),
            2
        )

        if confidence := res["confidence"] > 0.5:
            # Confidence is returned between 0 and 1 so multiply by 100 and
            # round to get the percentage confidence value for this frame.
            confidence_str = f"{round(confidence * 100)}%"
            id_str = names[res["tag"] - 1]
        else:
            confidence_str = "???"
            id_str = "UNKNOWN"
        
        # Put text above the top left of the face.
        cv2.putText(
            img,
            str(id_str),
            (p["x"] + 5, p["y"] - 5),
            DEFAULT_DISPLAY_FONT,
            1,
            (255, 255, 255),
            2
        )

        # Put the confidence underneath the bottom left of the face.
        cv2.putText(
            img,
            str(confidence_str),
            (p["x"] + 5, p["y"] + p["h"] - 5),
            DEFAULT_DISPLAY_FONT,
            1,
            (255, 255, 0),
            1
        )

        # Show the current frame to the window and wait for CTRL-C
        cv2.imshow('camera', img)
        k = cv2.waitKey(10) & 0xff

        if k == 27:
            break


if __name__ == '__main__':
    main()
