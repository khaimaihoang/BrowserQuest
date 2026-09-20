import json
import os

armors = {
    'clotharmor': 'white',
    'leatherarmor': 'brownleather',
    'mailarmor': 'grey',
    'platearmor': 'blackleather',
    'redarmor': 'red',
    'goldenarmor': 'yellow'
}

base_dir = 'client/sprites'

template = {
    "width": 32,
    "height": 32,
    "offset_x": -8,
    "offset_y": -7,
    "is_multi": True,
    "base_path": "Minifantasy/Minifantasy_AMyriadOfNPCs_v.1.0/Minifantasy_NPCs_Assets/Generic_NPCs/",
    "animations": {}
}

for name, color in armors.items():
    file_path = os.path.join(base_dir, f"{name}.json")
    
    data = dict(template)
    data["id"] = name
    data["animations"] = {
        "idle_right": { "length": 14, "row": 0, "file": f"Idle/Body/Shirt/minifantasy_npcsidle_shirt_{color}.png" },
        "walk_right": { "length": 4,  "row": 0, "file": f"Walk/Body/Shirt/minifantasy_npcswalk_shirt_{color}.png" },
        "atk_right":  { "length": 4,  "row": 0, "file": "" },
        
        "idle_up":    { "length": 14, "row": 3, "file": f"Idle/Body/Shirt/minifantasy_npcsidle_shirt_{color}.png" },
        "walk_up":    { "length": 4,  "row": 3, "file": f"Walk/Body/Shirt/minifantasy_npcswalk_shirt_{color}.png" },
        "atk_up":     { "length": 4,  "row": 3, "file": "" },
        
        "idle_down":  { "length": 14, "row": 0, "file": f"Idle/Body/Shirt/minifantasy_npcsidle_shirt_{color}.png" },
        "walk_down":  { "length": 4,  "row": 0, "file": f"Walk/Body/Shirt/minifantasy_npcswalk_shirt_{color}.png" },
        "atk_down":   { "length": 4,  "row": 0, "file": "" },
        
        "death":      { "length": 12, "row": 0, "file": f"Die/Body/Shirt/minifantasy_npcsdie_shirt_{color}.png" }
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
print("Armors successfully converted.")

