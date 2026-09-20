from PIL import Image

try:
    img = Image.open('client/Minifantasy/Minifantasy_Creatures_v3.3_Commercial_Version/Minifantasy_Creatures_Assets/Base_Humanoids/Human/Base_Human/humanidle.png')
    img = img.convert('RGBA')
    crop = img.crop((0, 0, 32, 32))
    extrema = crop.getextrema()
    
    # Check if alpha channel has max value > 0 (meaning some pixels are visible)
    if extrema[3][1] > 0:
        print("Visible pixels found in (0,0,32,32). Alpha max:", extrema[3][1])
    else:
        print("Fully transparent in (0,0,32,32)!")
        
    # Check row 1 (32 to 64)
    crop2 = img.crop((0, 32, 32, 64))
    extrema2 = crop2.getextrema()
    print("Row 1 alpha max:", extrema2[3][1])
except Exception as e:
    print(e)
