
import io
import json
import uuid
import hmac
from datetime import datetime, timezone

import streamlit as st

st.set_page_config(page_title="RAVF Cloud", page_icon="🎬", layout="wide")

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default

APP_PASSWORD = get_secret("APP_PASSWORD")
OWNER_ID = get_secret("OWNER_ID", "owner")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
OPENAI_MODEL = get_secret("OPENAI_MODEL", "gpt-4.1-mini")
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = get_secret("SUPABASE_SERVICE_ROLE_KEY")

st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.3rem}
.hero{padding:1.5rem 1.7rem;border-radius:16px;background:linear-gradient(115deg,#14243c,#244f70);color:white;margin-bottom:1.2rem}
.hero h1{font-size:2rem;margin:0}.hero p{margin:.4rem 0 0;color:#d8e8f5}
.module{border:1px solid rgba(120,140,160,.3);border-radius:12px;padding:1rem;min-height:105px}
</style>
""", unsafe_allow_html=True)

if not APP_PASSWORD:
    st.title("ROBLOX AI VIDEO FACTORY · CLOUD")
    st.error("Cloud app chưa được mở khóa. Hãy thêm APP_PASSWORD vào Streamlit App settings → Secrets.")
    st.code('APP_PASSWORD = "choose-a-long-password"\nOPENAI_API_KEY = "your-openai-api-key"')
    st.stop()

if not st.session_state.get("authenticated"):
    st.title("🎬 ROBLOX AI VIDEO FACTORY · CLOUD")
    with st.form("login"):
        password = st.text_input("Mật khẩu truy cập", type="password")
        submitted = st.form_submit_button("Đăng nhập", type="primary")
    if submitted:
        if hmac.compare_digest(password or "", APP_PASSWORD):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Mật khẩu không đúng.")
    st.stop()

@st.cache_resource(show_spinner=False)
def supabase_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        return None

DB = supabase_client()
st.session_state.setdefault("records", [])

def now():
    return datetime.now(timezone.utc).isoformat()

def save_item(kind, title, payload, item_id=None):
    row = {
        "id": item_id or str(uuid.uuid4()),
        "owner_id": OWNER_ID,
        "kind": kind,
        "title": str(title or "Untitled")[:180],
        "payload": payload,
        "updated_at": now(),
    }
    if DB:
        DB.table("ravf_cloud_records").upsert(row, on_conflict="id").execute()
    else:
        rows = [x for x in st.session_state.records if x.get("id") != row["id"]]
        rows.insert(0, row)
        st.session_state.records = rows
    return row

def get_items(kind=None, limit=300):
    if DB:
        q = DB.table("ravf_cloud_records").select("id,owner_id,kind,title,payload,updated_at").eq("owner_id", OWNER_ID)
        if kind:
            q = q.eq("kind", kind)
        return q.order("updated_at", desc=True).limit(limit).execute().data or []
    return [x for x in st.session_state.records if not kind or x.get("kind") == kind][:limit]

def ai_json(system_prompt, payload):
    if not OPENAI_API_KEY:
        raise RuntimeError("Thêm OPENAI_API_KEY trong Streamlit Secrets trước khi dùng AI.")
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    result = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0.65,
    )
    return json.loads(result.choices[0].message.content or "{}")

def download_json(label, payload, filename, key):
    st.download_button(
        label,
        data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=filename,
        mime="application/json",
        key=key,
    )

def choose_item(rows, label, key):
    if not rows:
        st.info("Chưa có dữ liệu. Hãy tạo nội dung trước.")
        return None
    names = [f'{x.get("title", "Untitled")} · {x.get("id", "")[:8]}' for x in rows]
    choice = st.selectbox(label, names, key=key)
    return rows[names.index(choice)]

PAGES = [
    "Tổng quan", "AI Story", "Character AI", "World Builder", "Scene Director",
    "Sound Studio", "Thumbnail Studio", "SEO Manager", "Production Manager",
    "Quality Control", "Batch Production",
]
with st.sidebar:
    st.title("🎬 RAVF CLOUD")
    st.caption("ROBLOX AI VIDEO FACTORY 2.0")
    page = st.radio("ĐIỀU HƯỚNG", PAGES)
    st.divider()
    st.write("OpenAI: " + ("Ready" if OPENAI_API_KEY else "Not configured"))
    st.write("Supabase: " + ("Connected" if DB else "Session only"))
    if st.button("Đăng xuất", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

if not DB:
    st.warning("Chưa có Supabase. Dữ liệu hiện chỉ được giữ trong phiên Streamlit; hãy cấu hình Supabase để lưu bền vững.")

if page == "Tổng quan":
    st.markdown('<div class="hero"><h1>ROBLOX AI VIDEO FACTORY · CLOUD</h1><p>Cloud workspace for Roblox AI Stories and Windows Production Agent.</p></div>', unsafe_allow_html=True)
    rows = get_items(limit=500)
    kinds = [("story","Stories"),("character","Characters"),("world","World Plans"),("director","Director Plans"),("sound","Sound Timelines"),("seo","SEO Packages"),("job","Production Jobs"),("batch","Batch Items")]
    cols = st.columns(4)
    for i,(kind,label) in enumerate(kinds):
        cols[i%4].metric(label, sum(1 for r in rows if r.get("kind")==kind))
    st.subheader("Tạo Production Job")
    with st.form("quick_job"):
        title = st.text_input("Tên tập", placeholder="Noob Survives 99 Nights")
        series = st.selectbox("Series", ["Zombie Survival","Noob Life","99 Nights","Rich vs Poor","Escape Story","Original"])
        submitted = st.form_submit_button("Tạo Job", type="primary")
    if submitted:
        if title.strip():
            job = {"schema_version":"ravf.production-job.v1","job_id":str(uuid.uuid4()),"title":title.strip(),"series":series,"status":"queued","created_at":now(),"cloud_execution":False,"agent_requirements":["Roblox Studio","OBS Studio","FFmpeg"]}
            saved = save_item("job", title, job)
            st.success("Production Job đã tạo.")
            download_json("Tải Production Job JSON", saved, "production_job.json", "quick_job_json")
        else:
            st.error("Nhập tên tập phim.")
    st.subheader("Pipeline")
    modules = ["AI Story","Character AI","World Builder","Scene Director","Sound Studio","Thumbnail Studio","SEO Manager","Production Manager","Quality Control","Batch Production"]
    cols = st.columns(2)
    for i,name in enumerate(modules):
        cols[i%2].markdown(f'<div class="module"><b>{i+1:02d}. {name}</b></div>', unsafe_allow_html=True)

elif page == "AI Story":
    st.title("🧠 AI STORY")
    with st.form("story_form"):
        idea = st.text_input("Ý tưởng", placeholder="A Roblox Noob gets trapped in a zombie forest")
        series = st.selectbox("Series", ["Zombie Survival","Noob Life","99 Nights","Rich vs Poor","Escape Story","Original"])
        runtime = st.slider("Thời lượng (phút)", 1, 15, 5)
        scene_count = st.slider("Số cảnh", 10, 40, 24)
        tone = st.selectbox("Tone", ["Funny + adventurous","Suspenseful","Emotional","Horror-lite, non-graphic","Mixed"])
        extra = st.text_area("Chi tiết bổ sung")
        make = st.form_submit_button("✨ Tạo Story Bible", type="primary")
    if make:
        try:
            with st.spinner("AI đang viết kịch bản..."):
                story = ai_json(
                    "Write original family-friendly Roblox-like 3D animated stories for a US audience. Use American English. No copyrighted characters or creator imitation. No voiceover required. Return JSON keys title, logline, characters (array), story_beats (array), scenes (exact requested count; scene_number, location, duration_seconds, characters, visual_action, expression, camera, on_screen_text, music_and_sfx, transition), ending_hook, thumbnail_concept, style_notes.",
                    {"idea":idea,"series":series,"runtime_minutes":runtime,"scene_count":scene_count,"tone":tone,"extra":extra},
                )
                story["series"] = series
                story["runtime_minutes"] = runtime
                saved = save_item("story", story.get("title", idea), story)
            st.success("Story Bible đã lưu.")
            st.json(story)
            download_json("Tải Story JSON", story, "story_bible.json", "story_dl")
        except Exception as exc:
            st.error(f"AI Story lỗi: {exc}")
    rows = get_items("story")
    if rows:
        picked = choose_item(rows, "Story Library", "story_library")
        if picked:
            download_json("Tải story đã lưu", picked.get("payload", {}), "story_bible.json", "story_library_dl")

elif page == "Character AI":
    st.title("👥 CHARACTER AI")
    tab_ai, tab_manual = st.tabs(["AI Designer","Tạo thủ công"])
    with tab_ai:
        with st.form("character_ai"):
            concept = st.text_area("Mô tả nhân vật")
            role = st.selectbox("Vai trò", ["Main hero","Sidekick","Villain","Mentor","Comic relief","Supporting"])
            rig = st.selectbox("Kiểu rig", ["R6 blocky","R15 blocky","Stylized blocky"])
            make = st.form_submit_button("AI tạo Character Bible")
        if make:
            try:
                char = ai_json("Design an original family-friendly Roblox-style character. Return JSON: name, role, avatar_archetype, body_type, primary_colors, outfit_accessories, visual_description, personality, signature_expressions, signature_movement, recognition_props, continuity_rules, image_prompt. Make it reproducible with block-based geometry.", {"concept":concept,"role":role,"rig":rig})
                save_item("character", char.get("name","Character"), char)
                st.success("Character Bible đã lưu.")
                st.json(char)
                download_json("Tải Character JSON", char, "character_bible.json", "character_ai_dl")
            except Exception as exc:
                st.error(f"Character AI lỗi: {exc}")
    with tab_manual:
        with st.form("character_manual"):
            name = st.text_input("Tên")
            role_m = st.text_input("Vai trò")
            appearance = st.text_area("Ngoại hình")
            personality = st.text_area("Tính cách")
            rules = st.text_area("Quy tắc nhất quán")
            save = st.form_submit_button("Lưu nhân vật")
        if save:
            if name.strip():
                char = {"name":name.strip(),"role":role_m,"visual_description":appearance,"personality":personality,"continuity_rules":rules}
                save_item("character", name, char)
                st.success("Đã lưu.")
            else:
                st.error("Tên nhân vật là bắt buộc.")
    rows = get_items("character")
    if rows:
        st.subheader("Character Library")
        st.dataframe([{"Tên":r.get("title"),"ID":r.get("id"),"Cập nhật":r.get("updated_at")} for r in rows], use_container_width=True, hide_index=True)

elif page == "World Builder":
    st.title("🌍 WORLD BUILDER")
    with st.form("world_form"):
        name = st.text_input("Tên thế giới")
        environment = st.selectbox("Môi trường", ["Zombie Forest","Abandoned City","Island","School","Underground Bunker","Fantasy Realm"])
        size = st.selectbox("Kích thước (studs)", [200,300,400,600,800], index=2)
        mood = st.selectbox("Ánh sáng", ["Daylight","Sunset","Night","Foggy","Horror"])
        landmarks = st.text_area("Landmarks")
        make = st.form_submit_button("AI thiết kế World Plan", type="primary")
    if make:
        try:
            world = ai_json("Act as a Roblox block-based level designer. Return JSON: world_name, environment, map_size_studs, mood, spawn_point, landmarks (array of name, purpose, position_hint, dimensions_hint), routes, ambient_details, lighting, palette, asset_checklist, continuity_rules, luau_builder_notes. Do not claim to create an RBXL file.", {"name":name,"environment":environment,"size":size,"mood":mood,"landmarks":landmarks})
            save_item("world", world.get("world_name",name or "World Plan"), world)
            st.success("World Plan đã lưu.")
            st.json(world)
            download_json("Tải World Plan", world, "world_plan.json", "world_dl")
        except Exception as exc:
            st.error(f"World Builder lỗi: {exc}")
    rows = get_items("world")
    if rows:
        picked = choose_item(rows, "World Library", "world_library")
        if picked:
            download_json("Tải World Plan đã lưu", picked.get("payload", {}), "world_plan.json", "world_library_dl")

elif page == "Scene Director":
    st.title("🎬 SCENE DIRECTOR")
    stories = get_items("story")
    selected = choose_item(stories, "Chọn Story Bible", "director_story") if stories else None
    worlds = get_items("world")
    world = choose_item(worlds, "World Plan (tùy chọn)", "director_world") if worlds else None
    if selected and st.button("AI đạo diễn từng cảnh", type="primary"):
        try:
            plan = ai_json("You are a director for Roblox-style 3D animation. Return JSON with title and scenes. Every scene: scene_number, duration_seconds, location, characters, action, expression, camera (shot_type, movement, framing), on_screen_text, sound_notes, transition, continuity_notes. Preserve character names and visual identity.", {"story":selected.get("payload",{}),"world":world.get("payload",{}) if world else {}})
            plan["story_id"] = selected.get("id")
            plan["world_id"] = world.get("id") if world else None
            save_item("director", plan.get("title", selected.get("title","Director Plan")), plan)
            st.success("Director Plan đã lưu.")
            st.json(plan)
            download_json("Tải Director Plan", plan, "director_plan.json", "director_dl")
        except Exception as exc:
            st.error(f"Scene Director lỗi: {exc}")
    rows = get_items("director")
    if rows:
        picked = choose_item(rows, "Director Plans", "director_library")
        if picked:
            download_json("Tải Director Plan đã lưu", picked.get("payload", {}), "director_plan.json", "director_library_dl")

elif page == "Sound Studio":
    st.title("🎵 SOUND STUDIO")
    directors = get_items("director")
    selected = choose_item(directors, "Chọn Director Plan", "sound_director") if directors else None
    if selected and st.button("AI tạo Sound Timeline", type="primary"):
        try:
            timeline = ai_json("You are a sound designer. Return JSON with cues array. Each cue: scene_number, type (Music/Ambience/SFX/Transition), start_offset_seconds, duration_seconds, volume_0_to_1, fade_in_seconds, fade_out_seconds, loop, description, suggested_asset_search_terms. Never invent asset IDs or files.", {"director_plan":selected.get("payload",{})})
            timeline["director_id"] = selected.get("id")
            save_item("sound", selected.get("title","Sound Timeline"), timeline)
            st.success("Sound Timeline đã lưu.")
            st.json(timeline)
            download_json("Tải Sound Timeline", timeline, "sound_timeline.json", "sound_dl")
        except Exception as exc:
            st.error(f"Sound Studio lỗi: {exc}")
    rows = get_items("sound")
    if rows:
        picked = choose_item(rows, "Sound Library", "sound_library")
        if picked:
            download_json("Tải Sound Timeline đã lưu", picked.get("payload", {}), "sound_timeline.json", "sound_library_dl")

elif page == "Thumbnail Studio":
    st.title("🖼️ THUMBNAIL STUDIO")
    st.write("Tải ảnh nền hoặc ảnh chụp Roblox. Cloud không thể chụp trực tiếp cửa sổ Roblox Studio trên máy Windows.")
    uploaded = st.file_uploader("Ảnh JPG / PNG / WEBP", type=["jpg","jpeg","png","webp"])
    headline = st.text_input("Headline", "NOOB VS ZOMBIES")
    subtitle = st.text_input("Subtitle", "ROBLOX STORY")
    if uploaded and st.button("Tạo 3 thumbnail 1280×720", type="primary"):
        try:
            from PIL import Image, ImageDraw, ImageFont
            src = Image.open(uploaded).convert("RGB")
            target_ratio = 16/9
            if src.width/src.height > target_ratio:
                nw = int(src.height*target_ratio)
                left = (src.width-nw)//2
                src = src.crop((left,0,left+nw,src.height))
            else:
                nh = int(src.width/target_ratio)
                top = (src.height-nh)//2
                src = src.crop((0,top,src.width,top+nh))
            src = src.resize((1280,720))
            variants = []
            for i, style in enumerate(["bottom","left","top"]):
                image = src.copy()
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                if style == "bottom":
                    draw.rectangle((0,480,1280,720), fill=(0,0,0))
                    pos=(60,530)
                elif style == "left":
                    draw.rounded_rectangle((30,55,650,665), radius=25, fill=(14,24,40))
                    pos=(75,310)
                else:
                    draw.rectangle((0,0,1280,245), fill=(0,0,0))
                    pos=(55,90)
                draw.text(pos, headline.upper()[:55], fill=(255,220,45), font=font, stroke_width=2, stroke_fill=(0,0,0))
                draw.text((55,675 if style=="bottom" else 625), subtitle.upper()[:40], fill=(255,255,255), font=font)
                buf=io.BytesIO()
                image.save(buf, format="JPEG", quality=90, optimize=True)
                variants.append(buf.getvalue())
            st.session_state.thumbnail_variants = variants
            st.success("Đã tạo 3 phương án.")
        except Exception as exc:
            st.error(f"Thumbnail lỗi: {exc}")
    for i, data in enumerate(st.session_state.get("thumbnail_variants", [])):
        col = st.columns(3)[i]
        with col:
            st.image(data, caption=f"Variant {i+1}", use_container_width=True)
            st.download_button("Tải JPG", data=data, file_name=f"thumbnail_{i+1}.jpg", mime="image/jpeg", key=f"thumb_{i}")

elif page == "SEO Manager":
    st.title("📈 YOUTUBE SEO MANAGER")
    stories = get_items("story")
    selected = choose_item(stories, "Story nguồn (tùy chọn)", "seo_story") if stories else None
    summary = st.text_area("Tóm tắt video", value=(selected or {}).get("payload",{}).get("logline",""))
    fmt = st.radio("Định dạng", ["Long-form 16:9","Shorts 9:16"], horizontal=True)
    if st.button("AI tạo gói YouTube SEO", type="primary"):
        try:
            package = ai_json("You are a YouTube strategist for original Roblox story videos targeting the US. Return JSON: title_options (5), description, tags (12-20 without #), hashtags (3-5), thumbnail_text_options (5), thumbnail_image_prompts (3), pinned_comment. Natural American English. Avoid misleading claims and keyword stuffing.", {"summary":summary,"format":fmt,"story":selected.get("payload",{}) if selected else {}})
            package["format"] = fmt
            save_item("seo", (package.get("title_options") or ["SEO Package"])[0], package)
            st.success("YouTube SEO package đã lưu.")
            st.json(package)
            download_json("Tải YouTube Metadata", package, "youtube_metadata.json", "seo_dl")
        except Exception as exc:
            st.error(f"SEO Manager lỗi: {exc}")
    rows = get_items("seo")
    if rows:
        picked = choose_item(rows, "SEO Packages", "seo_library")
        if picked:
            download_json("Tải SEO package", picked.get("payload", {}), "youtube_metadata.json", "seo_library_dl")

elif page == "Production Manager":
    st.title("🧭 PRODUCTION MANAGER")
    kinds = [("story","Story"),("world","World Plan"),("director","Director Plan"),("sound","Sound Timeline")]
    options = {}
    for kind,label in kinds:
        rows = get_items(kind)
        options[kind] = choose_item(rows, label, f"manifest_{kind}") if rows else None
    title = st.text_input("Tên Production Job", "Roblox Episode")
    if st.button("Tạo Production Job JSON", type="primary"):
        character_rows = get_items("character")
        manifest = {
            "schema_version":"ravf.production-job.v1",
            "job_id":str(uuid.uuid4()),
            "title":title,
            "created_at":now(),
            "status":"queued",
            "source_record_ids":{k:(v.get("id") if v else None) for k,v in options.items()},
            "records":{
                "story": options["story"].get("payload") if options["story"] else None,
                "world": options["world"].get("payload") if options["world"] else None,
                "director": options["director"].get("payload") if options["director"] else None,
                "sound": options["sound"].get("payload") if options["sound"] else None,
                "characters":[r.get("payload", {}) for r in character_rows],
            },
            "steps":[{"name":n,"status":"pending"} for n in ["build_world","build_characters","run_director","record_obs","render_ffmpeg","qc","publish"]],
            "execution_target":"windows_agent",
            "agent_requirements":["Roblox Studio","OBS Studio","FFmpeg"],
            "note":"Cloud exports this complete job manifest. Roblox Studio, OBS and FFmpeg execute on the Windows Agent."
        }
        saved=save_item("job",title,manifest)
        st.success("Production Job đã tạo.")
        download_json("Tải Production Job", saved, "production_job.json", "prod_job_dl")
    jobs=get_items("job")
    if jobs:
        st.dataframe([{"Tên":r.get("title"),"Trạng thái":r.get("payload",{}).get("status"),"ID":r.get("id")} for r in jobs],use_container_width=True,hide_index=True)

elif page == "Quality Control":
    st.title("🛡️ QUALITY CONTROL")
    kind=st.selectbox("Loại dữ liệu",["story","character","world","director","sound","seo","job"])
    rows=get_items(kind)
    selected=choose_item(rows,"Chọn đối tượng QC","qc_target") if rows else None
    if selected and st.button("Chạy kiểm tra",type="primary"):
        p=selected.get("payload",{})
        checks=[]
        def add(label,ok,detail):
            checks.append({"check":label,"result":"PASS" if ok else "WARNING","detail":detail})
        if kind=="story":
            scenes=p.get("scenes",[])
            add("Title",bool(p.get("title")),"Story title")
            add("Scene count",10<=len(scenes)<=40,f"{len(scenes)} scenes")
            add("Scene durations",bool(scenes) and all(float(x.get("duration_seconds",0) or 0)>0 for x in scenes),"All scenes should have positive duration")
            add("Characters",bool(p.get("characters")),"Character list")
        elif kind=="director":
            scenes=p.get("scenes",[])
            add("Scenes",bool(scenes),f"{len(scenes)} scenes")
            add("Camera",bool(scenes) and all(bool(x.get("camera")) for x in scenes),"Every scene should specify camera")
        elif kind=="character":
            add("Visual description",bool(p.get("visual_description")),"Appearance continuity")
            add("Continuity rules",bool(p.get("continuity_rules")),"Character identity rules")
        elif kind=="world":
            add("Spawn",bool(p.get("spawn_point")),"World spawn")
            add("Landmarks",bool(p.get("landmarks")),"World landmarks")
        elif kind=="sound":
            add("Cues",bool(p.get("cues")),"Audio cue list")
        elif kind=="seo":
            titles=p.get("title_options",[])
            add("Title length",bool(titles) and all(len(str(t))<=100 for t in titles),"YouTube titles should be 100 characters or less")
            add("Description",bool(p.get("description")),"Video description")
        else:
            add("Job schema",p.get("schema_version")=="ravf.production-job.v1","Production job contract")
        report={"record_id":selected.get("id"),"kind":kind,"checked_at":now(),"checks":checks,"passed":sum(x["result"]=="PASS" for x in checks),"warnings":sum(x["result"]!="PASS" for x in checks)}
        save_item("qc",f'QC {selected.get("title",kind)}',report)
        st.session_state.last_qc=report
    if st.session_state.get("last_qc"):
        report=st.session_state.last_qc
        a,b=st.columns(2)
        a.metric("PASS",report["passed"])
        b.metric("WARNING",report["warnings"])
        st.dataframe(report["checks"],use_container_width=True,hide_index=True)
        download_json("Tải QC Report",report,"qc_report.json","qc_dl")

elif page == "Batch Production":
    st.title("📚 BATCH PRODUCTION")
    with st.form("batch_form"):
        title=st.text_input("Tên tập / chủ đề")
        series=st.selectbox("Series",["Zombie Survival","Noob Life","99 Nights","Rich vs Poor","Escape Story","Original"])
        priority=st.selectbox("Ưu tiên",["Normal","High","Low"])
        add=st.form_submit_button("Thêm vào hàng đợi")
    if add:
        if title.strip():
            item={"batch_id":str(uuid.uuid4()),"title":title.strip(),"series":series,"priority":priority,"status":"queued","created_at":now()}
            save_item("batch",title,item)
            st.success("Đã thêm vào hàng đợi.")
        else:
            st.error("Nhập tên tập.")
    rows=get_items("batch")
    if rows:
        queue={"schema_version":"ravf.batch-queue.v1","created_at":now(),"items":[r.get("payload",{}) for r in rows]}
        st.dataframe(queue["items"],use_container_width=True,hide_index=True)
        download_json("Tải Batch Queue JSON",queue,"batch_queue.json","batch_dl")
