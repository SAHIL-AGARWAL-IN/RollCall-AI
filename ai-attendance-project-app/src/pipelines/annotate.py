from io import BytesIO

from PIL import ImageDraw, ImageFont, ImageOps

# Register colours: ink for a match, amber for a match worth checking, red for a face nobody matched
COLORS = {
    "match": (31, 58, 168),
    "weak": (180, 83, 9),
    "unknown": (198, 47, 55),
}


def draw_matches(img, faces, max_side=1400):
    """Draw a labelled box around each face and return the photo as JPEG bytes.

    faces: dicts with 'box' (left, top, right, bottom in img's pixels), 'label' and 'kind' (a COLORS key).
    """
    img = img.copy()
    scale = min(1.0, max_side / max(img.size))
    if scale < 1:
        img = img.resize((round(img.width * scale), round(img.height * scale)))

    draw = ImageDraw.Draw(img)
    line = max(3, round(max(img.size) / 300))
    pad = max(3, line * 2)
    fonts = {}

    for face in faces:
        color = COLORS[face['kind']]
        left, top, right, bottom = (round(v * scale) for v in face['box'])
        # dlib can report boxes that run past the edge of the photo
        left, top = max(0, left), max(0, top)
        right, bottom = min(img.width - 1, right), min(img.height - 1, bottom)
        draw.rectangle([left, top, right, bottom], outline=color, width=line)

        # Tags scale with the face so they stay readable on a phone without covering the next face
        size = max(14, min(round(max(img.size) / 32), round((bottom - top) * 0.45)))
        if size not in fonts:
            fonts[size] = ImageFont.load_default(size=size)
        font = fonts[size]
        text_left, text_top, text_right, text_bottom = draw.textbbox((0, 0), face['label'], font=font)
        tag_w = text_right - text_left + 2 * pad
        tag_h = text_bottom - text_top + 2 * pad
        # Name tag above the box, or below it when the face is at the top of the photo
        y = top - tag_h if top - tag_h >= 0 else min(bottom, img.height - tag_h)
        x = max(0, min(left, img.width - tag_w))
        draw.rectangle([x, y, x + tag_w, y + tag_h], fill=color)
        draw.text((x + pad - text_left, y + pad - text_top), face['label'], fill="white", font=font)

    out = BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


def crop_face(img, box, size=96):
    """A square close-up of one face, with some room around it, as JPEG bytes."""
    left, top, right, bottom = box
    half = max(right - left, bottom - top) * 0.85
    cx, cy = (left + right) / 2, (top + bottom) / 2
    region = (max(0, round(cx - half)), max(0, round(cy - half)),
              min(img.width, round(cx + half)), min(img.height, round(cy + half)))
    face = ImageOps.fit(img.crop(region), (size, size))
    out = BytesIO()
    face.save(out, format="JPEG", quality=85)
    return out.getvalue()
