from google.cloud import vision
import re
from io import BytesIO
from PIL import Image


def detect_number(img: Image) -> int:
    """Detects text in the file."""

    client = vision.ImageAnnotatorClient()

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    content = img_byte_arr.getvalue()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("Texts:")

    for text in texts:
        print(f'\n"{text.description}"')
        if text.description:
            match = re.search(r"(\d+)", text.description)
            if match:
                return int(match.group(1))

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
