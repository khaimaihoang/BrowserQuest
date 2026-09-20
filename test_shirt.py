from PIL import Image

try:
    img = Image.open('client/Minifantasy/Minifantasy_AMyriadOfNPCs_v.1.0/Minifantasy_NPCs_Assets/Generic_NPCs/Idle/Body/Shirt/minifantasy_npcsidle_shirt_white.png')
    img = img.convert('RGBA')

    img_human = Image.open('client/Minifantasy/Minifantasy_Creatures_v3.3_Commercial_Version/Minifantasy_Creatures_Assets/Base_Humanoids/Human/Base_Human/humanidle.png')
    img_human = img_human.convert('RGBA')

    # Get bounding box of non-transparent pixels
    bbox_shirt = img.getbbox()
    bbox_human = img_human.getbbox()
    
    print("Shirt bbox:", bbox_shirt)
    print("Human bbox:", bbox_human)

except Exception as e:
    print(e)
