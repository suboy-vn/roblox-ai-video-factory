import streamlit as st
from pathlib import Path
import json
import re
import math
import shutil
import subprocess
import pandas as pd
from datetime import datetime

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
CONFIG = DATA / "config.json"
PROJECTS = DATA / "projects.json"

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def lua_string(value):
    """Return a safely quoted Luau string literal."""
    return json.dumps(str(value or ""), ensure_ascii=False)


def safe_filename(value):
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "RobloxCharacter")).strip("_")
    return (value or "RobloxCharacter")[:64]


def build_roblox_r6_script(character, palette, spawn_y=3, add_hair=False,
                           hair_color="#7D4126", add_backpack=False,
                           shirt_id="", pants_id="", face_id=""):
    """Build a one-shot Luau script that creates a blocky R6-style NPC in Workspace."""
    name = character.get("name", "Roblox Character")
    role = character.get("role", "Character")
    char_id = character.get("character_id", safe_filename(name))
    appearance = character.get("visual_description", "")
    personality = character.get("personality", "")
    continuity = character.get("continuity_rules", "")

    def rgb(hex_color):
        h = str(hex_color).strip().lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
            h = "F5CD30"
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    colors = {key: rgb(palette.get(key, "#F5CD30")) for key in ("head", "torso", "arms", "legs")}
    hair_rgb = rgb(hair_color)
    shirt_id = re.sub(r"\D", "", str(shirt_id or ""))
    pants_id = re.sub(r"\D", "", str(pants_id or ""))
    face_id = re.sub(r"\D", "", str(face_id or ""))
    model_name = safe_filename(name)
    face_texture = f"rbxassetid://{face_id}" if face_id else "rbxasset://textures/face.png"

    lua = f"""-- ROBLOX AI VIDEO FACTORY 1.0
-- Generated R6-style blocky NPC. Run this script in Roblox Studio.
-- Creates a rig in Workspace; then right-click the Model > Save to File to export .rbxm.

local Workspace = game:GetService("Workspace")
local modelName = {lua_string(model_name)}
local oldModel = Workspace:FindFirstChild(modelName)
if oldModel then oldModel:Destroy() end

local model = Instance.new("Model")
model.Name = modelName
model:SetAttribute("CharacterId", {lua_string(char_id)})
model:SetAttribute("CharacterRole", {lua_string(role)})
model:SetAttribute("VisualDescription", {lua_string(appearance)})
model:SetAttribute("Personality", {lua_string(personality)})
model:SetAttribute("ContinuityRules", {lua_string(continuity)})
model.Parent = Workspace

local spawn = CFrame.new(0, {float(spawn_y):.2f}, 0)
local function makePart(partName, size, color, relativeCFrame, canCollide, parent)
    local part = Instance.new("Part")
    part.Name = partName
    part.Size = size
    part.Color = color
    part.Material = Enum.Material.SmoothPlastic
    part.TopSurface = Enum.SurfaceType.Smooth
    part.BottomSurface = Enum.SurfaceType.Smooth
    part.Anchored = false
    part.CanCollide = canCollide
    part.CanTouch = true
    part.CanQuery = true
    part.Massless = false
    part.CFrame = spawn * relativeCFrame
    part.Parent = parent or model
    return part
end

local root = makePart("HumanoidRootPart", Vector3.new(2, 2, 1), Color3.new(1,1,1), CFrame.new(0,0,0), false)
root.Transparency = 1
root.CanTouch = false
root.CanQuery = false
local torso = makePart("Torso", Vector3.new(2, 2, 1), Color3.fromRGB({colors['torso'][0]}, {colors['torso'][1]}, {colors['torso'][2]}), CFrame.new(0,0,0), true)
local head = makePart("Head", Vector3.new(2, 1, 1), Color3.fromRGB({colors['head'][0]}, {colors['head'][1]}, {colors['head'][2]}), CFrame.new(0,1.5,0), true)
local leftArm = makePart("Left Arm", Vector3.new(1, 2, 1), Color3.fromRGB({colors['arms'][0]}, {colors['arms'][1]}, {colors['arms'][2]}), CFrame.new(-1.5,0,0), false)
local rightArm = makePart("Right Arm", Vector3.new(1, 2, 1), Color3.fromRGB({colors['arms'][0]}, {colors['arms'][1]}, {colors['arms'][2]}), CFrame.new(1.5,0,0), false)
local leftLeg = makePart("Left Leg", Vector3.new(1, 2, 1), Color3.fromRGB({colors['legs'][0]}, {colors['legs'][1]}, {colors['legs'][2]}), CFrame.new(-0.5,-2,0), true)
local rightLeg = makePart("Right Leg", Vector3.new(1, 2, 1), Color3.fromRGB({colors['legs'][0]}, {colors['legs'][1]}, {colors['legs'][2]}), CFrame.new(0.5,-2,0), true)

local function makeMotor(jointName, part0, part1, c0, c1)
    local motor = Instance.new("Motor6D")
    motor.Name = jointName
    motor.Part0 = part0
    motor.Part1 = part1
    motor.C0 = c0
    motor.C1 = c1
    motor.Parent = part0
    return motor
end

makeMotor("RootJoint", root, torso, CFrame.new(0,0,0), CFrame.new(0,0,0))
makeMotor("Neck", torso, head, CFrame.new(0,1,0), CFrame.new(0,-0.5,0))
makeMotor("Left Shoulder", torso, leftArm, CFrame.new(-1,0.5,0), CFrame.new(0.5,0.5,0))
makeMotor("Right Shoulder", torso, rightArm, CFrame.new(1,0.5,0), CFrame.new(-0.5,0.5,0))
makeMotor("Left Hip", torso, leftLeg, CFrame.new(-0.5,-1,0), CFrame.new(0.5,1,0))
makeMotor("Right Hip", torso, rightLeg, CFrame.new(0.5,-1,0), CFrame.new(-0.5,1,0))

local humanoid = Instance.new("Humanoid")
humanoid.Name = "Humanoid"
humanoid.RigType = Enum.HumanoidRigType.R6
humanoid.DisplayName = {lua_string(name)}
humanoid.MaxHealth = 100
humanoid.Health = 100
humanoid.WalkSpeed = 16
humanoid.JumpPower = 50
humanoid.RequiresNeck = true
humanoid.Parent = model
local animator = Instance.new("Animator")
animator.Parent = humanoid
model.PrimaryPart = root

local face = Instance.new("Decal")
face.Name = "face"
face.Face = Enum.NormalId.Front
face.Texture = {lua_string(face_texture)}
face.Parent = head
"""
    if shirt_id:
        lua += f"\nlocal shirt = Instance.new(\"Shirt\")\nshirt.Name = \"Shirt\"\nshirt.ShirtTemplate = \"rbxassetid://{shirt_id}\"\nshirt.Parent = model\n"
    if pants_id:
        lua += f"\nlocal pants = Instance.new(\"Pants\")\npants.Name = \"Pants\"\npants.PantsTemplate = \"rbxassetid://{pants_id}\"\npants.Parent = model\n"
    if add_hair:
        lua += f"""
-- Simple procedural block hair; replace with a permitted catalog accessory for higher detail.
local function addWeldedBlock(partName, size, headOffset, rotation)
    local block = Instance.new("Part")
    block.Name = partName
    block.Size = size
    block.Color = Color3.fromRGB({hair_rgb[0]}, {hair_rgb[1]}, {hair_rgb[2]})
    block.Material = Enum.Material.SmoothPlastic
    block.TopSurface = Enum.SurfaceType.Smooth
    block.BottomSurface = Enum.SurfaceType.Smooth
    block.Anchored = false
    block.CanCollide = false
    block.CanTouch = false
    block.CanQuery = false
    block.Massless = true
    block.CFrame = head.CFrame * CFrame.new(headOffset) * CFrame.Angles(rotation[1], rotation[2], rotation[3])
    block.Parent = model
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = head
    weld.Part1 = block
    weld.Parent = block
end
addWeldedBlock("Hair_Crown", Vector3.new(1.8,0.35,1.05), Vector3.new(0,0.62,0), {{0,0,0}})
addWeldedBlock("Hair_Front_Left", Vector3.new(0.48,0.95,0.42), Vector3.new(-0.58,0.15,-0.42), {{0,0,-0.12}})
addWeldedBlock("Hair_Front_Center", Vector3.new(0.5,0.78,0.42), Vector3.new(0,0.22,-0.48), {{0.08,0,0.04}})
addWeldedBlock("Hair_Front_Right", Vector3.new(0.48,0.88,0.42), Vector3.new(0.58,0.18,-0.40), {{0,0,0.12}})
addWeldedBlock("Hair_Side_Left", Vector3.new(0.36,0.75,0.7), Vector3.new(-0.82,-0.05,0.05), {{0,0,-0.08}})
"""
    if add_backpack:
        lua += """
-- Simple backpack block welded to the back of the torso.
local backpack = Instance.new("Part")
backpack.Name = "Backpack_Block"
backpack.Size = Vector3.new(1.15,1.1,0.45)
backpack.Color = Color3.fromRGB(95,65,45)
backpack.Material = Enum.Material.SmoothPlastic
backpack.Anchored = false
backpack.CanCollide = false
backpack.CanTouch = false
backpack.CanQuery = false
backpack.Massless = true
backpack.CFrame = torso.CFrame * CFrame.new(0,0.05,0.72)
backpack.Parent = model
local backpackWeld = Instance.new("WeldConstraint")
backpackWeld.Part0 = torso
backpackWeld.Part1 = backpack
backpackWeld.Parent = backpack
"""
    lua += """
model:PivotTo(spawn)
print("[ROBLOX AI VIDEO FACTORY] Created rig:", model:GetFullName())
print("Select the model in Workspace and use Save to File to export an .rbxm asset.")
"""
    return lua


def make_studio_launcher(studio_exe, place_file, script_name="build_character.lua"):
    """Create a Windows launcher for Roblox Studio's documented RunScript CLI."""
    studio = str(studio_exe or "").strip()
    place = str(place_file or "").strip()
    lines = ["@echo off", "setlocal", 'cd /d "%~dp0"']
    if studio:
        lines.append(f'set "STUDIO_EXE={studio}"')
    else:
        lines += [
            'set "STUDIO_EXE="',
            'for /d %%D in ("%LOCALAPPDATA%\\Roblox\\Versions\\version-*") do (',
            '  if exist "%%~fD\\RobloxStudioBeta.exe" set "STUDIO_EXE=%%~fD\\RobloxStudioBeta.exe"',
            ')'
        ]
    lines += [
        'if not defined STUDIO_EXE (echo Khong tim thay RobloxStudioBeta.exe. Hay chon duong dan trong Dashboard > Cai dat.& pause & exit /b 1)',
        'if not exist "%STUDIO_EXE%" (echo Duong dan Roblox Studio khong ton tai: "%STUDIO_EXE%"& pause & exit /b 1)'
    ]
    if place:
        lines.append(f'"%STUDIO_EXE%" --task RunScript --localPlaceFile "{place}" --runScriptFile "%~dp0{script_name}" --outputFile "%~dp0studio_build.log"')
    else:
        lines.append(f'"%STUDIO_EXE%" --task RunScript --runScriptFile "%~dp0{script_name}" --outputFile "%~dp0studio_build.log"')
    lines += ['if errorlevel 1 echo Roblox Studio ket thuc voi loi. Kiem tra studio_build.log.', 'pause', 'endlocal']
    return "\r\n".join(lines) + "\r\n"


def hex_rgb(hex_color, fallback="#777777"):
    value = str(hex_color or fallback).strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        value = fallback.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def world_mood_settings(mood):
    settings = {
        "Ban ngày": {"clock": 14, "brightness": 2.2, "ambient": "#8C8C8C", "outdoor": "#BDBDBD", "fog": "#D7E3EA", "fog_end": 100000},
        "Hoàng hôn": {"clock": 18.2, "brightness": 2.0, "ambient": "#A66D55", "outdoor": "#D99A72", "fog": "#E9A77C", "fog_end": 1400},
        "Ban đêm": {"clock": 0.4, "brightness": 1.0, "ambient": "#27334D", "outdoor": "#34445F", "fog": "#192235", "fog_end": 850},
        "U ám": {"clock": 11, "brightness": 1.25, "ambient": "#626A70", "outdoor": "#7D858A", "fog": "#9AA3A8", "fog_end": 900},
        "Kinh dị": {"clock": 1.1, "brightness": 0.75, "ambient": "#28202E", "outdoor": "#352A3A", "fog": "#332A38", "fog_end": 360},
    }
    return settings.get(mood, settings["Ban ngày"])


def make_world_template(world_name, environment, mood, map_size, building_count, tree_count, prop_count, seed, notes=""):
    """Create a deterministic, editable world plan from built-in Roblox-friendly primitives."""
    import random
    rng = random.Random(int(seed))
    half = map_size / 2 - 18
    env = environment
    base = {
        "Thành phố": ("#666B70", "Concrete"),
        "Rừng": ("#477A3F", "Grass"),
        "Đảo": ("#CDBB83", "Sand"),
        "Trường học": ("#5C984E", "Grass"),
        "Hầm ngầm": ("#55565B", "Concrete"),
        "Thế giới giả tưởng": ("#536B53", "Grass"),
    }
    ground_color, ground_material = base.get(env, base["Thành phố"])
    plan = {
        "name": world_name.strip() or "Roblox World",
        "environment": env,
        "mood": mood,
        "map_size": int(map_size),
        "seed": int(seed),
        "description": notes.strip() or f"A {mood.lower()} {env.lower()} environment for an original Roblox story.",
        "ground_color": ground_color,
        "ground_material": ground_material,
        "lighting": world_mood_settings(mood),
        "objects": []
    }

    def add(kind, name, x, z, w=10, d=10, h=8, color="#888888", material="Concrete", rotation=0):
        plan["objects"].append({
            "kind": kind, "name": str(name)[:48],
            "x": round(max(-half, min(half, float(x))), 1),
            "z": round(max(-half, min(half, float(z))), 1),
            "w": round(max(2, min(90, float(w))), 1),
            "d": round(max(2, min(90, float(d))), 1),
            "h": round(max(2, min(100, float(h))), 1),
            "color": color, "material": material,
            "rotation": int(rotation) % 360
        })

    # A cross-road or main route gives each map a readable navigational spine.
    if env in ("Thành phố", "Trường học", "Hầm ngầm"):
        add("road", "Main_Road_EW", 0, 0, map_size - 24, 18, 1, "#34383D", "Asphalt")
        add("road", "Main_Road_NS", 0, 0, 18, map_size - 24, 1, "#34383D", "Asphalt")
    elif env in ("Rừng", "Đảo"):
        add("road", "Trail_Main", 0, 0, map_size - 55, 9, 1, "#8A7854" if env == "Rừng" else "#A99162", "Ground")
    else:
        add("road", "Mystic_Path", 0, 0, map_size - 45, 12, 1, "#6A6477", "Slate")

    if env == "Thành phố":
        slots = [(-half*.62,-half*.62),(-half*.18,-half*.62),(half*.28,-half*.62),(half*.68,-half*.62),
                 (-half*.62,half*.62),(-half*.18,half*.62),(half*.28,half*.62),(half*.68,half*.62)]
        for i,(x,z) in enumerate(slots[:building_count]):
            colors = ["#B86F55", "#8D9AA6", "#D2B56E", "#7C8495"]
            add("building", f"City_Building_{i+1}", x, z, 25+rng.randint(0,12), 24+rng.randint(0,12), 24+rng.randint(0,28), colors[i%len(colors)], "Brick" if i%2 else "Concrete", rng.choice([0,90,180,270]))
        for i in range(max(3, prop_count)):
            x = rng.choice([-half*.35, half*.35]) + rng.uniform(-12,12)
            z = rng.uniform(-half*.45, half*.45)
            add("lamp", f"Street_Lamp_{i+1}", x, z, 2, 2, 12, "#4C535A", "Metal")
        for i in range(tree_count):
            x = rng.choice([-half*.82, half*.82]) + rng.uniform(-8,8)
            z = rng.uniform(-half*.82, half*.82)
            add("tree", f"Roadside_Tree_{i+1}", x, z, 5, 5, rng.randint(12,20), "#347A3D", "Wood")
    elif env == "Rừng":
        add("building", "Ranger_Cabin", -18, -35, 28, 22, 16, "#78553A", "WoodPlanks", 0)
        add("crate", "Supply_Crate_A", 5, -28, 5, 5, 5, "#90663C", "Wood")
        add("crate", "Supply_Crate_B", 12, -27, 4, 4, 4, "#90663C", "Wood")
        for i in range(tree_count):
            x = rng.uniform(-half, half); z = rng.uniform(-half, half)
            if abs(x) < 32 and abs(z) < 32: x += 42 if x >= 0 else -42
            add("tree", f"Forest_Tree_{i+1}", x, z, rng.randint(5,8), rng.randint(5,8), rng.randint(16,27), rng.choice(["#286A35","#347A3D","#4B8B45"]), "Wood")
        for i in range(prop_count):
            add("rock", f"Forest_Rock_{i+1}", rng.uniform(-half,half), rng.uniform(-half,half), rng.randint(4,9), rng.randint(4,9), rng.randint(3,8), "#73756F", "Slate")
    elif env == "Đảo":
        plan["water_base"] = True
        add("building", "Beach_Hut", -22, -22, 22, 18, 12, "#A9794D", "WoodPlanks", 0)
        add("spawn", "Island_Spawn", 0, 12, 7, 7, 1, "#36A3A8", "Neon")
        for i in range(tree_count):
            angle = (2*3.14159*i/max(tree_count,1)) + rng.uniform(-.22,.22)
            radius = rng.uniform(map_size*.19,map_size*.34)
            add("tree", f"Palm_Tree_{i+1}", math.cos(angle)*radius, math.sin(angle)*radius, 5, 5, rng.randint(15,24), "#3D8A45", "Wood")
        for i in range(prop_count):
            add("rock", f"Beach_Rock_{i+1}", rng.uniform(-half,half), rng.uniform(-half,half), 5, 5, 4, "#9A9587", "Rock")
    elif env == "Trường học":
        add("building", "Main_School", 0, -half*.55, 62, 28, 27, "#D9C7A3", "Brick", 0)
        add("road", "School_Courtyard", 0, half*.38, 76, 34, 1, "#8C969B", "Concrete")
        for i in range(tree_count):
            x = (-1 if i%2==0 else 1) * (half*.62 + rng.uniform(-5,5))
            z = rng.uniform(-half*.4,half*.75)
            add("tree", f"Campus_Tree_{i+1}", x, z, 5, 5, rng.randint(12,19), "#347A3D", "Wood")
        for i in range(prop_count):
            add("crate", f"Playground_Prop_{i+1}", rng.uniform(-40,40), rng.uniform(15,half*.65), 6, 3, 3, "#D17D37", "Wood")
        for i in range(building_count):
            if i == 0: continue
            add("building", f"Campus_Block_{i}", rng.choice([-half*.65,half*.65]), rng.uniform(-10,half*.45), 22, 20, 15, "#C6B38E", "Brick", rng.choice([0,90,180,270]))
    elif env == "Hầm ngầm":
        add("building", "Bunker_Main", 0, -30, 68, 45, 18, "#59616A", "Concrete", 0)
        add("building", "Control_Room", 0, 28, 36, 24, 13, "#46525F", "Metal", 0)
        for i in range(tree_count):
            # In a bunker scene, this slider controls debris/rock obstacles.
            add("rock", f"Debris_{i+1}", rng.uniform(-half,half), rng.uniform(-half,half), rng.randint(4,10), rng.randint(4,10), rng.randint(3,7), "#55575A", "Concrete")
        for i in range(max(2,prop_count)):
            add("lamp", f"Emergency_Lamp_{i+1}", rng.uniform(-half*.7,half*.7), rng.uniform(-half*.7,half*.7), 2, 2, 10, "#555D65", "Metal")
        for i in range(max(0,building_count-2)):
            add("fence", f"Barrier_{i+1}", rng.uniform(-half*.7,half*.7), rng.uniform(-half*.7,half*.7), 18, 2, 5, "#74777B", "Metal")
    else:  # fantasy
        add("tower", "Ancient_Tower", 0, -25, 24, 24, 52, "#81709B", "Slate", 0)
        for i in range(tree_count):
            x = rng.uniform(-half,half); z = rng.uniform(-half,half)
            add("tree", f"Fantasy_Tree_{i+1}", x, z, 6, 6, rng.randint(17,28), "#365E69", "Wood")
        for i in range(prop_count):
            add("crystal", f"Magic_Crystal_{i+1}", rng.uniform(-half,half), rng.uniform(-half,half), 4, 4, rng.randint(8,16), "#59B6D6", "Neon")
        for i in range(max(0,building_count-1)):
            add("tower", f"Ruined_Tower_{i+1}", rng.uniform(-half,half), rng.uniform(-half,half), 12, 12, rng.randint(20,36), "#716780", "Slate")

    # One clear player spawn is guaranteed in every generated map.
    if not any(o["kind"] == "spawn" for o in plan["objects"]):
        add("spawn", "Player_Spawn", 0, 10, 7, 7, 1, "#36A3A8", "Neon")
    return plan


def normalize_ai_world_plan(ai_data, base_plan):
    """Validate untrusted AI JSON and return only supported, bounded world objects."""
    allowed_kinds = {"building", "tower", "tree", "rock", "lamp", "fence", "crate", "spawn", "crystal", "bush", "road"}
    allowed_materials = {"Grass", "Ground", "Sand", "Concrete", "Brick", "Wood", "WoodPlanks", "Slate", "Rock", "Metal", "Asphalt", "Neon", "Glass", "Sandstone"}
    result = dict(base_plan)
    result["description"] = str(ai_data.get("description") or base_plan["description"])[:1200]
    objects = []
    half = base_plan["map_size"] / 2 - 18
    for item in (ai_data.get("objects") or [])[:90]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind", "")).lower()
        if kind not in allowed_kinds:
            continue
        material = str(item.get("material", "Concrete"))
        if material not in allowed_materials:
            material = "Concrete"
        color = str(item.get("color", "#888888"))
        if not re.fullmatch(r"#?[0-9a-fA-F]{6}", color):
            color = "#888888"
        def bounded(key, default, low, high):
            try: value = float(item.get(key, default))
            except (TypeError, ValueError): value = float(default)
            return round(max(low, min(high, value)), 1)
        objects.append({
            "kind": kind, "name": str(item.get("name") or f"{kind.title()}_{len(objects)+1}")[:48],
            "x": bounded("x", 0, -half, half), "z": bounded("z", 0, -half, half),
            "w": bounded("w", 10, 2, 90), "d": bounded("d", 10, 2, 90),
            "h": bounded("h", 8, 2, 100), "color": color if color.startswith("#") else "#"+color,
            "material": material, "rotation": int(bounded("rotation", 0, 0, 359))
        })
    if not objects:
        raise ValueError("AI không trả về object hợp lệ. Hãy thử lại hoặc dùng chế độ theo mẫu.")
    result["objects"] = objects
    if not any(o["kind"] == "spawn" for o in objects):
        result["objects"].append({"kind":"spawn","name":"Player_Spawn","x":0,"z":10,"w":7,"d":7,"h":1,"color":"#36A3A8","material":"Neon","rotation":0})
    return result


def build_roblox_world_script(plan):
    """Build a self-contained Luau script that creates an editable block-based map."""
    world_name = safe_filename(plan.get("name", "RobloxWorld"))
    size = int(plan.get("map_size", 400))
    mood = plan.get("lighting") or world_mood_settings(plan.get("mood", "Ban ngày"))
    ground_rgb = hex_rgb(plan.get("ground_color", "#777777"))
    mood_ambient = hex_rgb(mood.get("ambient", "#888888"))
    mood_outdoor = hex_rgb(mood.get("outdoor", "#BBBBBB"))
    mood_fog = hex_rgb(mood.get("fog", "#D7E3EA"))
    ground_material = plan.get("ground_material", "Grass")
    allowed_materials = {"Grass", "Ground", "Sand", "Concrete", "Brick", "Wood", "WoodPlanks", "Slate", "Rock", "Metal", "Asphalt", "Neon", "Glass", "Sandstone"}
    if ground_material not in allowed_materials:
        ground_material = "Grass"
    objects = plan.get("objects", [])[:120]
    lines = []
    lines.append("-- ROBLOX AI VIDEO FACTORY 1.0 | WORLD BUILDER")
    lines.append("-- Generated editable block-based environment. Run in Roblox Studio.")
    lines.append("local Workspace = game:GetService('Workspace')")
    lines.append("local Lighting = game:GetService('Lighting')")
    lines.append(f"local worldName = {lua_string(world_name)}")
    lines.append("local old = Workspace:FindFirstChild(worldName)")
    lines.append("if old then old:Destroy() end")
    lines.append("local folder = Instance.new('Folder'); folder.Name = worldName; folder.Parent = Workspace")
    lines.append(f"folder:SetAttribute('Environment', {lua_string(plan.get('environment',''))})")
    lines.append(f"folder:SetAttribute('Mood', {lua_string(plan.get('mood',''))})")
    lines.append(f"folder:SetAttribute('WorldDescription', {lua_string(plan.get('description',''))})")
    lines.append(f"Lighting.ClockTime = {float(mood.get('clock',14)):.2f}")
    lines.append(f"Lighting.Brightness = {float(mood.get('brightness',2)):.2f}")
    lines.append(f"Lighting.Ambient = Color3.fromRGB({mood_ambient[0]}, {mood_ambient[1]}, {mood_ambient[2]})")
    lines.append(f"Lighting.OutdoorAmbient = Color3.fromRGB({mood_outdoor[0]}, {mood_outdoor[1]}, {mood_outdoor[2]})")
    lines.append(f"Lighting.FogColor = Color3.fromRGB({mood_fog[0]}, {mood_fog[1]}, {mood_fog[2]})")
    lines.append(f"Lighting.FogStart = 0; Lighting.FogEnd = {int(mood.get('fog_end',100000))}")
    lines.append("local function mat(name) return Enum.Material[name] or Enum.Material.SmoothPlastic end")
    lines.append("local function part(name, size, pos, color, material, shape, rotation, parent, collide)")
    lines.append("    local p = Instance.new('Part'); p.Name = name; p.Size = size")
    lines.append("    p.CFrame = CFrame.new(pos.X, pos.Y, pos.Z) * CFrame.Angles(0, math.rad(rotation or 0), 0)")
    lines.append("    p.Color = color; p.Material = mat(material or 'Concrete'); p.Anchored = true")
    lines.append("    p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth")
    lines.append("    p.CanCollide = collide ~= false; p.Parent = parent or folder")
    lines.append("    if shape and shape ~= 'Block' then p.Shape = Enum.PartType[shape] or Enum.PartType.Block end")
    lines.append("    return p")
    lines.append("end")
    lines.append(f"local mapSize = {size}")
    lines.append(f"part('Ground', Vector3.new(mapSize, 4, mapSize), Vector3.new(0, -2, 0), Color3.fromRGB({ground_rgb[0]}, {ground_rgb[1]}, {ground_rgb[2]}), '{ground_material}', 'Block', 0, folder, true)")
    if plan.get("water_base"):
        lines.append("local water = part('Ocean_Base', Vector3.new(mapSize + 120, 3, mapSize + 120), Vector3.new(0, -5.5, 0), Color3.fromRGB(39, 119, 166), 'Water', 'Block', 0, folder, true)")
    lines.append("local function addBuilding(o)")
    lines.append("    local x,z,w,d,h = o.x,o.z,o.w,o.d,o.h; local rot = o.rotation")
    lines.append("    local base = part(o.name, Vector3.new(w,h,d), Vector3.new(x,h/2,z), o.color, o.material, 'Block', rot, folder, true)")
    lines.append("    part(o.name..'_Roof', Vector3.new(w+2, math.max(1.5,h*0.07), d+2), Vector3.new(x,h+0.8,z), Color3.fromRGB(65,68,74), 'Slate', 'Block', rot, folder, true)")
    lines.append("    local localCF = CFrame.new(x,0,z) * CFrame.Angles(0, math.rad(rot), 0)")
    lines.append("    local doorPos = (localCF * CFrame.new(0, math.min(4,h*0.22), -d/2-0.16)).Position")
    lines.append("    part(o.name..'_Door', Vector3.new(math.max(2,w*0.13), math.min(8,h*0.46), 0.3), doorPos, Color3.fromRGB(83,55,39), 'Wood', 'Block', rot, folder, true)")
    lines.append("    for _,side in ipairs({-1,1}) do")
    lines.append("        local winPos = (localCF * CFrame.new(side*w*0.27, h*0.62, -d/2-0.18)).Position")
    lines.append("        part(o.name..'_Window_'..tostring(side), Vector3.new(math.max(2,w*0.18), math.max(2,h*0.18), 0.25), winPos, Color3.fromRGB(125,190,211), 'Glass', 'Block', rot, folder, false)")
    lines.append("    end")
    lines.append("end")
    lines.append("local function addTree(o)")
    lines.append("    part(o.name..'_Trunk', Vector3.new(math.max(2,o.w*0.28), o.h*0.58, math.max(2,o.d*0.28)), Vector3.new(o.x,o.h*0.29,o.z), Color3.fromRGB(105,72,45), 'Wood', 'Block', o.rotation, folder, true)")
    lines.append("    part(o.name..'_Canopy', Vector3.new(o.w*1.65, o.h*0.48, o.d*1.65), Vector3.new(o.x,o.h*0.78,o.z), o.color, 'Grass', 'Ball', 0, folder, true)")
    lines.append("end")
    lines.append("local function addLamp(o)")
    lines.append("    part(o.name..'_Pole', Vector3.new(0.8,o.h,0.8), Vector3.new(o.x,o.h/2,o.z), o.color, 'Metal', 'Block', o.rotation, folder, true)")
    lines.append("    local glow = part(o.name..'_Light', Vector3.new(2.5,1.2,2.5), Vector3.new(o.x,o.h+0.5,o.z), Color3.fromRGB(255,231,153), 'Neon', 'Ball', 0, folder, false)")
    lines.append("    local light = Instance.new('PointLight'); light.Brightness = 1.5; light.Range = 18; light.Parent = glow")
    lines.append("end")
    lines.append("local function addFence(o)")
    lines.append("    local count = math.max(2, math.floor(o.w/8)); local left = -o.w/2")
    lines.append("    for i=0,count do local x = o.x + left + o.w*i/count; part(o.name..'_Post_'..i, Vector3.new(1,o.h,1), Vector3.new(x,o.h/2,o.z), o.color, o.material, 'Block', o.rotation, folder, true) end")
    lines.append("    part(o.name..'_Rail_Low', Vector3.new(o.w,o.h*0.12,0.8), Vector3.new(o.x,o.h*0.35,o.z), o.color, o.material, 'Block', o.rotation, folder, true)")
    lines.append("    part(o.name..'_Rail_High', Vector3.new(o.w,o.h*0.12,0.8), Vector3.new(o.x,o.h*0.72,o.z), o.color, o.material, 'Block', o.rotation, folder, true)")
    lines.append("end")
    lines.append("local function addObject(o)")
    lines.append("    if o.kind == 'building' or o.kind == 'tower' then addBuilding(o)")
    lines.append("    elseif o.kind == 'tree' then addTree(o)")
    lines.append("    elseif o.kind == 'lamp' then addLamp(o)")
    lines.append("    elseif o.kind == 'fence' then addFence(o)")
    lines.append("    elseif o.kind == 'spawn' then")
    lines.append("        local s = Instance.new('SpawnLocation'); s.Name = o.name; s.Size = Vector3.new(o.w,1,o.d); s.Position = Vector3.new(o.x,0.6,o.z); s.Anchored = true; s.Neutral = true; s.Duration = 0; s.Parent = folder")
    lines.append("    elseif o.kind == 'crystal' then")
    lines.append("        local c = part(o.name, Vector3.new(o.w*0.65,o.h,o.d*0.65), Vector3.new(o.x,o.h/2,o.z), o.color, 'Neon', 'Ball', o.rotation, folder, false)")
    lines.append("    elseif o.kind == 'water' then part(o.name, Vector3.new(o.w,2,o.d), Vector3.new(o.x,0,o.z), o.color, 'Water', 'Block', o.rotation, folder, true)")
    lines.append("    elseif o.kind == 'bush' or o.kind == 'rock' then part(o.name, Vector3.new(o.w,o.h,o.d), Vector3.new(o.x,o.h/2,o.z), o.color, o.material, 'Ball', o.rotation, folder, true)")
    lines.append("    elseif o.kind == 'road' then part(o.name, Vector3.new(o.w,0.5,o.d), Vector3.new(o.x,0.15,o.z), o.color, o.material, 'Block', o.rotation, folder, true)")
    lines.append("    else part(o.name, Vector3.new(o.w,o.h,o.d), Vector3.new(o.x,o.h/2,o.z), o.color, o.material, 'Block', o.rotation, folder, true) end")
    lines.append("end")
    lines.append("local objects = {")
    for obj in objects:
        r,g,b = hex_rgb(obj.get("color", "#888888"))
        mat_name = obj.get("material", "Concrete")
        if mat_name not in allowed_materials: mat_name = "Concrete"
        fields = [
            f"kind={lua_string(obj.get('kind','crate'))}", f"name={lua_string(safe_filename(obj.get('name','Object')))}",
            f"x={float(obj.get('x',0)):.1f}", f"z={float(obj.get('z',0)):.1f}",
            f"w={float(obj.get('w',8)):.1f}", f"d={float(obj.get('d',8)):.1f}", f"h={float(obj.get('h',8)):.1f}",
            f"color=Color3.fromRGB({r},{g},{b})", f"material={lua_string(mat_name)}", f"rotation={int(obj.get('rotation',0))}"
        ]
        lines.append("    {" + ", ".join(fields) + "},")
    lines.append("}")
    lines.append("for _, objectSpec in ipairs(objects) do addObject(objectSpec) end")
    lines.append("print('[ROBLOX AI VIDEO FACTORY] World generated:', folder:GetFullName(), 'Objects:', #objects)")
    lines.append("print('Review the map in Studio, then save the place or select the world folder and Save to File.')")
    return "\n".join(lines) + "\n"


def infer_scene_action(text):
    value = str(text or '').lower()
    rules = [
        (('run', 'runs', 'running', 'sprint', 'chase', 'escape'), 'run'),
        (('walk', 'walks', 'walking', 'approach', 'approaches', 'move toward'), 'walk'),
        (('jump', 'jumps', 'leap', 'leaps'), 'jump'),
        (('wave', 'waves', 'waving'), 'wave'),
        (('cheer', 'celebrate', 'celebrates', 'victory'), 'cheer'),
        (('fall', 'falls', 'trip', 'trips', 'collapse'), 'fall'),
        (('dodge', 'duck', 'avoid', 'sidestep'), 'dodge'),
        (('look', 'looks', 'notice', 'notices', 'turns around', 'stares'), 'look'),
        (('react', 'surprise', 'shocked', 'gasps', 'scared', 'afraid'), 'react'),
    ]
    for words, action in rules:
        if any(word in value for word in words):
            return action
    return 'idle'


def infer_camera_shot(text):
    value = str(text or '').lower().replace('-', '_').replace(' ', '_')
    if 'orbit' in value or '360' in value:
        return 'orbit'
    if 'over_shoulder' in value or 'shoulder' in value:
        return 'over_shoulder'
    if 'close' in value or 'portrait' in value:
        return 'closeup'
    if 'low' in value:
        return 'low_angle'
    if 'high' in value or 'top' in value or 'bird' in value:
        return 'high_angle'
    if 'track' in value or 'follow' in value:
        return 'tracking'
    if 'wide' in value or 'establish' in value:
        return 'wide'
    return 'medium'


def match_world_anchor(location, world_plan):
    objects = (world_plan or {}).get('objects', [])
    if not objects:
        return None
    stop = {'the','a','an','of','in','on','at','to','and','near','inside','outside','street','area','place','room'}
    def tokens(s):
        return {x for x in re.findall(r'[a-z0-9]+', str(s or '').lower()) if x not in stop and len(x) > 2}
    query = tokens(location)
    if not query:
        return None
    best, best_score = None, 0
    for obj in objects:
        if obj.get('kind') == 'spawn':
            continue
        names = tokens(obj.get('name','')) | tokens(obj.get('kind',''))
        score = len(query & names)
        if score > best_score:
            best, best_score = obj, score
    return best if best_score > 0 else None


def make_scene_director_plan(story, world_plan=None, character_records=None):
    raw_scenes = story.get('scenes', []) if isinstance(story, dict) else []
    if not isinstance(raw_scenes, list) or not raw_scenes:
        raise ValueError('Kịch bản không có danh sách scenes hợp lệ.')
    character_records = character_records or []
    by_name = {str(c.get('name','')).casefold(): c for c in character_records if c.get('name')}
    world_size = int((world_plan or {}).get('map_size', 400))
    bound = max(30, world_size / 2 - 25)
    scenes = []
    for index, raw in enumerate(raw_scenes, start=1):
        if not isinstance(raw, dict):
            continue
        original_names = raw.get('characters', [])
        if isinstance(original_names, str):
            original_names = [x.strip() for x in original_names.split(',') if x.strip()]
        names = []
        for value in original_names:
            value = str(value).strip()
            if not value:
                continue
            record = by_name.get(value.casefold())
            canonical = record.get('name') if record else value
            if canonical not in names:
                names.append(canonical)
        location = str(raw.get('location') or 'Main Story Area')[:120]
        anchor = match_world_anchor(location, world_plan)
        if anchor:
            tx, tz = float(anchor.get('x', 0)), float(anchor.get('z', 0))
            anchor_name = str(anchor.get('name',''))
        else:
            # A gentle zig-zag staging path keeps unanchored scenes inside the map footprint.
            tx = max(-bound, min(bound, ((index - 1) % 4 - 1.5) * 16))
            tz = max(-bound, min(bound, ((index - 1) // 4 % 4 - 1.5) * 18))
            anchor_name = 'Auto_Stage_Position'
        visual = str(raw.get('visual_action') or raw.get('action') or raw.get('description') or '')[:700]
        camera_text = str(raw.get('camera') or 'medium')
        try:
            duration = float(raw.get('duration_seconds', 6))
        except (TypeError, ValueError):
            duration = 6.0
        duration = max(2.0, min(45.0, duration))
        scenes.append({
            'scene_number': int(raw.get('scene_number') or raw.get('scene_id') or index),
            'location': location,
            'location_anchor': anchor_name,
            'duration_seconds': round(duration, 1),
            'characters': names,
            'model_names': [safe_filename(x) for x in names],
            'action': infer_scene_action(visual),
            'visual_action': visual,
            'facial_expression': str(raw.get('facial_expression') or 'Expressive, readable reaction')[:240],
            'camera': infer_camera_shot(camera_text),
            'camera_note': camera_text[:180],
            'on_screen_text': str(raw.get('on_screen_text') or '')[:160],
            'music_and_sfx': str(raw.get('music_and_sfx') or '')[:240],
            'transition': str(raw.get('transition') or 'cut')[:60],
            'target_x': round(max(-bound, min(bound, tx)), 1),
            'target_z': round(max(-bound, min(bound, tz)), 1),
            'director_note': 'Auto-directed from story action and selected world.'
        })
    if not scenes:
        raise ValueError('Không tìm thấy cảnh có dữ liệu để đạo diễn.')
    return {
        'title': str(story.get('title') or 'Roblox Story')[:120],
        'story_logline': str(story.get('logline') or '')[:500],
        'world_name': (world_plan or {}).get('name', ''),
        'world_size': world_size,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'scenes': scenes
    }


def apply_ai_scene_direction(base_plan, ai_data, world_plan=None):
    ai_scenes = ai_data.get('scenes', []) if isinstance(ai_data, dict) else []
    if not isinstance(ai_scenes, list):
        return base_plan
    allowed_actions = {'idle','walk','run','jump','wave','cheer','fall','dodge','look','react'}
    allowed_cameras = {'wide','medium','closeup','over_shoulder','low_angle','high_angle','tracking','orbit'}
    allowed_anchors = {str(o.get('name')): o for o in (world_plan or {}).get('objects', [])}
    output = []
    for index, base in enumerate(base_plan['scenes']):
        item = ai_scenes[index] if index < len(ai_scenes) and isinstance(ai_scenes[index], dict) else {}
        row = dict(base)
        action = str(item.get('action', row['action'])).lower()
        camera = str(item.get('camera', row['camera'])).lower()
        if action in allowed_actions:
            row['action'] = action
        if camera in allowed_cameras:
            row['camera'] = camera
        try:
            row['duration_seconds'] = round(max(2, min(45, float(item.get('duration_seconds', row['duration_seconds'])))), 1)
        except (TypeError, ValueError):
            pass
        anchor_name = str(item.get('target_anchor') or '')
        if anchor_name in allowed_anchors:
            anchor = allowed_anchors[anchor_name]
            row['location_anchor'] = anchor_name
            row['target_x'] = float(anchor.get('x', 0))
            row['target_z'] = float(anchor.get('z', 0))
        for key, limit in [('facial_expression',240),('director_note',500)]:
            if item.get(key):
                row[key] = str(item[key])[:limit]
        output.append(row)
    result = dict(base_plan)
    result['scenes'] = output
    result['direction_mode'] = 'AI Director'
    return result


def build_scene_director_server_source(plan):
    payload = json.dumps(plan, ensure_ascii=False, separators=(',', ':'))
    payload_lua = lua_string(payload)
    source = r'''-- ROBLOX AI VIDEO FACTORY 1.0 | SCENE DIRECTOR SERVER
-- Installed into ServerScriptService. Press Play (F5) in Studio to run the sequence.
local HttpService = game:GetService("HttpService")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local cameraEvent = ReplicatedStorage:WaitForChild("RAVF_SceneCameraEvent")
local cameraReady = ReplicatedStorage:WaitForChild("RAVF_SceneCameraReady")
local plan = HttpService:JSONDecode(__PLAN_JSON__)

local function findActor(modelName)
    if not modelName or modelName == "" then return nil end
    local direct = workspace:FindFirstChild(modelName)
    if direct and direct:IsA("Model") and direct:FindFirstChildOfClass("Humanoid") then return direct end
    for _, item in ipairs(workspace:GetDescendants()) do
        if item:IsA("Model") and item.Name == modelName and item:FindFirstChildOfClass("Humanoid") then
            return item
        end
    end
    return nil
end

local function getRoot(model)
    return model:FindFirstChild("HumanoidRootPart") or model.PrimaryPart or model:FindFirstChild("Torso")
end

local function getMotor(model, name)
    for _, item in ipairs(model:GetDescendants()) do
        if item:IsA("Motor6D") and item.Name == name then return item end
    end
    return nil
end

local function tweenMotor(motor, transform, duration)
    if not motor then return end
    local tween = TweenService:Create(motor, TweenInfo.new(0.22, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), {Transform = transform})
    tween:Play()
end

local function pose(model, action)
    local right = getMotor(model, "Right Shoulder")
    local left = getMotor(model, "Left Shoulder")
    local neck = getMotor(model, "Neck")
    if action == "wave" then
        tweenMotor(right, CFrame.Angles(0, 0, math.rad(-125)), 0.25)
    elseif action == "cheer" then
        tweenMotor(right, CFrame.Angles(0, 0, math.rad(-150)), 0.25)
        tweenMotor(left, CFrame.Angles(0, 0, math.rad(150)), 0.25)
    elseif action == "react" or action == "dodge" then
        tweenMotor(right, CFrame.Angles(math.rad(-25), 0, math.rad(-45)), 0.2)
        tweenMotor(left, CFrame.Angles(math.rad(-25), 0, math.rad(45)), 0.2)
        tweenMotor(neck, CFrame.Angles(math.rad(-12), 0, 0), 0.2)
    elseif action == "look" then
        tweenMotor(neck, CFrame.Angles(0, math.rad(28), 0), 0.2)
    else
        tweenMotor(right, CFrame.new(), 0.2)
        tweenMotor(left, CFrame.new(), 0.2)
        tweenMotor(neck, CFrame.new(), 0.2)
    end
end

local actorMoveTokens = {}
local function directActor(model, action, x, z, duration, sceneIndex)
    actorMoveTokens[model] = (actorMoveTokens[model] or 0) + 1
    local moveToken = actorMoveTokens[model]
    local humanoid = model:FindFirstChildOfClass("Humanoid")
    local root = getRoot(model)
    if not humanoid or not root then return end
    local target = Vector3.new(x, root.Position.Y, z)
    local stageX = x
    if action == "walk" or action == "run" then stageX = x - 5 end
    model:PivotTo(CFrame.new(stageX, math.max(3, root.Position.Y), z))
    root = getRoot(model)
    if (action == "walk" or action == "run") then
        humanoid.WalkSpeed = (action == "run") and 22 or 12
        local moveTarget = Vector3.new(x, root.Position.Y, z)
        humanoid:MoveTo(moveTarget)
        -- Humanoid:MoveTo can time out after 8 seconds; reissue while this shot remains active.
        task.spawn(function()
            local deadline = os.clock() + duration
            while humanoid.Parent and actorMoveTokens[model] == moveToken and os.clock() < deadline do
                task.wait(6.5)
                if actorMoveTokens[model] ~= moveToken or not humanoid.Parent then break end
                local currentRoot = getRoot(model)
                if currentRoot and (currentRoot.Position - moveTarget).Magnitude > 3 then
                    humanoid:MoveTo(moveTarget)
                else
                    break
                end
            end
        end)
    elseif action == "jump" then
        humanoid.Jump = true
    elseif action == "fall" then
        humanoid.PlatformStand = true
        task.delay(math.min(duration, 2.5), function()
            if humanoid and humanoid.Parent then humanoid.PlatformStand = false end
        end)
    elseif action == "wave" or action == "cheer" or action == "react" or action == "look" or action == "dodge" then
        pose(model, action)
    else
        pose(model, "idle")
    end
end

local readyPlayers = {}
cameraReady.OnServerEvent:Connect(function(player)
    readyPlayers[player] = true
end)
local readyDeadline = os.clock() + 15
repeat
    local allReady = #Players:GetPlayers() > 0
    for _, player in ipairs(Players:GetPlayers()) do
        if not readyPlayers[player] then allReady = false break end
    end
    if allReady then break end
    task.wait(0.2)
until os.clock() >= readyDeadline

local scenes = plan.scenes or {}
print("[RAVF Scene Director] Starting", #scenes, "scenes for", plan.title or "Untitled")
for index, scene in ipairs(scenes) do
    local names = scene.model_names or {}
    local targetName = names[1] or ""
    cameraEvent:FireAllClients({
        sceneNumber = scene.scene_number or index,
        camera = scene.camera or "medium",
        targetName = targetName,
        targetX = tonumber(scene.target_x) or 0,
        targetZ = tonumber(scene.target_z) or 0,
        duration = tonumber(scene.duration_seconds) or 6,
        reset = false
    })
    local actors = {}
    for _, modelName in ipairs(names) do
        local actor = findActor(modelName)
        if actor then table.insert(actors, actor) end
    end
    if #actors == 0 and #names > 0 then
        warn("[RAVF Scene Director] Actor not found in Workspace for scene " .. tostring(index) .. ": " .. table.concat(names, ", "))
    end
    local count = math.max(1, #actors)
    for actorIndex, actor in ipairs(actors) do
        local spread = (actorIndex - (count + 1) / 2) * 4
        directActor(actor, scene.action or "idle", (tonumber(scene.target_x) or 0) + spread, tonumber(scene.target_z) or 0, tonumber(scene.duration_seconds) or 6, index)
    end
    print(string.format("[RAVF Scene Director] Scene %d/%d | %s | %s | %ss", index, #scenes, tostring(scene.location), tostring(scene.action), tostring(scene.duration_seconds)))
    task.wait(math.max(2, tonumber(scene.duration_seconds) or 6))
end
cameraEvent:FireAllClients({reset = true})
print("[RAVF Scene Director] Sequence complete.")
'''
    return source.replace('__PLAN_JSON__', payload_lua)


def build_scene_director_client_source():
    return r'''-- ROBLOX AI VIDEO FACTORY 1.0 | SCENE DIRECTOR CAMERA CLIENT
-- Installed into StarterPlayerScripts. Camera choreography runs when the place is played.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local player = Players.LocalPlayer
local event = ReplicatedStorage:WaitForChild("RAVF_SceneCameraEvent")
local readyEvent = ReplicatedStorage:WaitForChild("RAVF_SceneCameraReady")
local camera = workspace.CurrentCamera

local function findActor(name)
    if not name or name == "" then return nil end
    local direct = workspace:FindFirstChild(name)
    if direct and direct:IsA("Model") then return direct end
    for _, item in ipairs(workspace:GetDescendants()) do
        if item:IsA("Model") and item.Name == name then return item end
    end
    return nil
end

local function getFocus(model, payload)
    if model then
        local root = model:FindFirstChild("HumanoidRootPart") or model.PrimaryPart or model:FindFirstChild("Head")
        if root then return root.Position + Vector3.new(0, 1.5, 0) end
    end
    return Vector3.new(tonumber(payload.targetX) or 0, 5, tonumber(payload.targetZ) or 0)
end

event.OnClientEvent:Connect(function(payload)
    if payload.reset then
        task.wait(0.25)
        camera.CameraType = Enum.CameraType.Custom
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if humanoid then camera.CameraSubject = humanoid end
        return
    end
    local model = findActor(payload.targetName)
    local focus = getFocus(model, payload)
    local mode = tostring(payload.camera or "medium")
    local offsets = {
        wide = Vector3.new(0, 10, 25),
        medium = Vector3.new(8, 5, 15),
        closeup = Vector3.new(0, 2.8, 7),
        over_shoulder = Vector3.new(4.5, 4.5, 8),
        low_angle = Vector3.new(0, 1.5, 13),
        high_angle = Vector3.new(0, 20, 12),
        tracking = Vector3.new(10, 6, 13),
        orbit = Vector3.new(14, 7, 0)
    }
    local offset = offsets[mode] or offsets.medium
    if mode == "orbit" then
        local theta = math.rad(((tonumber(payload.sceneNumber) or 1) * 67) % 360)
        offset = Vector3.new(math.cos(theta) * 14, 7, math.sin(theta) * 14)
    end
    local desired = CFrame.lookAt(focus + offset, focus)
    camera.CameraType = Enum.CameraType.Scriptable
    camera.Focus = CFrame.new(focus)
    local duration = math.max(0.35, math.min(2, (tonumber(payload.duration) or 6) * 0.22))
    TweenService:Create(camera, TweenInfo.new(duration, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), {CFrame = desired}):Play()
end)
readyEvent:FireServer()
'''


def build_scene_director_installer(server_source, client_source):
    server_lua = lua_string(server_source)
    client_lua = lua_string(client_source)
    return f'''-- ROBLOX AI VIDEO FACTORY 1.0 | SCENE DIRECTOR INSTALLER
-- Run this file once using Roblox Studio Command Bar or Studio CLI --task RunScript.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")
local starterScripts = StarterPlayer:WaitForChild("StarterPlayerScripts")

local event = ReplicatedStorage:FindFirstChild("RAVF_SceneCameraEvent")
if not event then
    event = Instance.new("RemoteEvent")
    event.Name = "RAVF_SceneCameraEvent"
    event.Parent = ReplicatedStorage
end
local readyEvent = ReplicatedStorage:FindFirstChild("RAVF_SceneCameraReady")
if not readyEvent then
    readyEvent = Instance.new("RemoteEvent")
    readyEvent.Name = "RAVF_SceneCameraReady"
    readyEvent.Parent = ReplicatedStorage
end

local oldServer = ServerScriptService:FindFirstChild("RAVF_SceneDirectorServer")
if oldServer then oldServer:Destroy() end
local serverScript = Instance.new("Script")
serverScript.Name = "RAVF_SceneDirectorServer"
serverScript.Source = {server_lua}
serverScript.Parent = ServerScriptService

local oldClient = starterScripts:FindFirstChild("RAVF_SceneDirectorCamera")
if oldClient then oldClient:Destroy() end
local cameraScript = Instance.new("LocalScript")
cameraScript.Name = "RAVF_SceneDirectorCamera"
cameraScript.Source = {client_lua}
cameraScript.Parent = starterScripts

print("[ROBLOX AI VIDEO FACTORY] Scene Director installed.")
print("Check that generated NPC models exist in Workspace, then press Play (F5).")
'''


def build_scene_director_launcher(studio_exe, place_file, installer_name):
    studio = str(studio_exe or '').strip()
    place = str(place_file or '').strip()
    lines = ['@echo off', 'setlocal', 'cd /d "%~dp0"']
    if studio:
        lines.append(f'set "STUDIO_EXE={studio}"')
    else:
        lines += [
            'set "STUDIO_EXE="',
            'for /d %%D in ("%LOCALAPPDATA%\\Roblox\\Versions\\version-*") do (',
            '  if exist "%%~fD\\RobloxStudioBeta.exe" set "STUDIO_EXE=%%~fD\\RobloxStudioBeta.exe"',
            ')'
        ]
    lines += [
        'if not defined STUDIO_EXE (echo Khong tim thay RobloxStudioBeta.exe. Hay cau hinh trong Dashboard > Cai dat.& pause & exit /b 1)',
        'if not exist "%STUDIO_EXE%" (echo Duong dan Roblox Studio khong ton tai: "%STUDIO_EXE%"& pause & exit /b 1)'
    ]
    if place:
        lines.append(f'"%STUDIO_EXE%" --task RunScript --localPlaceFile "{place}" --runScriptFile "%~dp0{installer_name}" --outputFile "%~dp0scene_director_install.log"')
    else:
        lines.append(f'"%STUDIO_EXE%" --task RunScript --runScriptFile "%~dp0{installer_name}" --outputFile "%~dp0scene_director_install.log"')
    lines += ['echo Installer finished. Open Studio and press Play (F5) to preview the sequence.', 'pause', 'endlocal']
    return '\r\n'.join(lines) + '\r\n'


def normalize_roblox_audio_id(value):
    # Accept a numeric Roblox audio asset ID or an rbxassetid:// URL.
    return re.sub(r"\D", "", str(value or ""))


def classify_sound_note(note, action=""):
    text = (str(note or "") + " " + str(action or "")).lower()
    if any(word in text for word in ("music", "score", "theme", "soundtrack", "nhạc")):
        return "Music"
    if any(word in text for word in ("ambience", "ambient", "wind", "rain", "forest", "city", "environment", "môi trường")):
        return "Ambience"
    if any(word in text for word in ("transition", "whoosh", "sweep", "stinger", "chuyển cảnh")):
        return "Transition"
    return "SFX"


def make_default_sound_cues(director_plan):
    # Create editable cue suggestions from the saved Director Plan; no audio is fabricated.
    cues = []
    cursor = 0.0
    for scene in director_plan.get("scenes", []):
        try:
            duration = max(1.0, float(scene.get("duration_seconds", 6)))
        except (TypeError, ValueError):
            duration = 6.0
        note = str(scene.get("music_and_sfx") or "").strip()
        action = str(scene.get("action") or "idle")
        if not note:
            action_notes = {
                "walk": "Footsteps, light movement Foley",
                "run": "Fast footsteps and movement Foley",
                "jump": "Short jump whoosh",
                "fall": "Soft cartoon impact, non-graphic",
                "cheer": "Short upbeat celebratory sting",
                "dodge": "Quick movement whoosh",
                "wave": "Light friendly movement cue",
                "react": "Short surprised reaction sting",
                "look": "Subtle suspense accent",
                "idle": "Low-level location ambience"
            }
            note = action_notes.get(action, "Low-level location ambience")
        cue_type = classify_sound_note(note, action)
        scene_number = int(scene.get("scene_number", len(cues)+1))
        cues.append({
            "cue_id": f"SC{scene_number:03d}_{len(cues)+1:03d}",
            "scene_number": scene_number,
            "cue_type": cue_type,
            "asset_name": "",
            "start_seconds": round(cursor, 2),
            "duration_seconds": round(duration, 2),
            "volume": 0.7 if cue_type in ("SFX", "Transition") else 0.35,
            "fade_in_seconds": 0.15 if cue_type in ("Music", "Ambience") else 0.03,
            "fade_out_seconds": 0.25 if cue_type in ("Music", "Ambience") else 0.08,
            "loop": cue_type in ("Music", "Ambience"),
            "target_model": "",
            "description": note[:240],
            "asset_id": "",
            "local_path": "",
            "rights_confirmed": False
        })
        cursor += duration
    return cues


def build_sound_studio_client_source(cues):
    # Build a LocalScript that schedules authorized Roblox audio assets on the client.
    roblox_cues = []
    for cue in cues:
        asset_id = normalize_roblox_audio_id(cue.get("asset_id", ""))
        if not asset_id:
            continue
        roblox_cues.append({
            "cue_id": str(cue.get("cue_id", "")),
            "asset_id": asset_id,
            "cue_type": str(cue.get("cue_type", "SFX")),
            "start_seconds": max(0.0, float(cue.get("start_seconds", 0) or 0)),
            "duration_seconds": max(0.1, float(cue.get("duration_seconds", 3) or 3)),
            "volume": max(0.0, min(10.0, float(cue.get("volume", 0.7) or 0))),
            "fade_in_seconds": max(0.0, float(cue.get("fade_in_seconds", 0) or 0)),
            "fade_out_seconds": max(0.0, float(cue.get("fade_out_seconds", 0) or 0)),
            "loop": bool(cue.get("loop", False)),
            "target_model": str(cue.get("target_model", "") or "")
        })
    payload = lua_string(json.dumps(roblox_cues, ensure_ascii=False, separators=(",", ":")))
    return r'''-- ROBLOX AI VIDEO FACTORY 1.0 | SOUND STUDIO CLIENT
-- LocalScript installed in StarterPlayerScripts.
-- Roblox audio assets must be uploaded/authorized for this experience.
local HttpService = game:GetService("HttpService")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local payload = HttpService:JSONDecode(__PAYLOAD__)

local function findSoundParent(modelName)
    if not modelName or modelName == "" then
        return SoundService
    end
    for _, item in ipairs(workspace:GetDescendants()) do
        if item:IsA("Model") and item.Name == modelName then
            local root = item:FindFirstChild("HumanoidRootPart") or item.PrimaryPart
            if root then return root end
        end
    end
    return SoundService
end

for index, cue in ipairs(payload) do
    task.delay(math.max(0, tonumber(cue.start_seconds) or 0), function()
        local sound = Instance.new("Sound")
        sound.Name = "RAVF_Sound_" .. tostring(cue.cue_id or index)
        sound.SoundId = "rbxassetid://" .. tostring(cue.asset_id)
        sound.Looped = cue.loop == true
        local targetVolume = math.clamp(tonumber(cue.volume) or 0.7, 0, 10)
        local fadeIn = math.max(0, tonumber(cue.fade_in_seconds) or 0)
        local fadeOut = math.max(0, tonumber(cue.fade_out_seconds) or 0)
        sound.Volume = (fadeIn > 0) and 0 or targetVolume
        sound.Parent = findSoundParent(cue.target_model)
        sound:Play()

        if fadeIn > 0 then
            TweenService:Create(sound, TweenInfo.new(fadeIn, Enum.EasingStyle.Linear), {
                Volume = targetVolume
            }):Play()
        end

        local duration = math.max(0.1, tonumber(cue.duration_seconds) or 3)
        local stopDelay = math.max(0, duration - math.min(fadeOut, duration))
        task.delay(stopDelay, function()
            if not sound.Parent then return end
            if fadeOut > 0 then
                local fade = TweenService:Create(sound, TweenInfo.new(math.min(fadeOut, duration), Enum.EasingStyle.Linear), {
                    Volume = 0
                })
                fade:Play()
                fade.Completed:Wait()
            end
            if sound.Parent then
                sound:Stop()
                sound:Destroy()
            end
        end)
    end)
end

print("[ROBLOX AI VIDEO FACTORY] Sound timeline scheduled:", #payload, "cues")
'''.replace("__PAYLOAD__", payload)


def build_sound_studio_installer(client_source):
    client_lua = lua_string(client_source)
    return f'''-- ROBLOX AI VIDEO FACTORY 1.0 | SOUND STUDIO INSTALLER
-- Run once in Roblox Studio using the Command Bar or Studio CLI --task RunScript.
local StarterPlayer = game:GetService("StarterPlayer")
local starterScripts = StarterPlayer:WaitForChild("StarterPlayerScripts")
local oldScript = starterScripts:FindFirstChild("RAVF_SoundStudioClient")
if oldScript then oldScript:Destroy() end

local soundScript = Instance.new("LocalScript")
soundScript.Name = "RAVF_SoundStudioClient"
soundScript.Source = {client_lua}
soundScript.Parent = starterScripts

print("[ROBLOX AI VIDEO FACTORY] Sound Studio installed.")
print("Verify audio asset permissions, then press Play (F5).")
'''


def build_ffmpeg_sound_mix_batch(cues, ffmpeg_exe, input_video, output_video, preserve_source_audio=False, source_audio_volume=0.7):
    # Build a Windows batch script that mixes local, rights-confirmed audio files.
    usable = []
    for cue in cues:
        local_path = str(cue.get("local_path", "") or "")
        if not local_path or not Path(local_path).is_file() or not cue.get("rights_confirmed"):
            continue
        usable.append(cue)
    if not usable:
        raise ValueError("Không có cue nào gắn file âm thanh cục bộ và được xác nhận quyền sử dụng.")

    def bat_value(value):
        return str(value or "").replace("%", "%%").replace('"', '""')

    ffmpeg = str(ffmpeg_exe or "").strip() or "ffmpeg"
    lines = [
        "@echo off",
        "setlocal",
        'cd /d "%~dp0"',
        f'set "FFMPEG_EXE={bat_value(ffmpeg)}"',
        f'set "INPUT_VIDEO={bat_value(input_video)}"',
        f'set "OUTPUT_VIDEO={bat_value(output_video)}"',
        'if not exist "%INPUT_VIDEO%" (echo Khong tim thay video dau vao: "%INPUT_VIDEO%"& pause & exit /b 1)',
        'where "%FFMPEG_EXE%" >nul 2>nul',
        'if errorlevel 1 if not exist "%FFMPEG_EXE%" (echo Khong tim thay FFmpeg. Hay them FFmpeg vao PATH hoac cau hinh duong dan trong Dashboard.& pause & exit /b 1)'
    ]
    input_args = ['-i "%INPUT_VIDEO%"']
    filter_parts = []
    labels = []
    if preserve_source_audio:
        source_volume = max(0.0, min(2.0, float(source_audio_volume)))
        filter_parts.append(f"[0:a:0]volume={source_volume:.3f}[orig]")
        labels.append("[orig]")
    for index, cue in enumerate(usable, start=1):
        if cue.get("loop"):
            input_args.append(f'-stream_loop -1 -i "{bat_value(cue["local_path"])}"')
        else:
            input_args.append(f'-i "{bat_value(cue["local_path"])}"')
        duration = max(0.1, float(cue.get("duration_seconds", 3) or 3))
        start_ms = max(0, int(float(cue.get("start_seconds", 0) or 0) * 1000))
        volume = max(0.0, min(10.0, float(cue.get("volume", 0.7) or 0)))
        fade_in = min(duration, max(0.0, float(cue.get("fade_in_seconds", 0) or 0)))
        fade_out = min(duration, max(0.0, float(cue.get("fade_out_seconds", 0) or 0)))
        filters = [
            f"atrim=duration={duration:.3f}",
            "asetpts=PTS-STARTPTS",
            f"volume={volume:.3f}"
        ]
        if fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in:.3f}")
        if fade_out > 0:
            filters.append(f"afade=t=out:st={max(0.0, duration-fade_out):.3f}:d={fade_out:.3f}")
        filters.append(f"adelay={start_ms}|{start_ms}")
        label = f"a{index}"
        filter_parts.append(f"[{index}:a]" + ",".join(filters) + f"[{label}]")
        labels.append(f"[{label}]")
    filter_parts.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=2,apad[aout]")
    filter_complex = ";".join(filter_parts)
    command = (
        '"%FFMPEG_EXE%" -y ' + " ".join(input_args) +
        f' -filter_complex "{filter_complex}" -map 0:v:0 -map "[aout]"'
        ' -c:v copy -c:a aac -b:a 192k -shortest "%OUTPUT_VIDEO%"'
    )
    lines += [command, 'if errorlevel 1 (echo Mix that bai.& pause & exit /b 1)', 'echo Da xuat video co am thanh: "%OUTPUT_VIDEO%"', 'pause', 'endlocal']
    return "\r\n".join(lines) + "\r\n"


def response_value(response, *names, default=None):
    """Read a field from obsws-python response objects or dictionaries."""
    for name in names:
        if isinstance(response, dict) and name in response:
            return response[name]
        if hasattr(response, name):
            return getattr(response, name)
    return default


def make_obs_client(config):
    """Create an obsws-python v5 request client. Caller owns connection lifetime."""
    import obsws_python as obs
    return obs.ReqClient(
        host=str(config.get("obs_host", "127.0.0.1") or "127.0.0.1"),
        port=int(config.get("obs_port", 4455) or 4455),
        password=str(config.get("obs_password", "") or ""),
        timeout=5
    )


def obs_scene_names(response):
    scenes = response_value(response, "scenes", default=[]) or []
    names = []
    for scene in scenes:
        name = response_value(scene, "sceneName", "scene_name", "name", default="")
        if name:
            names.append(str(name))
    return names


def safe_copy_recording(source_path, output_dir, prefix="OBS_Capture"):
    """Copy a just-finished OBS recording into the project's capture folder."""
    if not source_path:
        return ""
    source = Path(str(source_path)).expanduser()
    if not source.is_file():
        return ""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix or ".mkv"
    target = target_dir / f"{safe_filename(prefix)}{suffix}"
    counter = 2
    while target.exists():
        target = target_dir / f"{safe_filename(prefix)}_{counter}{suffix}"
        counter += 1
    shutil.copy2(source, target)
    return str(target)

defaults = {
    "openai_api_key": "",
    "image_provider": "Chưa kết nối",
    "roblox_place_path": "",
    "roblox_studio_exe": "",
    "obs_path": "",
    "ffmpeg_path": "",
    "output_dir": str(BASE / "exports"),
    "resolution": "1920x1080",
    "fps": 30
}
config = load_json(CONFIG, defaults)
projects = load_json(PROJECTS, [])

st.set_page_config(page_title="ROBLOX AI VIDEO FACTORY", page_icon="🎬", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1500px;}
.hero {padding: 1.4rem 1.6rem; border-radius: 14px; background: linear-gradient(110deg,#18243b,#273e62); color: white; margin-bottom: 1rem;}
.hero h1 {margin:0; font-size:2rem;}
.hero p {margin:.35rem 0 0 0; color:#d5e2f5;}
.small-muted {color: #8b95a7; font-size:.88rem;}
.module-card {border:1px solid rgba(128,128,128,.28); padding:1rem; border-radius:12px; min-height:120px;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎬 ROBLOX AI")
    st.caption("VIDEO FACTORY · VERSION 1.0")
    page = st.radio("ĐIỀU HƯỚNG", [
        "Tổng quan", "AI Story", "Character AI", "3D Model Builder", "World Builder",
        "Scene Director", "Sound Studio", "Video Editor", "Auto Publish", "Cài đặt"
    ])
    st.divider()
    st.caption("Bộ công cụ sản xuất Roblox story — các kết nối được cấu hình theo từng module.")

if page == "Tổng quan":
    st.markdown('<div class="hero"><h1>ROBLOX AI VIDEO FACTORY</h1><p>Trung tâm sản xuất câu chuyện Roblox cho khán giả quốc tế</p></div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    a.metric("Dự án", len(projects))
    b.metric("Module", "8")
    c.metric("Độ phân giải", config.get("resolution","1920x1080"))
    d.metric("Trạng thái", "Khởi tạo")
    st.subheader("Quy trình sản xuất")
    stages = [
        ("01","AI STORY","Kịch bản và phân cảnh","Đã tích hợp"),
        ("02","CHARACTER AI","Hồ sơ nhân vật nhất quán","Đã tích hợp"),
        ("03","3D MODEL BUILDER","Tạo rig nhân vật Roblox","Đã tích hợp"),
        ("04","WORLD BUILDER","Bản đồ và bối cảnh Roblox","Đã tích hợp"),
        ("05","SCENE DIRECTOR","Diễn xuất, camera, chuyển động","Đã tích hợp"),
        ("06","SOUND STUDIO","Nhạc nền và hiệu ứng","Đã tích hợp"),
        ("07","VIDEO FACTORY","Quay, dựng và xuất MP4","Đã tích hợp"),
        ("08","AUTO PUBLISH","Metadata và lịch xuất bản","Khung module")
    ]
    cols = st.columns(3)
    for i,(num,name,desc,status) in enumerate(stages):
        with cols[i%3]:
            st.markdown(f'<div class="module-card"><div class="small-muted">{num}</div><h3>{name}</h3><p>{desc}</p><span class="small-muted">{status}</span></div>', unsafe_allow_html=True)
        if i%3 == 2: st.write("")
    st.subheader("Tạo dự án mới")
    with st.form("new_project"):
        title = st.text_input("Tên dự án", placeholder="Ví dụ: Noob Survives 99 Nights")
        series = st.selectbox("Series", ["Zombie Survival","Noob Life","99 Nights","Rich vs Poor","Escape Story","Khác"])
        language = st.selectbox("Ngôn ngữ khán giả", ["English (US)","Tiếng Việt","Khác"])
        submitted = st.form_submit_button("＋ Tạo dự án", type="primary")
        if submitted:
            if not title.strip():
                st.error("Vui lòng nhập tên dự án.")
            else:
                projects.append({"title":title.strip(),"series":series,"language":language,"created_at":datetime.now().isoformat(timespec="minutes"),"status":"Ý tưởng"})
                save_json(PROJECTS, projects)
                st.success("Đã tạo dự án.")
                st.rerun()
    if projects:
        st.subheader("Dự án gần đây")
        st.dataframe(projects, use_container_width=True, hide_index=True)

elif page == "AI Story":
    st.title("🧠 AI STORY")
    st.write("Tạo câu chuyện Roblox bằng tiếng Anh Mỹ, chia cảnh và xuất JSON để chuyển sang các module sản xuất.")
    st.caption("Cần có OpenAI API key trong mục Cài đặt. API usage có thể phát sinh phí riêng.")

    with st.form("story_generator"):
        c1, c2 = st.columns(2)
        with c1:
            topic = st.text_input("Chủ đề / ý tưởng", placeholder="A poor Roblox Noob finds a secret bunker during a zombie outbreak")
            series = st.selectbox("Series", ["Zombie Survival","Noob Life","99 Nights","Rich vs Poor","Escape Story","Original Story"])
            audience = st.selectbox("Đối tượng khán giả", ["US kids & family-friendly gaming audience","Teen gaming audience","General Roblox audience"])
        with c2:
            duration = st.slider("Thời lượng mục tiêu (phút)", 1, 15, 5)
            scene_count = st.slider("Số cảnh", 10, 40, 24)
            tone = st.selectbox("Sắc thái", ["Funny + adventurous","Suspenseful","Emotional","Horror-lite (non-graphic)","Mixed"])
        premise = st.text_area("Chi tiết bắt buộc (không bắt buộc)", placeholder="Nhân vật chính, cú twist, kết thúc mong muốn...")
        generate = st.form_submit_button("✨ Tạo kịch bản bằng AI", type="primary")

    if generate:
        api_key = config.get("openai_api_key", "").strip()
        if not topic.strip():
            st.error("Hãy nhập chủ đề câu chuyện.")
        elif not api_key:
            st.error("Chưa có OpenAI API key. Hãy vào Cài đặt để thêm API key, sau đó quay lại đây.")
        else:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                system_prompt = """
You are a professional writer and storyboard director for original Roblox-style 3D animated stories.
Create original, family-friendly entertainment for a US audience. Do not use copyrighted characters,
existing Roblox creators' characters, or imitate a specific living creator. No voice-over is required:
use visual storytelling, expressive acting, music/SFX cues, and optional short on-screen text.
Return ONLY valid JSON. Use American English for all story content.
JSON schema:
{
 "title": string,
 "logline": string,
 "target_audience": string,
 "estimated_duration_minutes": number,
 "style_notes": string,
 "characters": [{"name":string,"role":string,"visual_description":string,"personality":string,"signature_expression":string}],
 "story_beats": [{"beat":string,"description":string}],
 "scenes": [{
   "scene_number": number,
   "location": string,
   "duration_seconds": number,
   "characters": [string],
   "visual_action": string,
   "facial_expression": string,
   "camera": string,
   "on_screen_text": string,
   "music_and_sfx": string,
   "transition": string
 }],
 "ending_hook": string,
 "thumbnail_concept": string,
 "youtube_title_options": [string],
 "youtube_description": string,
 "tags": [string]
}
Ensure exactly the requested number of scenes. Scene durations should approximately add up to the requested runtime.
Keep actions visually filmable in a Roblox-like 3D environment. Maintain character continuity.
"""
                user_prompt = f"""
Series: {series}
Story idea: {topic}
Target audience: {audience}
Tone: {tone}
Target runtime: {duration} minutes
Required scene count: exactly {scene_count}
Additional requirements: {premise or "None"}
Make the opening 5 seconds visually gripping. Include a clear setup, escalation, turning point,
climax, and satisfying ending with a hook for another episode when appropriate.
"""
                with st.spinner("AI đang viết cốt truyện và chia cảnh..."):
                    response = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.8
                    )
                    raw = response.choices[0].message.content
                    story_data = json.loads(raw)
                    story_data["project_series"] = series
                    story_data["created_at"] = datetime.now().isoformat(timespec="seconds")
                    out_dir = DATA / "stories"
                    out_dir.mkdir(exist_ok=True)
                    safe_title = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in story_data.get("title","roblox_story"))[:60]
                    out_file = out_dir / f"{safe_title or 'roblox_story'}.json"
                    out_file.write_text(json.dumps(story_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    st.session_state["generated_story"] = story_data
                    st.session_state["generated_story_path"] = str(out_file)
                st.success(f"Đã tạo kịch bản và lưu tại: {out_file}")
            except ImportError:
                st.error("Thiếu thư viện OpenAI. Đóng ứng dụng, chạy lại run_windows.bat để cài requirements mới.")
            except Exception as e:
                st.error(f"Không tạo được kịch bản: {e}")

    if "generated_story" in st.session_state:
        story = st.session_state["generated_story"]
        st.divider()
        st.subheader(story.get("title", "Generated Story"))
        st.write(story.get("logline", ""))
        tab1, tab2, tab3, tab4 = st.tabs(["Tổng quan", "Nhân vật", "Phân cảnh", "Xuất dữ liệu"])
        with tab1:
            st.write("**Style notes:**", story.get("style_notes", ""))
            st.write("**Story beats**")
            for beat in story.get("story_beats", []):
                st.markdown(f"- **{beat.get('beat','')}** — {beat.get('description','')}")
            st.write("**Ending hook:**", story.get("ending_hook", ""))
            st.write("**Thumbnail concept:**", story.get("thumbnail_concept", ""))
        with tab2:
            st.dataframe(story.get("characters", []), use_container_width=True, hide_index=True)
        with tab3:
            st.dataframe(story.get("scenes", []), use_container_width=True, hide_index=True)
        with tab4:
            st.download_button(
                "⬇️ Tải kịch bản JSON",
                data=json.dumps(story, ensure_ascii=False, indent=2),
                file_name="roblox_story.json",
                mime="application/json"
            )
            st.code(st.session_state.get("generated_story_path", ""), language="text")
            st.write("**YouTube title options**")
            for item in story.get("youtube_title_options", []):
                st.markdown(f"- {item}")
            st.write("**Description**")
            st.text(story.get("youtube_description", ""))
            st.write("**Tags**")
            st.write(", ".join(story.get("tags", [])))

elif page == "Character AI":
    st.title("👥 CHARACTER AI")
    st.write("Xây dựng Character Bible để giữ nhận diện nhân vật nhất quán giữa các tập và các cảnh.")
    st.caption("Có thể tạo hồ sơ thủ công hoặc dùng OpenAI API để đề xuất hồ sơ. Dùng 3D Model Builder để sinh rig Luau cho Roblox Studio.")

    chars = load_json(DATA/"characters.json", [])
    if not isinstance(chars, list):
        chars = []

    tab_create, tab_library, tab_export = st.tabs(["＋ Tạo nhân vật", "📚 Thư viện nhân vật", "📦 Xuất dữ liệu"])

    with tab_create:
        mode = st.radio("Cách tạo", ["Tạo thủ công", "AI đề xuất hồ sơ"], horizontal=True)
        if mode == "Tạo thủ công":
            with st.form("character_manual"):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("Tên nhân vật *", placeholder="Noob")
                    role = st.selectbox("Vai trò", ["Main hero","Sidekick","Villain","Mentor","Comic relief","Supporting character","Other"])
                    archetype = st.selectbox("Kiểu avatar", ["Classic Noob","Bacon Hair","Pro","Zombie","Custom Roblox avatar"])
                    body_type = st.selectbox("Tỷ lệ cơ thể", ["Classic blocky R6","Blocky R15","Stylized custom"])
                with c2:
                    primary_colors = st.text_input("Màu chủ đạo", placeholder="Yellow, blue, green")
                    outfit = st.text_input("Trang phục / phụ kiện", placeholder="Blue shirt, green pants, simple sneakers")
                    age_style = st.selectbox("Cách thể hiện", ["Childlike cartoon","Teen cartoon","Adult cartoon","Creature / monster"])
                    voice_note = st.text_input("Ghi chú âm thanh (nếu cần)", placeholder="Không dùng voice-over; chỉ biểu cảm và SFX")
                appearance = st.text_area("Mô tả ngoại hình cố định *", placeholder="Blocky yellow head, simple smiling face, bright blue torso...")
                personality = st.text_area("Tính cách", placeholder="Optimistic, clumsy, brave when friends are in danger...")
                expressions = st.text_input("Biểu cảm đặc trưng", placeholder="Wide-eyed surprise; goofy grin; nervous sweat")
                animation = st.text_area("Chuyển động / dáng đi đặc trưng", placeholder="Bouncy walk, exaggerated stumble, quick celebratory jump")
                props = st.text_input("Đạo cụ nhận diện", placeholder="Small backpack, flashlight")
                negative = st.text_area("Không được thay đổi", placeholder="Never change head shape, shirt color, face style, or signature backpack.")
                if st.form_submit_button("Lưu nhân vật", type="primary"):
                    if not name.strip() or not appearance.strip():
                        st.error("Tên và mô tả ngoại hình là bắt buộc.")
                    elif any(c.get("name","").casefold() == name.strip().casefold() for c in chars):
                        st.error("Đã có nhân vật cùng tên. Hãy dùng tên khác hoặc chỉnh sửa hồ sơ trong thư viện.")
                    else:
                        char_id = "char_" + "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip()).strip("_")
                        record = {
                            "character_id": char_id, "name": name.strip(), "role": role,
                            "avatar_archetype": archetype, "body_type": body_type,
                            "primary_colors": primary_colors, "outfit_accessories": outfit,
                            "presentation_style": age_style, "audio_notes": voice_note,
                            "visual_description": appearance, "personality": personality,
                            "signature_expressions": expressions, "signature_movement": animation,
                            "recognition_props": props, "continuity_rules": negative,
                            "created_at": datetime.now().isoformat(timespec="seconds")
                        }
                        chars.append(record)
                        save_json(DATA/"characters.json", chars)
                        st.success(f"Đã lưu hồ sơ {name.strip()}.")
                        st.rerun()
        else:
            with st.form("character_ai"):
                concept = st.text_area("Mô tả nhân vật", placeholder="A funny but brave classic Roblox Noob who is afraid of zombies but never abandons friends.")
                role_ai = st.selectbox("Vai trò", ["Main hero","Sidekick","Villain","Mentor","Comic relief","Supporting character"])
                style_ai = st.selectbox("Phong cách hình ảnh", ["Classic blocky Roblox","Colorful cartoon Roblox","Cinematic stylized Roblox"])
                if st.form_submit_button("✨ AI đề xuất Character Bible", type="primary"):
                    api_key = config.get("openai_api_key", "").strip()
                    if not concept.strip():
                        st.error("Hãy mô tả nhân vật.")
                    elif not api_key:
                        st.error("Chưa có API key. Vào Cài đặt để cấu hình.")
                    else:
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=api_key)
                            sys_msg = """You are a character designer for original family-friendly Roblox-style 3D stories.
Return ONLY valid JSON in American English with keys:
name, role, avatar_archetype, body_type, primary_colors, outfit_accessories,
visual_description, personality, signature_expressions, signature_movement,
recognition_props, continuity_rules, image_prompt.
Make the design easy to reproduce in a block-based 3D environment. Be specific and consistent.
Do not use copyrighted characters or imitate a specific creator. Keep the design original."""
                            with st.spinner("AI đang thiết kế hồ sơ nhân vật..."):
                                result = client.chat.completions.create(
                                    model="gpt-4.1-mini",
                                    response_format={"type":"json_object"},
                                    messages=[{"role":"system","content":sys_msg},
                                              {"role":"user","content":f"Character concept: {concept}\nRole: {role_ai}\nVisual style: {style_ai}"}],
                                    temperature=0.7
                                )
                                proposed = json.loads(result.choices[0].message.content)
                                st.session_state["character_proposal"] = proposed
                        except Exception as e:
                            st.error(f"Không tạo được đề xuất: {e}")

            if "character_proposal" in st.session_state:
                proposed = st.session_state["character_proposal"]
                st.subheader("Đề xuất của AI — kiểm tra trước khi lưu")
                st.json(proposed)
                proposed_name = proposed.get("name","").strip()
                if st.button("Lưu đề xuất vào thư viện", type="primary"):
                    if not proposed_name:
                        st.error("AI chưa trả về tên nhân vật hợp lệ.")
                    elif any(c.get("name","").casefold() == proposed_name.casefold() for c in chars):
                        st.error("Tên nhân vật đã tồn tại. Hãy chỉnh tên trong đề xuất rồi tạo lại.")
                    else:
                        record = dict(proposed)
                        record["character_id"] = "char_" + "".join(ch.lower() if ch.isalnum() else "_" for ch in proposed_name).strip("_")
                        record["created_at"] = datetime.now().isoformat(timespec="seconds")
                        chars.append(record)
                        save_json(DATA/"characters.json", chars)
                        del st.session_state["character_proposal"]
                        st.success("Đã lưu Character Bible.")
                        st.rerun()

    with tab_library:
        if not chars:
            st.info("Chưa có nhân vật. Tạo nhân vật đầu tiên ở tab Tạo nhân vật.")
        else:
            selected_name = st.selectbox("Chọn nhân vật để xem / chỉnh sửa", [c.get("name","Unnamed") for c in chars])
            selected_index = next(i for i,c in enumerate(chars) if c.get("name","Unnamed") == selected_name)
            selected = chars[selected_index]
            st.json(selected)
            with st.expander("Chỉnh sửa nhanh"):
                edit_name = st.text_input("Tên", value=selected.get("name",""), key="edit_char_name")
                edit_appearance = st.text_area("Mô tả ngoại hình", value=selected.get("visual_description",""), key="edit_char_appearance")
                edit_personality = st.text_area("Tính cách", value=selected.get("personality",""), key="edit_char_personality")
                edit_rules = st.text_area("Quy tắc nhất quán", value=selected.get("continuity_rules",""), key="edit_char_rules")
                if st.button("Lưu chỉnh sửa"):
                    if edit_name.strip():
                        selected["name"] = edit_name.strip()
                        selected["visual_description"] = edit_appearance
                        selected["personality"] = edit_personality
                        selected["continuity_rules"] = edit_rules
                        chars[selected_index] = selected
                        save_json(DATA/"characters.json", chars)
                        st.success("Đã cập nhật hồ sơ.")
                        st.rerun()
            if st.button("Xóa nhân vật đang chọn", type="secondary"):
                chars.pop(selected_index)
                save_json(DATA/"characters.json", chars)
                st.rerun()

    with tab_export:
        if chars:
            st.write(f"Đã lưu **{len(chars)}** hồ sơ nhân vật.")
            st.download_button("⬇️ Tải Character Bible JSON", data=json.dumps(chars, ensure_ascii=False, indent=2),
                               file_name="roblox_character_bible.json", mime="application/json")
            st.dataframe([{"Tên":c.get("name"),"Vai trò":c.get("role"),"ID":c.get("character_id")} for c in chars],
                         use_container_width=True, hide_index=True)
        else:
            st.info("Thư viện hiện chưa có dữ liệu để xuất.")

elif page == "3D Model Builder":
    st.title("🧱 3D MODEL BUILDER")
    st.write("Tự dựng nhân vật blocky R6-style từ Character Bible và sinh script Luau có thể chạy trong Roblox Studio.")
    st.caption("Bản tích hợp tạo model bằng Parts + Humanoid + Motor6D. Không cần AI video hoặc dịch vụ dựng mesh bên ngoài.")
    characters = load_json(DATA / "characters.json", [])
    if not characters:
        st.warning("Chưa có Character Bible. Hãy tạo ít nhất một nhân vật trong mục Character AI trước.")
    else:
        char_names = [c.get("name", "Unnamed") for c in characters]
        chosen_name = st.selectbox("Chọn nhân vật", char_names)
        character = next(c for c in characters if c.get("name", "Unnamed") == chosen_name)
        st.markdown("**Hồ sơ đang chọn**")
        left, right = st.columns([1, 2])
        with left:
            st.write(f"**Vai trò:** {character.get('role', '—')}")
            st.write(f"**Avatar:** {character.get('avatar_archetype', '—')}")
            st.write(f"**ID:** `{character.get('character_id', '—')}`")
        with right:
            st.write(character.get("visual_description", "Chưa có mô tả ngoại hình."))

        archetype = (character.get("avatar_archetype", "") + " " + character.get("visual_description", "")).lower()
        if "zombie" in archetype:
            auto_palette = {"head":"#4B974B", "torso":"#3C5F3A", "arms":"#4B974B", "legs":"#333333"}
        elif "bacon" in archetype:
            auto_palette = {"head":"#FFCC99", "torso":"#A3A2A5", "arms":"#FFCC99", "legs":"#0D69AC"}
        elif "pro" in archetype:
            auto_palette = {"head":"#FFCC99", "torso":"#1B2A35", "arms":"#1B2A35", "legs":"#333333"}
        else:
            auto_palette = {"head":"#F5CD30", "torso":"#0D69AC", "arms":"#F5CD30", "legs":"#4B974B"}

        with st.form("build_3d_character"):
            st.subheader("Thiết lập model")
            palette_mode = st.radio("Bảng màu", ["Tự nhận diện từ Character Bible", "Classic Noob", "Bacon", "Zombie", "Tùy chỉnh"], horizontal=True)
            if palette_mode == "Classic Noob":
                palette = {"head":"#F5CD30", "torso":"#0D69AC", "arms":"#F5CD30", "legs":"#4B974B"}
            elif palette_mode == "Bacon":
                palette = {"head":"#FFCC99", "torso":"#A3A2A5", "arms":"#FFCC99", "legs":"#0D69AC"}
            elif palette_mode == "Zombie":
                palette = {"head":"#4B974B", "torso":"#3C5F3A", "arms":"#4B974B", "legs":"#333333"}
            else:
                palette = auto_palette.copy()
            if palette_mode == "Tùy chỉnh":
                p1, p2, p3, p4 = st.columns(4)
                palette["head"] = p1.color_picker("Đầu", palette["head"])
                palette["torso"] = p2.color_picker("Thân", palette["torso"])
                palette["arms"] = p3.color_picker("Tay", palette["arms"])
                palette["legs"] = p4.color_picker("Chân", palette["legs"])
            else:
                st.write("Màu tự chọn:", ", ".join(f"{k}: {v}" for k,v in palette.items()))

            st.subheader("Chi tiết bổ sung")
            b1, b2, b3 = st.columns(3)
            with b1:
                add_hair = st.checkbox("Tạo tóc block tự động", value="bacon" in archetype or "pro" in archetype)
                hair_color = st.color_picker("Màu tóc", "#7D4126")
            with b2:
                props_text = (character.get("recognition_props", "") + " " + character.get("outfit_accessories", "")).lower()
                add_backpack = st.checkbox("Thêm ba lô block", value="backpack" in props_text)
                spawn_y = st.number_input("Độ cao xuất hiện (3 = đặt chân gần mặt Baseplate)", min_value=2.0, max_value=100.0, value=3.0, step=1.0)
            with b3:
                shirt_id = st.text_input("Shirt template ID (không bắt buộc)", placeholder="Chỉ nhập số asset ID")
                pants_id = st.text_input("Pants template ID (không bắt buộc)", placeholder="Chỉ nhập số asset ID")
                face_id = st.text_input("Face decal ID (không bắt buộc)", placeholder="Để trống dùng face mặc định")
            generate_model = st.form_submit_button("⚙️ Tạo model 3D Roblox + Luau", type="primary")

        if generate_model:
            try:
                lua_script = build_roblox_r6_script(character, palette, spawn_y, add_hair, hair_color, add_backpack, shirt_id, pants_id, face_id)
                export_dir = BASE / "exports" / "roblox_models"
                export_dir.mkdir(parents=True, exist_ok=True)
                base_name = safe_filename(character.get("name", "RobloxCharacter"))
                lua_path = export_dir / f"{base_name}_R6.lua"
                bat_path = export_dir / f"{base_name}_OpenInStudio.bat"
                lua_path.write_text(lua_script, encoding="utf-8")
                bat_path.write_text(make_studio_launcher(config.get("roblox_studio_exe", ""), config.get("roblox_place_path", ""), lua_path.name), encoding="utf-8")
                st.session_state["generated_roblox_lua"] = lua_script
                st.session_state["generated_roblox_lua_name"] = lua_path.name
                st.session_state["generated_roblox_bat"] = bat_path.read_text(encoding="utf-8")
                st.session_state["generated_roblox_model_path"] = str(lua_path)
                st.success(f"Đã sinh script model: {lua_path}")
            except Exception as e:
                st.error(f"Không tạo được script model: {e}")

        if "generated_roblox_lua" in st.session_state:
            st.divider()
            st.subheader("Model Luau đã sẵn sàng")
            st.write("Tải script và launcher. Chạy launcher để Roblox Studio mở place và thực thi script; hoặc mở script trong Studio và chạy thủ công.")
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("⬇️ Tải script Luau (.lua)", data=st.session_state["generated_roblox_lua"],
                                   file_name=st.session_state["generated_roblox_lua_name"], mime="text/plain")
            with d2:
                st.download_button("⬇️ Tải launcher Windows (.bat)", data=st.session_state["generated_roblox_bat"],
                                   file_name=st.session_state["generated_roblox_lua_name"].replace(".lua", "_OpenInStudio.bat"), mime="text/plain")
            st.code(st.session_state["generated_roblox_lua"], language="lua")
            with st.expander("Hướng dẫn lưu thành file model .rbxm"):
                st.markdown("""
1. Chạy file `*_OpenInStudio.bat` (hoặc mở Roblox Studio và chạy script trong Command Bar / Script).
2. Trong Explorer, mở `Workspace` và chọn model vừa tạo.
3. Nhấp chuột phải model → **Save to File…** để lưu thành `.rbxm`.
4. Có thể kéo file `.rbxm` vào place khác hoặc dùng lại trong các dự án của bạn.

Model hiện là rig blocky R6-style với các Parts và Motor6D. Tóc/ba lô là hình khối cơ bản; để có ngoại hình chi tiết hơn, thay chúng bằng accessory/mesh asset mà bạn có quyền sử dụng.
""")

elif page == "World Builder":
    st.title("🌍 WORLD BUILDER AI")
    st.write("Thiết kế bản đồ theo chủ đề, tạo landmark và sinh mã Luau để Roblox Studio dựng môi trường 3D có thể chỉnh sửa.")
    st.caption("Chế độ theo mẫu hoạt động không cần API. Chế độ AI dùng OpenAI API để đề xuất bố cục; map vẫn được tạo bằng Parts trong Roblox Studio.")

    worlds = load_json(DATA / "worlds.json", [])
    if not isinstance(worlds, list):
        worlds = []

    with st.form("world_builder_form"):
        mode = st.radio("Phương thức thiết kế", ["Theo mẫu có sẵn", "AI đề xuất bố cục"], horizontal=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            world_name = st.text_input("Tên thế giới *", placeholder="Zombie Forest Outpost")
            environment = st.selectbox("Loại môi trường", ["Thành phố", "Rừng", "Đảo", "Trường học", "Hầm ngầm", "Thế giới giả tưởng"])
        with c2:
            mood = st.selectbox("Ánh sáng / không khí", ["Ban ngày", "Hoàng hôn", "Ban đêm", "U ám", "Kinh dị"])
            map_size = st.selectbox("Kích thước bản đồ", [300, 400, 600], index=1, format_func=lambda x: f"{x} × {x} studs")
        with c3:
            building_count = st.slider("Số công trình", 1, 10, 5)
            tree_count = st.slider("Số cây / vật cản thiên nhiên", 0, 40, 12)
            prop_count = st.slider("Số đạo cụ / vật thể phụ", 0, 30, 8)
        seed = st.number_input("Seed bố cục (cùng seed = cùng bản đồ mẫu)", min_value=1, max_value=999999, value=24031, step=1)
        notes = st.text_area("Mô tả cốt truyện / địa điểm bắt buộc", placeholder="Một trạm trú ẩn bỏ hoang, cổng thoát ở phía đông, đường ray bị chặn...")
        submit_world = st.form_submit_button("🗺️ Thiết kế bản đồ và sinh Luau", type="primary")

    if submit_world:
        if not world_name.strip():
            st.error("Vui lòng nhập tên thế giới.")
        else:
            base_plan = make_world_template(world_name, environment, mood, int(map_size), building_count, tree_count, prop_count, int(seed), notes)
            try:
                if mode == "AI đề xuất bố cục":
                    api_key = config.get("openai_api_key", "").strip()
                    if not api_key:
                        raise ValueError("Chưa có OpenAI API key. Hãy vào Cài đặt hoặc chọn chế độ Theo mẫu có sẵn.")
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    half = int(map_size / 2 - 18)
                    system_prompt = """You are a professional level designer for original, family-friendly Roblox 3D story maps.
Return ONLY valid JSON with keys: description (string), objects (array).
Each object must have: kind, name, x, z, w, d, h, color, material, rotation.
Allowed kind values: building, tower, tree, rock, lamp, fence, crate, spawn, crystal, bush, road.
Allowed materials: Grass, Ground, Sand, Concrete, Brick, Wood, WoodPlanks, Slate, Rock, Metal, Asphalt, Neon, Glass, Sandstone.
Coordinates are studs relative to map center. Keep x and z between -MAP_HALF and MAP_HALF.
Use compact readable names. Objects should make a playable, navigable story environment with a clear route and visual landmarks.
Do not add code, scripts, external asset ids, or instructions. Use original designs only."""
                    system_prompt = system_prompt.replace("MAP_HALF", str(half))
                    user_prompt = f"""Design a {environment} environment named {world_name}.
Mood: {mood}. Map footprint: {map_size} by {map_size} studs.
Requested object counts approximately: {building_count} buildings/towers, {tree_count} trees/natural obstacles, {prop_count} props.
Story and landmark requirements: {notes or 'Create a clear start area, objective landmark, route, and exit or climax area.'}
Return about 18 to 55 useful objects, including at least one spawn object. Use only the schema and allowed values."""
                    with st.spinner("AI đang thiết kế layout và landmark..."):
                        response = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            response_format={"type": "json_object"},
                            messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                            temperature=0.7
                        )
                        ai_data = json.loads(response.choices[0].message.content)
                    world_plan = normalize_ai_world_plan(ai_data, base_plan)
                else:
                    world_plan = base_plan
                world_plan["created_at"] = datetime.now().isoformat(timespec="seconds")
                lua_script = build_roblox_world_script(world_plan)
                safe_name = safe_filename(world_plan["name"])
                output_dir = BASE / "exports" / "roblox_worlds"
                output_dir.mkdir(parents=True, exist_ok=True)
                json_path = DATA / "worlds" / f"{safe_name}.json"
                json_path.parent.mkdir(parents=True, exist_ok=True)
                lua_path = output_dir / f"{safe_name}_BuildWorld.lua"
                bat_path = output_dir / f"{safe_name}_OpenInStudio.bat"
                json_path.write_text(json.dumps(world_plan, ensure_ascii=False, indent=2), encoding="utf-8")
                lua_path.write_text(lua_script, encoding="utf-8")
                bat_path.write_text(make_studio_launcher(config.get("roblox_studio_exe", ""), config.get("roblox_place_path", ""), lua_path.name), encoding="utf-8")
                worlds = [w for w in worlds if w.get("name") != world_plan["name"]]
                worlds.append({"name": world_plan["name"], "environment": environment, "mood": mood,
                               "map_size": int(map_size), "object_count": len(world_plan["objects"]),
                               "json_path": str(json_path), "lua_path": str(lua_path), "created_at": world_plan["created_at"]})
                save_json(DATA / "worlds.json", worlds)
                st.session_state["generated_world_plan"] = world_plan
                st.session_state["generated_world_lua"] = lua_script
                st.session_state["generated_world_bat"] = bat_path.read_text(encoding="utf-8")
                st.session_state["generated_world_paths"] = {"json":str(json_path),"lua":str(lua_path),"bat":str(bat_path)}
                st.success(f"Đã tạo thiết kế bản đồ và script Luau: {lua_path}")
            except Exception as exc:
                st.error(f"Không thể tạo bản đồ: {exc}")

    if "generated_world_plan" in st.session_state:
        plan = st.session_state["generated_world_plan"]
        st.divider()
        st.subheader(f"Bản đồ: {plan.get('name','Roblox World')}")
        st.write(plan.get("description", ""))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kích thước", f"{plan.get('map_size',0)} × {plan.get('map_size',0)}")
        m2.metric("Vật thể", len(plan.get("objects", [])))
        m3.metric("Môi trường", plan.get("environment", "—"))
        m4.metric("Ánh sáng", plan.get("mood", "—"))
        world_objects = plan.get("objects", [])
        st.dataframe([{"Tên":o.get("name"),"Loại":o.get("kind"),"X":o.get("x"),"Z":o.get("z"),"Kích thước":f"{o.get('w')} × {o.get('d')} × {o.get('h')}"} for o in world_objects], use_container_width=True, hide_index=True)
        paths = st.session_state.get("generated_world_paths", {})
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("⬇️ Tải script Luau", data=st.session_state["generated_world_lua"],
                               file_name=f"{safe_filename(plan.get('name'))}_BuildWorld.lua", mime="text/plain")
        with d2:
            st.download_button("⬇️ Tải launcher Windows", data=st.session_state["generated_world_bat"],
                               file_name=f"{safe_filename(plan.get('name'))}_OpenInStudio.bat", mime="text/plain")
        with d3:
            st.download_button("⬇️ Tải World Plan JSON", data=json.dumps(plan, ensure_ascii=False, indent=2),
                               file_name=f"{safe_filename(plan.get('name'))}_WorldPlan.json", mime="application/json")
        with st.expander("Xem mã Luau được sinh"):
            st.code(st.session_state["generated_world_lua"], language="lua")
        with st.expander("Hướng dẫn đưa map vào Roblox Studio"):
            st.markdown("""
1. Vào **Cài đặt** và nhập đường dẫn `RobloxStudioBeta.exe` nếu launcher không tự tìm thấy Studio.
2. Có thể chọn file place `.rbxl/.rbxlx` trong Cài đặt; nếu bỏ trống, Studio sẽ chạy script trên một place mặc định.
3. Chạy file `*_OpenInStudio.bat` hoặc mở Roblox Studio, mở tab **View → Command Bar**, dán nội dung file `.lua` và nhấn Enter.
4. Sau khi map được tạo, kiểm tra Workspace, vị trí spawn và các va chạm; điều chỉnh thủ công nếu cần.
5. Lưu place (`.rbxl`) hoặc chọn folder thế giới trong Workspace → **Save to File…** để xuất `.rbxm`.

**Giới hạn:** Bản này sinh map block-based bằng Roblox Parts, không tải mesh/asset trả phí hoặc tự publish lên Roblox. Chế độ AI tạo đề xuất bố cục; bạn nên kiểm tra đường đi, kích thước và khả năng chơi trước khi dùng để quay phim.
""")

    if worlds:
        st.divider()
        st.subheader("Thư viện thế giới đã tạo")
        st.dataframe(worlds, use_container_width=True, hide_index=True)


elif page == "Scene Director":
    st.title("🎬 SCENE DIRECTOR AI")
    st.write("Đọc kịch bản, phối hợp nhân vật và bản đồ, rồi tạo shot list + script Luau để diễn xuất và điều khiển camera trong Roblox Studio.")
    st.caption("Bộ điều khiển dùng Humanoid/pose Motor6D cho các NPC R6-style đã tạo. Camera được điều khiển bằng LocalScript khi bạn nhấn Play trong Studio.")
    st.warning("Trước khi cài Scene Director, hãy lưu place có sẵn map + NPC thành .rbxl/.rbxlx và khai báo đường dẫn đó trong Cài đặt. Nếu không khai báo, Roblox Studio CLI sẽ mở Baseplate mặc định thay vì place đang làm.")

    story_dir = DATA / "stories"
    story_files = sorted(story_dir.glob("*.json")) if story_dir.exists() else []
    char_records = load_json(DATA / "characters.json", [])
    if not isinstance(char_records, list):
        char_records = []
    world_dir = DATA / "worlds"
    world_files = sorted(world_dir.glob("*.json")) if world_dir.exists() else []

    with st.form("scene_director_form"):
        st.subheader("01 · Chọn tài nguyên đầu vào")
        source_labels = [f"{p.stem} ({p.name})" for p in story_files]
        source_map = {label: path for label, path in zip(source_labels, story_files)}
        selected_story = st.selectbox("Kịch bản đã lưu", ["— Chọn kịch bản —"] + source_labels)
        st.caption("Bạn cũng có thể tải JSON ở bên dưới sau khi chọn file; file tải lên sẽ được ưu tiên.")
        selected_world_label = st.selectbox("Bản đồ Roblox (tùy chọn)", ["Không gắn bản đồ"] + [p.stem for p in world_files])
        director_mode = st.radio("Chế độ đạo diễn", ["Tự động từ kịch bản", "AI đạo diễn nâng cao"], horizontal=True)
        if char_records:
            st.write(f"Character Bible: **{len(char_records)}** nhân vật đã lưu")
        else:
            st.warning("Chưa có Character Bible. Hãy tạo model NPC trong 3D Model Builder và đặt chúng trong Workspace trước khi chạy cảnh.")
        create_plan = st.form_submit_button("🎥 Phân cảnh và tạo Director Plan", type="primary")

    uploaded_story = st.file_uploader("Hoặc tải kịch bản JSON", type=["json"], key="director_story_upload")
    if create_plan:
        try:
            if uploaded_story is not None:
                story_data = json.loads(uploaded_story.getvalue().decode("utf-8-sig"))
            elif selected_story != "— Chọn kịch bản —":
                story_data = load_json(source_map[selected_story], None)
            elif "generated_story" in st.session_state:
                story_data = st.session_state["generated_story"]
            else:
                raise ValueError("Hãy chọn một kịch bản đã lưu, tải JSON lên hoặc tạo kịch bản trong AI Story trước.")
            if not isinstance(story_data, dict):
                raise ValueError("File kịch bản JSON không hợp lệ.")
            world_plan = None
            if selected_world_label != "Không gắn bản đồ":
                world_path = next((p for p in world_files if p.stem == selected_world_label), None)
                world_plan = load_json(world_path, None) if world_path else None
            director_plan = make_scene_director_plan(story_data, world_plan, char_records)
            if director_mode == "AI đạo diễn nâng cao":
                api_key = config.get("openai_api_key", "").strip()
                if not api_key:
                    raise ValueError("Chưa có OpenAI API key. Vào Cài đặt hoặc chọn Tự động từ kịch bản.")
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                anchor_names = [str(o.get("name")) for o in (world_plan or {}).get("objects", [])[:80]]
                prompt_system = """You are a film director for original family-friendly Roblox-style 3D stories. Return ONLY valid JSON: {\"scenes\":[...]}. For every input scene return scene_number, action, camera, duration_seconds, target_anchor, facial_expression, director_note. action must be one of idle, walk, run, jump, wave, cheer, fall, dodge, look, react. camera must be one of wide, medium, closeup, over_shoulder, low_angle, high_angle, tracking, orbit. Only use target_anchor names from the supplied allowed anchor list; use empty string if no suitable anchor. Preserve scene order and make directions visually filmable with blocky R6 NPCs. Keep action family-friendly and non-graphic. Do not return code."""
                prompt_user = json.dumps({"story_title": director_plan["title"], "scenes": director_plan["scenes"], "allowed_anchors": anchor_names}, ensure_ascii=False)
                with st.spinner("AI đang đạo diễn từng cảnh..."):
                    response = client.chat.completions.create(
                        model="gpt-4.1-mini", response_format={"type":"json_object"},
                        messages=[{"role":"system","content":prompt_system},{"role":"user","content":prompt_user}],
                        temperature=0.55
                    )
                    ai_direction = json.loads(response.choices[0].message.content)
                director_plan = apply_ai_scene_direction(director_plan, ai_direction, world_plan)
            else:
                director_plan["direction_mode"] = "Auto Director"
            director_plan["world_name"] = (world_plan or {}).get("name", "")
            st.session_state["scene_director_plan"] = director_plan
            st.session_state["scene_director_world"] = world_plan or {}
            st.session_state.pop("scene_director_files", None)
            st.session_state.pop("scene_director_installer_source", None)
            st.session_state.pop("scene_director_server_source", None)
            st.session_state.pop("scene_director_client_source", None)
            st.success(f"Đã đạo diễn {len(director_plan['scenes'])} cảnh.")
        except Exception as exc:
            st.error(f"Không thể tạo Director Plan: {exc}")

    if "scene_director_plan" in st.session_state:
        director_plan = st.session_state["scene_director_plan"]
        st.divider()
        st.subheader(f"02 · Director Plan — {director_plan.get('title','Roblox Story')}")
        total_seconds = sum(float(s.get("duration_seconds", 0)) for s in director_plan.get("scenes", []))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Số cảnh", len(director_plan.get("scenes", [])))
        c2.metric("Thời lượng", f"{total_seconds/60:.1f} phút")
        c3.metric("Diễn viên", len({n for s in director_plan.get("scenes", []) for n in s.get("model_names", [])}))
        c4.metric("Chế độ", director_plan.get("direction_mode", "Auto"))
        st.info("Sửa Action, Camera, thời lượng hoặc tọa độ staging bên dưới. Tên Model trong Workspace phải khớp với tên nhân vật đã tạo trong 3D Model Builder.")
        editable_rows = []
        for scene in director_plan.get("scenes", []):
            editable_rows.append({
                "scene_number": scene.get("scene_number"), "location": scene.get("location"),
                "action": scene.get("action"), "camera": scene.get("camera"),
                "duration_seconds": scene.get("duration_seconds"), "target_x": scene.get("target_x"),
                "target_z": scene.get("target_z"), "characters": ", ".join(scene.get("characters", []))
            })
        edited_rows = st.data_editor(pd.DataFrame(editable_rows), use_container_width=True, hide_index=True, num_rows="fixed", key="scene_director_editor",
            column_config={
                "action": st.column_config.SelectboxColumn("Action", options=["idle","walk","run","jump","wave","cheer","fall","dodge","look","react"]),
                "camera": st.column_config.SelectboxColumn("Camera", options=["wide","medium","closeup","over_shoulder","low_angle","high_angle","tracking","orbit"]),
                "duration_seconds": st.column_config.NumberColumn("Seconds", min_value=2, max_value=45, step=0.5),
                "target_x": st.column_config.NumberColumn("Target X", min_value=-1000, max_value=1000, step=1),
                "target_z": st.column_config.NumberColumn("Target Z", min_value=-1000, max_value=1000, step=1),
            })
        if st.button("💾 Áp dụng chỉnh sửa và sinh bộ file Scene Director", type="primary"):
            updated = dict(director_plan)
            updated_scenes = []
            for index, row in enumerate(edited_rows.to_dict(orient="records")):
                if index >= len(director_plan["scenes"]):
                    break
                scene = dict(director_plan["scenes"][index])
                scene["scene_number"] = int(row.get("scene_number") or index + 1)
                scene["location"] = str(row.get("location") or "Scene Location")[:120]
                scene["action"] = row.get("action") if row.get("action") in {"idle","walk","run","jump","wave","cheer","fall","dodge","look","react"} else "idle"
                scene["camera"] = row.get("camera") if row.get("camera") in {"wide","medium","closeup","over_shoulder","low_angle","high_angle","tracking","orbit"} else "medium"
                try: scene["duration_seconds"] = max(2, min(45, float(row.get("duration_seconds", 6))))
                except (TypeError, ValueError): scene["duration_seconds"] = 6
                try: scene["target_x"] = max(-1000, min(1000, float(row.get("target_x", 0))))
                except (TypeError, ValueError): scene["target_x"] = 0
                try: scene["target_z"] = max(-1000, min(1000, float(row.get("target_z", 0))))
                except (TypeError, ValueError): scene["target_z"] = 0
                names = [x.strip() for x in str(row.get("characters") or "").split(",") if x.strip()]
                scene["characters"] = names
                scene["model_names"] = [safe_filename(x) for x in names]
                updated_scenes.append(scene)
            updated["scenes"] = updated_scenes
            safe_title = safe_filename(updated.get("title", "RobloxStory"))
            out_dir = BASE / "exports" / "scene_director"
            out_dir.mkdir(parents=True, exist_ok=True)
            plan_dir = DATA / "scene_director"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plan_dir / f"{safe_title}_DirectorPlan.json"
            installer_path = out_dir / f"{safe_title}_SceneDirectorInstaller.lua"
            client_path = out_dir / f"{safe_title}_SceneDirectorCamera.client.lua"
            server_path = out_dir / f"{safe_title}_SceneDirector.server.lua"
            bat_path = out_dir / f"{safe_title}_InstallAndOpenStudio.bat"
            server_source = build_scene_director_server_source(updated)
            client_source = build_scene_director_client_source()
            installer_source = build_scene_director_installer(server_source, client_source)
            plan_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
            installer_path.write_text(installer_source, encoding="utf-8")
            server_path.write_text(server_source, encoding="utf-8")
            client_path.write_text(client_source, encoding="utf-8")
            bat_path.write_text(build_scene_director_launcher(config.get("roblox_studio_exe", ""), config.get("roblox_place_path", ""), installer_path.name), encoding="utf-8")
            st.session_state["scene_director_plan"] = updated
            st.session_state["scene_director_files"] = {"plan":str(plan_path),"installer":str(installer_path),"server":str(server_path),"client":str(client_path),"bat":str(bat_path)}
            st.session_state["scene_director_installer_source"] = installer_source
            st.session_state["scene_director_server_source"] = server_source
            st.session_state["scene_director_client_source"] = client_source
            st.success("Đã lưu Director Plan và tạo bộ script Roblox Studio.")

        files_out = st.session_state.get("scene_director_files")
        if files_out:
            st.subheader("03 · Tải bộ file và cài vào Roblox Studio")
            for key, label in [("installer","Scene Director Installer (.lua)"),("server","Server Controller (.lua)"),("client","Camera Controller (.lua)"),("bat","Windows Launcher (.bat)"),("plan","Director Plan (.json)")]:
                path = Path(files_out[key])
                if path.exists():
                    mime = "application/json" if path.suffix == ".json" else "text/plain"
                    st.download_button(f"⬇️ {label}", data=path.read_bytes(), file_name=path.name, mime=mime, key=f"download_scene_{key}")
            with st.expander("Xem mã Installer Luau"):
                st.code(st.session_state.get("scene_director_installer_source", ""), language="lua")
            with st.expander("Hướng dẫn chạy cảnh"):
                st.markdown("""
1. Tạo các NPC trong **3D Model Builder** và chạy script tạo model trong đúng place.
2. Tạo map bằng **World Builder** trong cùng place.
3. Trong Dashboard, chọn đúng Story JSON và World Plan; tạo Director Plan, chỉnh action/camera/tọa độ nếu cần.
4. Nhấn **Áp dụng chỉnh sửa và sinh bộ file Scene Director** để tải Installer và Launcher.
5. Đóng place chưa lưu nếu cần; chạy `*_InstallAndOpenStudio.bat` để cài hai script điều khiển vào `ServerScriptService` và `StarterPlayerScripts`.
6. Trong Roblox Studio nhấn **Play (F5)**. Server Script điều khiển NPC; LocalScript điều khiển camera riêng trên client. Dùng OBS để quay cửa sổ Play.

**Lưu ý:** Script điều khiển các model NPC có `Humanoid` trong Workspace và tên model phải khớp với Character Bible. Các action hiện gồm idle, walk, run, jump, wave, cheer, fall, dodge, look và react. Chuyển động là procedural/blocky cơ bản, chưa dùng animation asset chuyên nghiệp hay pathfinding né vật cản. Chuyển động `walk/run` dùng `Humanoid:MoveTo`; camera Scriptable chạy ở LocalScript của từng client. Kiểm tra scene và đường đi trước khi quay.
""")

elif page == "Sound Studio":
    st.title("🎵 SOUND STUDIO AI")
    st.write("Quản lý thư viện âm thanh, thiết kế cue theo từng cảnh và xuất timeline cho Roblox Studio hoặc FFmpeg.")
    st.caption("Module không tự tạo file nhạc/hiệu ứng. Bạn sử dụng audio tự có quyền, tải lên thư viện và gắn Roblox Audio Asset ID sau khi upload/được phép dùng trong experience.")

    audio_dir = BASE / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    cue_dir = DATA / "sound_cues"
    cue_dir.mkdir(parents=True, exist_ok=True)
    asset_path = DATA / "sound_assets.json"
    sound_assets = load_json(asset_path, [])
    if not isinstance(sound_assets, list):
        sound_assets = []

    tab_library, tab_timeline, tab_export = st.tabs(["📚 Thư viện âm thanh", "🎚️ Sound Timeline", "📦 Xuất & tích hợp"])

    with tab_library:
        st.subheader("Thêm âm thanh vào thư viện")
        uploaded_audio = st.file_uploader(
            "Tải file âm thanh (MP3, WAV, OGG, M4A)",
            type=["mp3", "wav", "ogg", "m4a"],
            key="sound_asset_upload"
        )
        with st.form("sound_asset_form"):
            c1, c2 = st.columns(2)
            with c1:
                asset_name = st.text_input("Tên asset *", placeholder="Suspense_Ambience_Loop")
                asset_type = st.selectbox("Loại âm thanh", ["Music", "Ambience", "SFX", "Transition"])
                roblox_audio_id = st.text_input("Roblox Audio Asset ID (không bắt buộc)", placeholder="Ví dụ: 1234567890")
            with c2:
                source_note = st.text_input("Nguồn / giấy phép", placeholder="Original / licensed library / Creator Store...")
                rights_confirmed = st.checkbox("Tôi có quyền sử dụng và/hoặc tải âm thanh này lên dự án")
            save_asset = st.form_submit_button("＋ Lưu vào thư viện", type="primary")
            if save_asset:
                clean_name = asset_name.strip()
                normalized_id = normalize_roblox_audio_id(roblox_audio_id)
                if not clean_name:
                    st.error("Hãy nhập tên asset.")
                elif any(a.get("name", "").casefold() == clean_name.casefold() for a in sound_assets):
                    st.error("Tên asset đã tồn tại.")
                elif uploaded_audio is None and not normalized_id:
                    st.error("Hãy tải file âm thanh hoặc nhập Roblox Audio Asset ID.")
                else:
                    local_path = ""
                    saved_file = ""
                    if uploaded_audio is not None:
                        suffix = Path(uploaded_audio.name).suffix.lower()
                        safe_stem = safe_filename(clean_name)
                        target = audio_dir / f"{safe_stem}{suffix}"
                        counter = 2
                        while target.exists():
                            target = audio_dir / f"{safe_stem}_{counter}{suffix}"
                            counter += 1
                        target.write_bytes(uploaded_audio.getvalue())
                        local_path = str(target)
                        saved_file = target.name
                    sound_assets.append({
                        "asset_id": "sound_" + safe_filename(clean_name),
                        "name": clean_name,
                        "type": asset_type,
                        "roblox_audio_id": normalized_id,
                        "local_path": local_path,
                        "file_name": saved_file,
                        "source_note": source_note,
                        "rights_confirmed": bool(rights_confirmed),
                        "created_at": datetime.now().isoformat(timespec="seconds")
                    })
                    save_json(asset_path, sound_assets)
                    st.success(f"Đã lưu asset: {clean_name}")
                    st.rerun()

        if sound_assets:
            st.subheader(f"Thư viện hiện có: {len(sound_assets)} asset")
            asset_rows = [{
                "Tên": a.get("name", ""),
                "Loại": a.get("type", ""),
                "File cục bộ": a.get("file_name", "") or "—",
                "Roblox Asset ID": a.get("roblox_audio_id", "") or "—",
                "Quyền sử dụng": "Đã xác nhận" if a.get("rights_confirmed") else "Chưa xác nhận",
                "Nguồn": a.get("source_note", "")
            } for a in sound_assets]
            st.dataframe(pd.DataFrame(asset_rows), use_container_width=True, hide_index=True)
            preview_name = st.selectbox("Nghe thử file cục bộ", ["— Không chọn —"] + [a.get("name", "") for a in sound_assets if a.get("local_path")])
            if preview_name != "— Không chọn —":
                asset = next(a for a in sound_assets if a.get("name") == preview_name)
                if Path(asset.get("local_path", "")).is_file():
                    st.audio(asset["local_path"])
            delete_name = st.selectbox("Xóa asset khỏi thư viện", ["— Không xóa —"] + [a.get("name", "") for a in sound_assets], key="delete_sound_asset")
            if st.button("Xóa asset đã chọn", disabled=(delete_name == "— Không xóa —")):
                sound_assets = [a for a in sound_assets if a.get("name") != delete_name]
                save_json(asset_path, sound_assets)
                st.success("Đã xóa khỏi thư viện. File âm thanh trên ổ đĩa được giữ nguyên.")
                st.rerun()
        else:
            st.info("Thư viện đang trống. Thêm nhạc nền, ambience hoặc SFX để bắt đầu.")

    director_dir = DATA / "scene_director"
    director_files = sorted(director_dir.glob("*_DirectorPlan.json")) if director_dir.exists() else []
    with tab_timeline:
        st.subheader("Nạp Director Plan")
        plan_labels = [p.name for p in director_files]
        if not plan_labels:
            st.info("Chưa có Director Plan. Hãy tạo và lưu bộ file trong Scene Director trước.")
        else:
            selected_plan_label = st.selectbox("Chọn Director Plan", plan_labels, key="sound_director_plan_select")
            if st.button("Nạp timeline từ Director Plan"):
                selected_path = next(p for p in director_files if p.name == selected_plan_label)
                loaded_plan = load_json(selected_path, None)
                if not isinstance(loaded_plan, dict) or not isinstance(loaded_plan.get("scenes"), list):
                    st.error("Director Plan không hợp lệ.")
                else:
                    timeline_path = cue_dir / f"{selected_path.stem.replace('_DirectorPlan','')}_SoundTimeline.json"
                    existing_timeline = load_json(timeline_path, None)
                    if isinstance(existing_timeline, dict) and isinstance(existing_timeline.get("cues"), list):
                        current_cues = existing_timeline["cues"]
                    else:
                        current_cues = make_default_sound_cues(loaded_plan)
                    st.session_state.pop("sound_timeline_editor", None)
                    st.session_state["sound_plan"] = loaded_plan
                    st.session_state["sound_plan_path"] = str(selected_path)
                    st.session_state["sound_timeline_path"] = str(timeline_path)
                    st.session_state["sound_cues"] = current_cues
                    st.success(f"Đã nạp {len(loaded_plan.get('scenes', []))} cảnh và {len(current_cues)} cue.")
                    st.rerun()

        if "sound_plan" in st.session_state:
            current_plan = st.session_state["sound_plan"]
            current_cues = st.session_state.get("sound_cues", [])
            scene_rows = current_plan.get("scenes", [])
            total_seconds = sum(float(s.get("duration_seconds", 0) or 0) for s in scene_rows)
            c1, c2, c3 = st.columns(3)
            c1.metric("Số cảnh", len(scene_rows))
            c2.metric("Tổng thời lượng", f"{total_seconds:.1f} giây")
            c3.metric("Cue âm thanh", len(current_cues))

            if st.button("✨ AI Sound Supervisor – đề xuất cue", type="secondary"):
                api_key = config.get("openai_api_key", "").strip()
                if not api_key:
                    st.error("Cần OpenAI API key trong mục Cài đặt để dùng AI Sound Supervisor.")
                else:
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)
                        system_prompt = """You are a sound designer for original, family-friendly Roblox-style animated stories.
Return ONLY valid JSON with one key: cues, an array of cues.
For each scene, suggest 0-2 practical sound cues. Each cue object must contain:
scene_number (integer), cue_type (Music|Ambience|SFX|Transition), start_offset_seconds (number within the scene),
duration_seconds (number no longer than the scene), volume (0.0-1.0), fade_in_seconds (number),
fade_out_seconds (number), loop (boolean), target_model (string or empty),
description (short sound design direction).
Do not create audio, do not invent Roblox asset IDs, and do not choose a file. Write concise American English descriptions.
Maintain family-friendly non-graphic tone. Do not add voice-over unless explicitly present in the story."""
                        user_prompt = json.dumps({
                            "title": current_plan.get("title", ""),
                            "scenes": [{
                                "scene_number": s.get("scene_number"),
                                "duration_seconds": s.get("duration_seconds"),
                                "action": s.get("action"),
                                "location": s.get("location"),
                                "characters": s.get("characters", []),
                                "music_and_sfx": s.get("music_and_sfx", "")
                            } for s in scene_rows]
                        }, ensure_ascii=False)
                        with st.spinner("AI đang thiết kế sound cues..."):
                            response = client.chat.completions.create(
                                model="gpt-4.1-mini",
                                response_format={"type": "json_object"},
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                temperature=0.45
                            )
                            ai_cues = json.loads(response.choices[0].message.content).get("cues", [])
                        scene_starts = {}
                        cursor = 0.0
                        scene_durations = {}
                        for sc in scene_rows:
                            sn = int(sc.get("scene_number", 0))
                            scene_starts[sn] = cursor
                            scene_durations[sn] = max(0.1, float(sc.get("duration_seconds", 6) or 6))
                            cursor += scene_durations[sn]
                        added = []
                        for idx, item in enumerate(ai_cues[:100], start=1):
                            if not isinstance(item, dict):
                                continue
                            try:
                                sn = int(item.get("scene_number"))
                                scene_duration = scene_durations.get(sn)
                                if scene_duration is None:
                                    continue
                                offset = max(0.0, min(scene_duration, float(item.get("start_offset_seconds", 0))))
                                dur = max(0.1, min(scene_duration - offset or scene_duration, float(item.get("duration_seconds", scene_duration))))
                            except (TypeError, ValueError):
                                continue
                            cue_type = item.get("cue_type")
                            if cue_type not in ("Music", "Ambience", "SFX", "Transition"):
                                cue_type = "SFX"
                            added.append({
                                "cue_id": f"AI_SC{sn:03d}_{idx:03d}",
                                "scene_number": sn,
                                "cue_type": cue_type,
                                "asset_name": "",
                                "start_seconds": round(scene_starts[sn] + offset, 2),
                                "duration_seconds": round(dur, 2),
                                "volume": max(0.0, min(1.0, float(item.get("volume", 0.6) or 0))),
                                "fade_in_seconds": max(0.0, min(10.0, float(item.get("fade_in_seconds", 0.1) or 0))),
                                "fade_out_seconds": max(0.0, min(10.0, float(item.get("fade_out_seconds", 0.2) or 0))),
                                "loop": bool(item.get("loop", False)),
                                "target_model": str(item.get("target_model", "") or ""),
                                "description": str(item.get("description", ""))[:240],
                                "asset_id": "",
                                "local_path": "",
                                "rights_confirmed": False
                            })
                        st.session_state["sound_cues"] = current_cues + added
                        st.session_state.pop("sound_timeline_editor", None)
                        st.success(f"AI đã đề xuất thêm {len(added)} cue. Hãy gán asset âm thanh trong bảng bên dưới.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Không thể tạo đề xuất âm thanh: {exc}")

            with st.expander("＋ Thêm cue thủ công"):
                scene_choices = ["Toàn video"] + [str(s.get("scene_number")) for s in scene_rows]
                with st.form("manual_sound_cue"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        cue_scene = st.selectbox("Cảnh", scene_choices)
                        cue_type = st.selectbox("Loại cue", ["Music", "Ambience", "SFX", "Transition"])
                    with c2:
                        cue_asset_name = st.selectbox("Asset", ["(Chưa gán)"] + [a.get("name", "") for a in sound_assets])
                        cue_volume = st.slider("Âm lượng", 0.0, 1.0, 0.5, 0.05)
                    with c3:
                        cue_duration = st.number_input("Thời lượng (giây)", min_value=0.1, max_value=3600.0, value=max(0.1, total_seconds if cue_scene == "Toàn video" else 6.0), step=0.5)
                        cue_loop = st.checkbox("Lặp lại", value=(cue_type in ("Music", "Ambience")))
                    cue_start = st.number_input("Thời điểm bắt đầu (giây)", min_value=0.0, max_value=36000.0, value=0.0, step=0.5)
                    cue_note = st.text_input("Mô tả / ghi chú", placeholder="Soft suspense pad fades in...")
                    if st.form_submit_button("Thêm cue"):
                        selected_asset = next((a for a in sound_assets if a.get("name") == cue_asset_name), None)
                        current_cues.append({
                            "cue_id": f"MANUAL_{len(current_cues)+1:03d}",
                            "scene_number": 0 if cue_scene == "Toàn video" else int(cue_scene),
                            "cue_type": cue_type,
                            "asset_name": "" if cue_asset_name == "(Chưa gán)" else cue_asset_name,
                            "start_seconds": float(cue_start),
                            "duration_seconds": float(cue_duration),
                            "volume": float(cue_volume),
                            "fade_in_seconds": 0.25 if cue_type in ("Music", "Ambience") else 0.05,
                            "fade_out_seconds": 0.4 if cue_type in ("Music", "Ambience") else 0.1,
                            "loop": bool(cue_loop),
                            "target_model": "",
                            "description": cue_note,
                            "asset_id": (selected_asset or {}).get("roblox_audio_id", ""),
                            "local_path": (selected_asset or {}).get("local_path", ""),
                            "rights_confirmed": bool((selected_asset or {}).get("rights_confirmed", False))
                        })
                        st.session_state["sound_cues"] = current_cues
                        st.session_state.pop("sound_timeline_editor", None)
                        st.success("Đã thêm cue.")
                        st.rerun()

            if current_cues:
                st.subheader("Chỉnh sửa timeline")
                asset_names = ["(Chưa gán)"] + [a.get("name", "") for a in sound_assets]
                rows_for_editor = []
                for cue in current_cues:
                    rows_for_editor.append({
                        "cue_id": cue.get("cue_id", ""),
                        "scene_number": int(cue.get("scene_number", 0) or 0),
                        "cue_type": cue.get("cue_type", "SFX"),
                        "asset_name": cue.get("asset_name", "") or "(Chưa gán)",
                        "start_seconds": float(cue.get("start_seconds", 0) or 0),
                        "duration_seconds": float(cue.get("duration_seconds", 3) or 3),
                        "volume": float(cue.get("volume", 0.7) or 0),
                        "fade_in_seconds": float(cue.get("fade_in_seconds", 0) or 0),
                        "fade_out_seconds": float(cue.get("fade_out_seconds", 0) or 0),
                        "loop": bool(cue.get("loop", False)),
                        "target_model": cue.get("target_model", ""),
                        "description": cue.get("description", "")
                    })
                edited_cues = st.data_editor(
                    pd.DataFrame(rows_for_editor),
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="sound_timeline_editor",
                    column_config={
                        "cue_id": st.column_config.TextColumn("Cue ID", disabled=True),
                        "scene_number": st.column_config.NumberColumn("Scene (0 = toàn video)", min_value=0, max_value=999, step=1),
                        "cue_type": st.column_config.SelectboxColumn("Loại", options=["Music", "Ambience", "SFX", "Transition"]),
                        "asset_name": st.column_config.SelectboxColumn("Asset", options=asset_names),
                        "start_seconds": st.column_config.NumberColumn("Start (s)", min_value=0.0, max_value=36000.0, step=0.1),
                        "duration_seconds": st.column_config.NumberColumn("Duration (s)", min_value=0.1, max_value=36000.0, step=0.1),
                        "volume": st.column_config.NumberColumn("Volume", min_value=0.0, max_value=1.0, step=0.05),
                        "fade_in_seconds": st.column_config.NumberColumn("Fade in", min_value=0.0, max_value=60.0, step=0.1),
                        "fade_out_seconds": st.column_config.NumberColumn("Fade out", min_value=0.0, max_value=60.0, step=0.1),
                        "loop": st.column_config.CheckboxColumn("Loop"),
                        "target_model": st.column_config.TextColumn("3D target model (optional)"),
                        "description": st.column_config.TextColumn("Mô tả cue")
                    }
                )
                if st.button("💾 Lưu chỉnh sửa timeline", type="primary"):
                    saved_cues = []
                    for idx, row in enumerate(edited_cues.to_dict(orient="records"), start=1):
                        name = row.get("asset_name", "")
                        asset = next((a for a in sound_assets if a.get("name") == name), None)
                        try:
                            start = max(0.0, float(row.get("start_seconds", 0) or 0))
                            duration = max(0.1, float(row.get("duration_seconds", 3) or 3))
                            volume = max(0.0, min(1.0, float(row.get("volume", 0.7) or 0)))
                        except (TypeError, ValueError):
                            continue
                        saved_cues.append({
                            "cue_id": str(row.get("cue_id") or f"CUE_{idx:03d}"),
                            "scene_number": max(0, int(row.get("scene_number", 0) or 0)),
                            "cue_type": row.get("cue_type") if row.get("cue_type") in ("Music","Ambience","SFX","Transition") else "SFX",
                            "asset_name": "" if name == "(Chưa gán)" else name,
                            "start_seconds": round(start, 2),
                            "duration_seconds": round(duration, 2),
                            "volume": round(volume, 3),
                            "fade_in_seconds": max(0.0, float(row.get("fade_in_seconds", 0) or 0)),
                            "fade_out_seconds": max(0.0, float(row.get("fade_out_seconds", 0) or 0)),
                            "loop": bool(row.get("loop", False)),
                            "target_model": str(row.get("target_model", "") or "")[:100],
                            "description": str(row.get("description", "") or "")[:240],
                            "asset_id": (asset or {}).get("roblox_audio_id", ""),
                            "local_path": (asset or {}).get("local_path", ""),
                            "rights_confirmed": bool((asset or {}).get("rights_confirmed", False))
                        })
                    st.session_state["sound_cues"] = saved_cues
                    st.session_state.pop("sound_timeline_editor", None)
                    st.success(f"Đã lưu {len(saved_cues)} cue.")
                    st.rerun()
            else:
                st.info("Chưa có cue. Dùng AI Sound Supervisor hoặc Thêm cue thủ công.")

    with tab_export:
        if "sound_plan" not in st.session_state:
            st.info("Nạp Director Plan trong tab Sound Timeline trước khi xuất.")
        else:
            current_plan = st.session_state["sound_plan"]
            current_cues = st.session_state.get("sound_cues", [])
            sound_title = safe_filename(current_plan.get("title", "RobloxStory"))
            st.write(f"**Dự án:** {current_plan.get('title','Roblox Story')} · **{len(current_cues)} cue**")
            roblox_ready = [c for c in current_cues if normalize_roblox_audio_id(c.get("asset_id", ""))]
            ffmpeg_ready = [c for c in current_cues if c.get("local_path") and Path(c.get("local_path", "")).is_file() and c.get("rights_confirmed")]
            st.metric("Cue có Roblox Audio ID", len(roblox_ready))
            st.metric("Cue có file cục bộ + xác nhận quyền", len(ffmpeg_ready))

            sound_bundle_dir = BASE / "exports" / "sound_studio"
            sound_bundle_dir.mkdir(parents=True, exist_ok=True)
            timeline_path = cue_dir / f"{sound_title}_SoundTimeline.json"
            timeline_payload = {
                "title": current_plan.get("title", ""),
                "director_plan": st.session_state.get("sound_plan_path", ""),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "total_duration_seconds": sum(float(s.get("duration_seconds", 0) or 0) for s in current_plan.get("scenes", [])),
                "cues": current_cues
            }
            timeline_path.write_text(json.dumps(timeline_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            st.download_button(
                "⬇️ Tải Sound Timeline JSON",
                data=timeline_path.read_bytes(),
                file_name=timeline_path.name,
                mime="application/json"
            )

            if roblox_ready:
                client_source = build_sound_studio_client_source(roblox_ready)
                installer_source = build_sound_studio_installer(client_source)
                installer_path = sound_bundle_dir / f"{sound_title}_SoundStudioInstaller.lua"
                client_path = sound_bundle_dir / f"{sound_title}_SoundStudioClient.client.lua"
                installer_path.write_text(installer_source, encoding="utf-8")
                client_path.write_text(client_source, encoding="utf-8")
                st.download_button("⬇️ Tải Roblox Sound Installer (.lua)", data=installer_path.read_bytes(),
                                   file_name=installer_path.name, mime="text/plain")
                st.download_button("⬇️ Tải Sound Client (.lua)", data=client_path.read_bytes(),
                                   file_name=client_path.name, mime="text/plain")
                st.success("Đã sinh bộ script âm thanh Roblox.")
            else:
                st.warning("Chưa có cue nào gắn Roblox Audio Asset ID. Để phát âm thanh trong Roblox, hãy upload/được cấp quyền audio cho experience rồi nhập Asset ID vào thư viện và gán cue.")

            st.subheader("FFmpeg – mix audio vào video")
            preserve_source_audio = st.checkbox("Giữ và trộn cả âm thanh gốc từ video OBS (video đầu vào phải có audio)", value=False)
            source_audio_volume = st.slider("Âm lượng audio gốc", 0.0, 2.0, 0.7, 0.05, disabled=not preserve_source_audio)
            source_video = st.text_input("Đường dẫn video OBS đầu vào (.mp4)", value="", placeholder=r"C:\RobloxProjects\exports\episode_raw.mp4")
            output_video = st.text_input("Đường dẫn MP4 đầu ra", value=str(Path(config.get("output_dir", str(BASE/"exports"))) / f"{sound_title}_final.mp4"))
            if st.button("Tạo file MixAudioToVideo.bat"):
                if not source_video.strip():
                    st.error("Nhập đường dẫn video đầu vào.")
                elif not Path(source_video).is_file():
                    st.error("Không tìm thấy video đầu vào trên máy đang chạy Dashboard.")
                elif not ffmpeg_ready:
                    st.error("Chưa có cue nào có file âm thanh cục bộ và xác nhận quyền sử dụng.")
                else:
                    try:
                        batch_source = build_ffmpeg_sound_mix_batch(
                            ffmpeg_ready,
                            config.get("ffmpeg_path", ""),
                            source_video.strip(),
                            output_video.strip(),
                            preserve_source_audio=preserve_source_audio,
                            source_audio_volume=source_audio_volume
                        )
                        batch_path = sound_bundle_dir / f"{sound_title}_MixAudioToVideo.bat"
                        batch_path.write_text(batch_source, encoding="utf-8")
                        st.session_state["sound_mix_batch_path"] = str(batch_path)
                        st.success("Đã tạo batch mix. Chạy file trên Windows sau khi kiểm tra đường dẫn FFmpeg.")
                    except Exception as exc:
                        st.error(f"Không tạo được batch: {exc}")
            mix_path = st.session_state.get("sound_mix_batch_path", "")
            if mix_path and Path(mix_path).is_file():
                st.download_button("⬇️ Tải MixAudioToVideo.bat", data=Path(mix_path).read_bytes(),
                                   file_name=Path(mix_path).name, mime="text/plain")

            with st.expander("Hướng dẫn cài âm thanh Roblox"):
                st.markdown("""
1. Chỉ dùng âm thanh do bạn tạo, được cấp phép hoặc có quyền sử dụng phù hợp.
2. Upload âm thanh lên Roblox Creator Dashboard/Creator Store theo quyền của tài khoản và experience; sao chép Audio Asset ID.
3. Thêm ID vào thư viện Sound Studio, gán asset cho từng cue và lưu timeline.
4. Tải `SoundStudioInstaller.lua`; chạy một lần trong Roblox Studio Command Bar hoặc thông qua Studio CLI `--task RunScript`.
5. Lưu place, nhấn Play (F5) để chạy thử. LocalScript lên lịch cue trên client; âm thanh gắn `target_model` sẽ phát gần HumanoidRootPart của model đó, nếu không tìm thấy sẽ phát toàn cục.
6. Để mix video offline, nhập file MP4 gốc và tạo `MixAudioToVideo.bat`. Batch chỉ dùng file âm thanh cục bộ đã được xác nhận quyền sử dụng.

**Giới hạn:** Chưa tự tạo nhạc/hiệu ứng, chưa upload audio lên Roblox thay bạn, chưa tự thu âm OBS. Âm thanh trong Roblox có thể bị chặn nếu asset chưa được cấp quyền cho experience. Hãy thử một cue ngắn trước khi render toàn tập.
""")


elif page == "Video Editor":
    st.title("🎞️ VIDEO FACTORY AI")
    st.write("Điều khiển OBS, cắt video theo Director Plan, nối cảnh, chuẩn hóa 1080p/4K và trộn âm thanh Sound Studio.")
    st.caption("OBS WebSocket điều khiển thao tác quay; FFmpeg xử lý hậu kỳ cục bộ. Hãy kiểm tra nguồn Display Capture/Game Capture và quyền âm thanh trước khi ghi hình.")

    tab_obs, tab_render, tab_jobs = st.tabs(["🔴 OBS Capture", "🎬 Render & Export", "📁 Jobs & hướng dẫn"])

    with tab_obs:
        st.subheader("Kết nối OBS Studio")
        st.markdown("OBS 28+ thường đã tích hợp WebSocket. Trong OBS: **Tools → WebSocket Server Settings → Enable WebSocket server**; giữ xác thực bằng mật khẩu và nhập đúng host/port/password trong Cài đặt.")
        st.caption("Mặc định OBS WebSocket dùng 127.0.0.1:4455. Nếu bạn đổi port, phải đổi cả trong Dashboard.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Host", config.get("obs_host", "127.0.0.1"))
        c2.metric("Port", int(config.get("obs_port", 4455)))
        c3.metric("OBS executable", "Đã cấu hình" if config.get("obs_path") else "Chưa cấu hình")

        if st.button("🔌 Kết nối / làm mới OBS", type="primary"):
            try:
                with make_obs_client(config) as obs_client:
                    version = obs_client.get_version()
                    scene_response = obs_client.get_scene_list()
                    record_status = obs_client.get_record_status()
                    names = obs_scene_names(scene_response)
                    st.session_state["obs_scene_names"] = names
                    st.session_state["obs_version_info"] = {
                        "obs_version": response_value(version, "obs_version", "obsVersion", default="Unknown"),
                        "websocket_version": response_value(version, "obs_web_socket_version", "obsWebSocketVersion", default="5.x"),
                        "current_scene": response_value(scene_response, "current_program_scene_name", "currentProgramSceneName", default="Unknown"),
                        "recording": bool(response_value(record_status, "output_active", "outputActive", default=False))
                    }
                st.success("Đã kết nối OBS WebSocket.")
            except ImportError:
                st.error("Thiếu obsws-python. Hãy đóng Dashboard và chạy lại run_windows.bat để cài dependency mới.")
            except Exception as exc:
                st.error(f"Không kết nối được OBS: {exc}. Kiểm tra OBS đang mở, WebSocket đã bật, host/port/password chính xác.")

        info = st.session_state.get("obs_version_info")
        if info:
            st.json(info)
            names = st.session_state.get("obs_scene_names", [])
            if names:
                scene_to_switch = st.selectbox("Chuyển OBS Program Scene", names, key="obs_scene_picker")
                if st.button("Đặt scene đang phát"):
                    try:
                        with make_obs_client(config) as obs_client:
                            obs_client.set_current_program_scene(scene_to_switch)
                        st.success(f"OBS đã chuyển sang scene: {scene_to_switch}")
                    except Exception as exc:
                        st.error(f"Không chuyển được scene: {exc}")

        st.divider()
        st.subheader("Điều khiển Recording")
        capture_name = st.text_input("Tên file capture khi nhập vào dự án", value="Roblox_Episode_Raw")
        st.warning("Trước khi quay: mở Roblox Studio, mở đúng place và kiểm tra OBS có nguồn Game Capture/Display Capture đang nhìn thấy cửa sổ Roblox. Start Recording ở đây, sau đó nhấn Play (F5) trong Studio. Khi hết cảnh, quay lại Dashboard và Stop Recording.")
        cstart, cstop = st.columns(2)
        with cstart:
            if st.button("⏺️ START RECORDING", type="primary", use_container_width=True):
                try:
                    with make_obs_client(config) as obs_client:
                        status = obs_client.get_record_status()
                        active = bool(response_value(status, "output_active", "outputActive", default=False))
                        if active:
                            st.warning("OBS đang quay. Không gửi lệnh Start lần nữa.")
                        else:
                            obs_client.start_record()
                            st.session_state["obs_capture_name"] = safe_filename(capture_name or "Roblox_Episode_Raw")
                            st.session_state["obs_record_started"] = datetime.now().isoformat(timespec="seconds")
                            st.success("OBS đã bắt đầu quay. Hãy nhấn F5 trong Roblox Studio để chạy Scene Director.")
                except Exception as exc:
                    st.error(f"Không bắt đầu quay được: {exc}")
        with cstop:
            if st.button("⏹️ STOP & IMPORT RECORDING", use_container_width=True):
                try:
                    with make_obs_client(config) as obs_client:
                        status = obs_client.get_record_status()
                        active = bool(response_value(status, "output_active", "outputActive", default=False))
                        if not active:
                            st.warning("OBS hiện không ở trạng thái Recording.")
                        else:
                            stopped = obs_client.stop_record()
                            recorded_path = response_value(stopped, "output_path", "outputPath", default="")
                            if not recorded_path:
                                st.warning("OBS đã dừng quay nhưng không trả về outputPath. Hãy xem Recording Path trong OBS Output Settings.")
                            else:
                                capture_dir = Path(config.get("output_dir", str(BASE/"exports"))) / "captures"
                                imported = safe_copy_recording(recorded_path, capture_dir, st.session_state.get("obs_capture_name", "Roblox_Episode_Raw"))
                                if imported:
                                    st.session_state["latest_obs_capture"] = imported
                                    st.success(f"Đã dừng OBS và nhập bản quay vào dự án: {imported}")
                                else:
                                    st.warning(f"OBS trả về đường dẫn nhưng file chưa tìm thấy: {recorded_path}. Hãy kiểm tra OBS Recording Path.")
                except Exception as exc:
                    st.error(f"Không dừng/import được recording: {exc}")
        latest_capture = st.session_state.get("latest_obs_capture")
        if latest_capture and Path(latest_capture).is_file():
            st.success(f"Capture gần nhất: {latest_capture}")
            st.video(latest_capture)

    with tab_render:
        st.subheader("Tạo video từ Director Plan")
        director_dir = DATA / "scene_director"
        director_files = sorted(director_dir.glob("*_DirectorPlan.json")) if director_dir.exists() else []
        cue_dir = DATA / "sound_cues"
        timeline_files = sorted(cue_dir.glob("*_SoundTimeline.json")) if cue_dir.exists() else []
        if not director_files:
            st.info("Chưa có Director Plan. Hãy tạo và lưu kế hoạch trong Scene Director trước.")
        else:
            director_labels = [p.name for p in director_files]
            selected_director_label = st.selectbox("Director Plan", director_labels, key="vf_director_plan")
            selected_director_path = next(p for p in director_files if p.name == selected_director_label)
            selected_director = load_json(selected_director_path, {})
            scenes = selected_director.get("scenes", []) if isinstance(selected_director, dict) else []
            total_seconds = sum(max(0.1, float(sc.get("duration_seconds", 6) or 6)) for sc in scenes)
            st.metric("Tổng cảnh / thời lượng dự kiến", f"{len(scenes)} cảnh · {total_seconds/60:.2f} phút")
            if timeline_files:
                timeline_options = ["Không trộn cue âm thanh"] + [p.name for p in timeline_files]
                selected_timeline_label = st.selectbox("Sound Timeline (tùy chọn)", timeline_options, key="vf_sound_timeline")
            else:
                selected_timeline_label = "Không trộn cue âm thanh"
                st.caption("Chưa có Sound Timeline đã lưu; bạn vẫn có thể dựng từ audio gốc trong OBS.")

            source_default = st.session_state.get("latest_obs_capture", "")
            source_video = st.text_input("Video OBS đầu vào (.mp4/.mkv)", value=source_default, placeholder=r"C:\RobloxProjects\exports\captures\Roblox_Episode_Raw.mkv")
            out_dir_default = Path(config.get("output_dir", str(BASE/"exports")))
            title_default = safe_filename(selected_director.get("title", "RobloxEpisode"))
            output_video = st.text_input("MP4 đầu ra", value=str(out_dir_default / f"{title_default}_final.mp4"))

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                aspect = st.selectbox("Tỷ lệ khung hình", ["16:9 YouTube", "9:16 Shorts"])
            with p2:
                resolution = st.selectbox("Độ phân giải", ["1080p", "4K"])
            with p3:
                fps = st.selectbox("FPS đầu ra", [24, 30, 60], index=1)
            with p4:
                preset = st.selectbox("Encoder preset", ["ultrafast", "veryfast", "fast", "medium", "slow"], index=2)
            framing = st.selectbox("Cách khớp khung hình", ["Fit with bars (YouTube)", "Crop to fill (Shorts)" if aspect == "9:16 Shorts" else "Crop to fill"], index=0)
            crf = st.slider("Chất lượng (CRF thấp = file lớn hơn)", 16, 28, 20)
            trim_start = st.number_input("Bỏ qua đầu video (giây) – ví dụ 5s nếu OBS quay trước khi nhấn F5", min_value=0.0, max_value=3600.0, value=0.0, step=0.5)
            preserve_source_audio = st.checkbox("Giữ âm thanh gốc từ OBS", value=True)
            source_audio_volume = st.slider("Âm lượng audio gốc", 0.0, 2.0, 0.65, 0.05, disabled=not preserve_source_audio)
            export_scene_clips = st.checkbox("Xuất thêm từng cảnh thành clip riêng", value=True)

            if aspect == "9:16 Shorts":
                width, height = ((1080, 1920) if resolution == "1080p" else (2160, 3840))
                if framing == "Fit with bars (YouTube)":
                    st.warning("Với Shorts, nên chọn Crop to fill để lấp đầy khung dọc. Crop hiện dùng tâm khung, chưa tự nhận diện chủ thể.")
            else:
                width, height = ((1920, 1080) if resolution == "1080p" else (3840, 2160))

            st.info("Video sẽ được chia theo duration của từng scene trong Director Plan, chuẩn hóa cùng độ phân giải/FPS, sau đó nối lại. Căn thời gian phụ thuộc việc lúc quay bạn bắt đầu Scene Director đúng nhịp; dùng Trim start để bỏ phần đếm trước.")
            if st.button("🧩 Tạo Render Job + Windows Launcher", type="primary"):
                if not source_video.strip():
                    st.error("Nhập đường dẫn video OBS đầu vào.")
                elif not Path(source_video).expanduser().is_file():
                    st.error("Không tìm thấy file video đầu vào trên máy đang chạy Dashboard.")
                elif not scenes:
                    st.error("Director Plan không có cảnh để dựng.")
                elif not output_video.strip():
                    st.error("Nhập đường dẫn MP4 đầu ra.")
                else:
                    sound_cues = []
                    timeline_name = ""
                    if selected_timeline_label != "Không trộn cue âm thanh":
                        chosen_timeline = next(p for p in timeline_files if p.name == selected_timeline_label)
                        timeline_data = load_json(chosen_timeline, {})
                        sound_cues = timeline_data.get("cues", []) if isinstance(timeline_data, dict) else []
                        timeline_name = str(chosen_timeline)
                    manifest = {
                        "title": selected_director.get("title", title_default),
                        "director_plan": str(selected_director_path),
                        "sound_timeline": timeline_name,
                        "source_video": str(Path(source_video).expanduser()),
                        "output_video": str(Path(output_video).expanduser()),
                        "trim_start_seconds": float(trim_start),
                        "profile": {
                            "width": width, "height": height, "fps": int(fps), "crf": int(crf),
                            "preset": preset, "framing": framing
                        },
                        "ffmpeg_path": config.get("ffmpeg_path", "") or "ffmpeg",
                        "ffprobe_path": "",
                        "preserve_source_audio": bool(preserve_source_audio),
                        "source_audio_volume": float(source_audio_volume),
                        "export_scene_clips": bool(export_scene_clips),
                        "scenes": [{
                            "scene_number": int(sc.get("scene_number", i+1)),
                            "duration_seconds": float(sc.get("duration_seconds", 6) or 6),
                            "location": sc.get("location", "")
                        } for i, sc in enumerate(scenes)],
                        "sound_cues": sound_cues
                    }
                    jobs_dir = DATA / "video_jobs"
                    jobs_dir.mkdir(parents=True, exist_ok=True)
                    job_name = safe_filename(selected_director.get("title", "RobloxEpisode"))
                    manifest_path = jobs_dir / f"{job_name}_RenderManifest.json"
                    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                    helper_path = BASE / "video_factory_render.py"
                    bat_path = jobs_dir / f"{job_name}_RenderVideoFactory.bat"
                    helper_abs = str(helper_path.resolve())
                    manifest_abs = str(manifest_path.resolve())
                    bat = "@echo off\r\nsetlocal\r\n" + f'cd /d "{BASE}"\r\n' + f'py -3 "{helper_abs}" --manifest "{manifest_abs}"\r\n' + 'if errorlevel 1 (echo Render that bai. Xem loi phia tren.& pause & exit /b 1)\r\n' + 'echo Render hoan tat.& pause\r\nendlocal\r\n'
                    bat_path.write_text(bat, encoding="utf-8")
                    st.session_state["video_factory_job"] = {"manifest":str(manifest_path),"launcher":str(bat_path),"output":str(Path(output_video).expanduser()),"scenes":len(scenes),"duration":total_seconds}
                    st.success("Đã tạo Render Job. Hãy tải hoặc chạy file BAT trên Windows để render bằng FFmpeg.")

            job = st.session_state.get("video_factory_job")
            if job:
                st.subheader("Render Job hiện tại")
                st.json(job)
                for key, label in [("manifest", "Render Manifest JSON"), ("launcher", "Windows Render Launcher BAT")]:
                    path = Path(job[key])
                    if path.is_file():
                        st.download_button(f"⬇️ Tải {label}", data=path.read_bytes(), file_name=path.name, mime="application/json" if path.suffix == ".json" else "text/plain", key=f"vf_download_{key}")

    with tab_jobs:
        st.subheader("Lịch sử / file Video Factory")
        jobs_dir = DATA / "video_jobs"
        if jobs_dir.exists():
            manifests = sorted(jobs_dir.glob("*_RenderManifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if manifests:
                st.dataframe([{"Job":p.stem,"Đường dẫn":str(p),"Cập nhật":datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")} for p in manifests], use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có Render Job.")
        st.markdown("""
### Quy trình quay và dựng
1. Mở OBS Studio và bật **Tools → WebSocket Server Settings**. OBS 28 trở lên tích hợp sẵn WebSocket; giữ xác thực bằng password.
2. Cấu hình Host `127.0.0.1`, Port `4455` và password trong **Cài đặt**. Nhấn Kết nối / làm mới OBS.
3. Đảm bảo OBS có Game Capture/Display Capture trỏ tới Roblox Studio. Chuyển đúng OBS Program Scene nếu cần.
4. Nhấn Start Recording trong Dashboard, sau đó nhấn F5 trong Roblox Studio để chạy Scene Director.
5. Khi tập kết thúc, nhấn Stop & Import Recording. File quay được sao chép vào `exports/captures/`.
6. Mở Render & Export, chọn Director Plan và Sound Timeline, nhập file capture, cấu hình khung hình/chất lượng rồi tạo Render Job.
7. Chạy file `*_RenderVideoFactory.bat` trên Windows. Hệ thống xuất MP4 cuối và (nếu chọn) thư mục clip từng cảnh.

**Lưu ý:** Module này chưa tự nhấn F5 hoặc tự chạy Roblox Studio Play. Bạn cần bắt đầu Play thủ công sau khi OBS ghi hình. Việc chia cảnh dùng thời lượng trong Director Plan nên bản quay phải khớp nhịp; nếu có countdown/đợi trước khi vào cảnh, điều chỉnh Trim start. Shorts crop theo tâm khung, chưa tự tracking khuôn mặt/nhân vật. 4K yêu cầu máy có đủ năng lực encode và dung lượng đĩa.
""")


elif page == "Auto Publish":
    st.title("📤 AUTO PUBLISH")
    st.info("Bản 1.0 chỉ chuẩn bị metadata và checklist. Chưa tự đăng nhập hoặc tự xuất bản lên nền tảng.")
    with st.form("metadata"):
        video_title = st.text_input("YouTube title (English)")
        description = st.text_area("Description")
        tags = st.text_input("Tags, phân tách bằng dấu phẩy")
        if st.form_submit_button("Lưu metadata"):
            save_json(DATA/"publish_metadata.json", {"title":video_title,"description":description,"tags":[x.strip() for x in tags.split(",") if x.strip()]})
            st.success("Đã lưu metadata.")

elif page == "Cài đặt":
    st.title("⚙️ CÀI ĐẶT HỆ THỐNG")
    st.warning("OpenAI API key và OBS WebSocket password được lưu cục bộ trong data/config.json ở bản thử nghiệm. Không chia sẻ file cấu hình hoặc thư mục dự án có chứa khóa bí mật.")
    with st.form("settings"):
        api_key = st.text_input("OpenAI API key (để trống nếu chưa cấu hình)", value=config.get("openai_api_key",""), type="password")
        provider = st.selectbox("Nhà cung cấp hình ảnh", ["Chưa kết nối","Leonardo AI","Khác"], index=["Chưa kết nối","Leonardo AI","Khác"].index(config.get("image_provider","Chưa kết nối")))
        roblox_path = st.text_input("Đường dẫn đầy đủ tới file place .rbxl/.rbxlx (không bắt buộc)", value=config.get("roblox_place_path",""))
        studio_exe = st.text_input("Đường dẫn RobloxStudioBeta.exe (không bắt buộc)", value=config.get("roblox_studio_exe",""))
        obs_path = st.text_input("Đường dẫn OBS executable", value=config.get("obs_path",""))
        st.markdown("**OBS WebSocket (điều khiển quay từ Dashboard)**")
        obs_host = st.text_input("OBS WebSocket Host", value=config.get("obs_host", "127.0.0.1"))
        obs_port = st.number_input("OBS WebSocket Port", min_value=1, max_value=65535, value=int(config.get("obs_port", 4455)), step=1)
        obs_password = st.text_input("OBS WebSocket Password", value=config.get("obs_password", ""), type="password")
        ffmpeg_path = st.text_input("Đường dẫn FFmpeg executable", value=config.get("ffmpeg_path",""))
        output_dir = st.text_input("Thư mục xuất video", value=config.get("output_dir",str(BASE/"exports")))
        resolution = st.selectbox("Độ phân giải", ["1920x1080","3840x2160"], index=["1920x1080","3840x2160"].index(config.get("resolution","1920x1080")))
        fps = st.selectbox("FPS", [24,30,60], index=[24,30,60].index(config.get("fps",30)))
        if st.form_submit_button("Lưu cài đặt", type="primary"):
            config.update({"openai_api_key":api_key,"image_provider":provider,"roblox_place_path":roblox_path,"roblox_studio_exe":studio_exe,"obs_path":obs_path,"obs_host":obs_host.strip() or "127.0.0.1","obs_port":int(obs_port),"obs_password":obs_password,"ffmpeg_path":ffmpeg_path,"output_dir":output_dir,"resolution":resolution,"fps":fps})
            save_json(CONFIG, config)
            st.success("Đã lưu cài đặt.")
