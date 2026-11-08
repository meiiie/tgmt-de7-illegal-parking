"""Raster exports of the geometric Curb mark, matching web/public/curb.svg."""
from pathlib import Path
from PIL import Image, ImageDraw


def export_brand(destination: Path):
    scale = 4
    image = Image.new("RGBA", (256 * scale, 256 * scale))
    draw = ImageDraw.Draw(image)
    def box(points):
        return tuple(value * scale for value in points)
    draw.rounded_rectangle(box((0, 0, 256, 256)), radius=58 * scale, fill="#ed592e")
    draw.arc(box((64, 64, 126, 126)), 180, 270, fill="white", width=18 * scale)
    draw.arc(box((64, 130, 126, 192)), 90, 180, fill="white", width=18 * scale)
    draw.line(box((95, 73, 192, 73)), fill="white", width=18 * scale)
    draw.line(box((73, 95, 73, 161)), fill="white", width=18 * scale)
    draw.line(box((95, 183, 192, 183)), fill="white", width=18 * scale)
    for x, y in ((192, 73), (192, 183)):
        draw.ellipse(box((x-9, y-9, x+9, y+9)), fill="white")
    for y in (78, 146):
        draw.rounded_rectangle(box((123, y-7, 137, y+39)), radius=7 * scale, fill="white")
    image = image.resize((256, 256), Image.Resampling.LANCZOS)
    image.save(destination / "curb.png")
    image.save(destination / "curb.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    small = Image.new("RGB", (64,64), "white")
    mark = image.resize((52,52), Image.Resampling.LANCZOS)
    small.paste(mark, (6,6), mark)
    small.save(destination / "installer-mark.bmp")
