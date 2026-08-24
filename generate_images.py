from PIL import Image, ImageDraw

def create_synthetic_image(filename, draw_func):
    img = Image.new('RGB', (512, 512), color=(34, 139, 34)) # Forest Green background
    draw = ImageDraw.Draw(img)
    draw_func(draw)
    img.save(filename)
    print(f"Saved {filename}")

# Image T1: Past (Small water body, empty fields)
def draw_t1(draw):
    # Small pond
    draw.ellipse((200, 200, 250, 250), fill=(30, 144, 255)) # Dodger Blue
    # A few brown dirt patches
    draw.rectangle((50, 50, 150, 150), fill=(139, 69, 19)) # Saddle Brown
    draw.rectangle((350, 350, 450, 450), fill=(139, 69, 19))

# Image T2: Current (Expanded watershed intervention)
def draw_t2(draw):
    # Massively expanded water body (watershed intervention success)
    draw.ellipse((150, 150, 300, 300), fill=(30, 144, 255))
    # Some new vegetation over the dirt patches
    draw.rectangle((50, 50, 150, 150), fill=(50, 205, 50)) # Lime Green
    draw.rectangle((350, 350, 450, 450), fill=(50, 205, 50))

create_synthetic_image("C:\\Users\\Yuvraj\\Desktop\\sih_internal\\test_data\\synthetic_t1_past.tif", draw_t1)
create_synthetic_image("C:\\Users\\Yuvraj\\Desktop\\sih_internal\\test_data\\synthetic_t2_current.tif", draw_t2)