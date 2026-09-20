import json
import os

weapons = {
    'sword1': {
        'base_path': 'Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/',
        'front': 'Sword/slash_sword_f.png',
        'back': 'Sword/slash_sword_b.png',
        'length': 4
    },
    'sword2': {
        'base_path': 'Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/',
        'front': 'Dagger/slash_dagger_f.png',
        'back': 'Dagger/slash_dagger_b.png',
        'length': 4
    },
    'redsword': {
        'base_path': 'Minifantasy/Minifantasy_Magic_Weapons_And_Effects_v1.0/Minifantasy_Magic_Weapons_And_Effects_Assets/Addon Effects (Minifantasy - Weapons)/Magic Weapons/Sword/',
        'front': 'Front Layer/sword_bleeding_f.png',
        'back': 'Back Layer/sword_bleeding_b.png',
        'length': 4
    },
    'goldensword': {
        'base_path': 'Minifantasy/Minifantasy_Magic_Weapons_And_Effects_v1.0/Minifantasy_Magic_Weapons_And_Effects_Assets/Addon Effects (Minifantasy - Weapons)/Magic Weapons/Sword/',
        'front': 'Front Layer/sword_stun_f_.png',
        'back': 'Back Layer/sword_stun_b.png',
        'length': 4
    },
    'axe': {
        'base_path': 'Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/',
        'front': 'Axe/slash_axe_f.png',
        'back': 'Axe/slash_axe_b.png',
        'length': 4
    },
    'morningstar': {
        'base_path': 'Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Swing_Attacks/',
        'front': 'swing_flail.png',
        'back': 'swing_flail.png',
        'length': 3
    }
}

base_dir = 'client/sprites'

for name, cfg in weapons.items():
    file_path = os.path.join(base_dir, f"{name}.json")
    
    data = {
        "id": name,
        "width": 32,
        "height": 32,
        "offset_x": -8,
        "offset_y": -7,
        "is_multi": True,
        "base_path": cfg['base_path'],
        "animations": {
            "idle_right": { "length": 14, "row": 0, "file": "" },
            "walk_right": { "length": 4,  "row": 0, "file": "" },
            "atk_right":  { "length": cfg['length'], "row": 0, "file": cfg['front'] },
            
            "idle_up":    { "length": 14, "row": 3, "file": "" },
            "walk_up":    { "length": 4,  "row": 3, "file": "" },
            "atk_up":     { "length": cfg['length'], "row": 3, "file": cfg['back'] },
            
            "idle_down":  { "length": 14, "row": 0, "file": "" },
            "walk_down":  { "length": 4,  "row": 0, "file": "" },
            "atk_down":   { "length": cfg['length'], "row": 0, "file": cfg['front'] },
            
            "death":      { "length": 12, "row": 0, "file": "" }
        }
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

print("Weapons successfully converted.")

