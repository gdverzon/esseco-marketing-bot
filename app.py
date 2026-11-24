from __future__ import annotations

import json
import logging
import sqlite3

import streamlit as st

from codex_bot.codex_runner import CodexError, codex_available, run_codex
from codex_bot.config import ROOT, Settings
from codex_bot.database import Database
from codex_bot.exports import (
    marketing_content_to_csv,
    marketing_content_to_markdown,
    messages_to_csv,
    messages_to_markdown,
    records_to_json,
)
from codex_bot.logging_config import configure_logging
from codex_bot.knowledge import (
    load_knowledge,
    read_knowledge_file,
    save_markdown_knowledge,
    save_products,
)
from codex_bot.marketing_service import MarketingRequest, MarketingService
from codex_bot.marketing_manager import MarketingManager
from codex_bot.models import MarketingTaskRequest, PLATFORMS
from codex_bot.prompts import chat_prompt, marketing_prompt
from codex_bot.scheduler import ScheduleRequest, build_schtasks_command, register_task
from skills.analytics import analyze_content
from skills.registry import SKILLS
from workflows import ContentWorkflow, WorkflowRequest


st.set_page_config(page_title="Codex Bot", page_icon="◈", layout="wide")
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(circle at 75% 0%, #172554 0, #080b12 35%, #06080d 100%); }
[data-testid="stSidebar"] { background: #0b0f19; border-right: 1px solid #1d2939; }
.hero {padding: 1.2rem 1.4rem; border: 1px solid #263244; border-radius: 18px;
       background: linear-gradient(135deg, rgba(30,41,59,.85), rgba(11,15,25,.92)); margin-bottom: 1rem;}
.hero h1 {margin: 0; font-size: 2rem; letter-spacing: -.04em;}
.hero p {color: #94a3b8; margin: .35rem 0 0;}
.status {display:inline-block; padding:.2rem .6rem; border-radius:99px; font-size:.8rem;
         background:#102a22; color:#6ee7b7; border:1px solid #185c48;}
.stButton button {border-radius: 10px;}
[data-testid="stMetric"] {background:#101621; padding:1rem; border-radius:14px; border:1px solid #243044;}
</style>
""", unsafe_allow_html=True)

settings = Settings.from_env()
settings.ensure_directories()
logger = configure_logging(settings.log_dir)


@st.cache_resource
def get_database(path: str) -> Database:
    return Database(path)


db = get_database(str(settings.db_path))
workflow = ContentWorkflow(ROOT, settings.codex_timeout)
marketing_service = MarketingService(db, ROOT, settings.codex_timeout, logger=logger)
marketing_manager = MarketingManager(db, ROOT, settings.codex_timeout, logger=logger)

if not db.get_business_profile():
    db.upsert_business_profile({"name":"Esse Co Handcrafted Essentials","industry":"Handcrafted essentials and personal care",
        "market":"Philippines","business_model":"Online retail","languages":["English","Filipino","Taglish"],
        "timezone":"Asia/Manila","brand_personality":"Friendly, authentic, caring, trustworthy, and professional"})
if not db.list_products():
    for product in json.loads((ROOT/"knowledge"/"products.json").read_text(encoding="utf-8"))["products"]:
        db.save_product(product)


def generate(prompt: str) -> str | None:
    try:
        with st.spinner("Codex is thinking…"):
            answer = run_codex(prompt, ROOT, settings.codex_timeout).text
        logger.info("Generation completed (%d characters)", len(answer))
        return answer
    except (CodexError, ValueError) as exc:
        logger.exception("Generation failed")
        st.error(str(exc))
        return None


with st.sidebar:
    st.markdown("## ◈ Codex Bot")
    page = st.radio(
        "Workspace",
        ["Overview", "AI marketing", "Chat", "Content studio", "Calendar", "SEO & listings", "Campaigns",
         "Products", "Approval queue", "Content history", "Content library", "Knowledge base", "Skills lab", "Analytics", "Settings", "Scheduler", "Activity"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("CODEX CLI")
    if codex_available():
        st.markdown('<span class="status">● Ready · read-only sandbox</span>', unsafe_allow_html=True)
    else:
        st.warning("Codex CLI not found")
    st.caption("Local data · SQLite · Human-approved actions")

st.markdown('<div class="hero"><h1>Codex Bot</h1><p>Your private, local-first marketing copilot.</p></div>', unsafe_allow_html=True)

if page == "Overview":
    st.subheader("Esse Co marketing overview")
    counts=db.overview_counts()
    with st.container(horizontal=True):
        st.metric("Products",counts["products"],border=True)
        st.metric("Generated content",counts["content"],border=True)
        st.metric("Awaiting approval",counts["pending"],border=True)
        st.metric("Approved",counts["approved"],border=True)
        st.metric("Campaigns",counts["campaigns"],border=True)
    if counts["content"] == 0: st.info("No generated marketing content yet. Start in AI marketing or Content studio.")
    else: st.dataframe(db.list_generated_content(limit=10),hide_index=True,alt="Recent generated marketing content")

elif page == "AI marketing":
    st.subheader("AI marketing manager")
    st.caption("Describe the outcome. The manager routes it to one specialist, validates the result, and sends it for approval.")
    products=db.list_products(); product_names={None:"No product"}|{p["id"]:p["name"] for p in products}
    with st.form("manager_form"):
        request_text=st.text_area("Marketing request",placeholder="Create a Taglish TikTok script introducing our massage oils without medical claims.")
        skill=st.selectbox("Skill",["auto",*SKILLS],format_func=lambda x:"Automatic routing" if x=="auto" else SKILLS[x].label)
        platform=st.selectbox("Platform",list(PLATFORMS))
        product_id=st.selectbox("Product",list(product_names),format_func=product_names.get)
        language=st.selectbox("Language",["English","Filipino","Taglish"])
        extra=st.text_area("Verified additional context")
        run_manager=st.form_submit_button("Generate for review",icon=":material/auto_awesome:",type="primary")
    if run_manager:
        try:
            with st.spinner("Routing, generating, and validating…"):
                cid,data=marketing_manager.execute(MarketingTaskRequest(request_text,skill,platform,product_id,product_names.get(product_id,""),language,extra_context=extra))
            st.success(f"Validated content #{cid} was sent to the approval queue.")
            st.json(data)
        except Exception as exc:
            logger.exception("AI marketing manager request failed")
            st.error(str(exc))

elif page == "Chat":
    conversations = db.list_conversations()
    left, right = st.columns([1, 3])
    with left:
        if st.button("New conversation", icon=":material/add:", width="stretch"):
            st.session_state.conversation_id = db.create_conversation("New conversation")
            st.rerun()
        if conversations:
            ids = [row["id"] for row in conversations]
            current = st.session_state.get("conversation_id", ids[0])
            if current not in ids:
                current = ids[0]
            labels = {row["id"]: row["title"] for row in conversations}
            chosen = st.selectbox("History", ids, index=ids.index(current), format_func=labels.get)
            st.session_state.conversation_id = chosen
            if st.button("Delete conversation", icon=":material/delete:", width="stretch"):
                db.delete_conversation(chosen)
                st.session_state.pop("conversation_id", None)
                st.rerun()
        else:
            st.info("Start a conversation to build your local history.")
    with right:
        conversation_id = st.session_state.get("conversation_id")
        messages = db.get_messages(conversation_id) if conversation_id else []
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if user_text := st.chat_input("Ask Codex Bot…"):
            if not conversation_id:
                conversation_id = db.create_conversation(user_text[:60])
                st.session_state.conversation_id = conversation_id
            db.add_message(conversation_id, "user", user_text)
            context = db.get_messages(conversation_id, settings.max_history_messages)
            if answer := generate(chat_prompt(context)):
                db.add_message(conversation_id, "assistant", answer)
            st.rerun()
        if messages:
            title = next((c["title"] for c in conversations if c["id"] == conversation_id), "Conversation")
            col1, col2 = st.columns(2)
            col1.download_button("Download Markdown", messages_to_markdown(title, messages), "conversation.md", "text/markdown", width="stretch")
            col2.download_button("Download CSV", messages_to_csv(messages), "conversation.csv", "text/csv", width="stretch")

elif page == "Content studio":
    st.subheader("Marketing content studio")
    st.caption("Every successful generation is saved locally as a draft and must be approved before publication.")
    generator = st.segmented_control(
        "Generator",
        ["Facebook captions", "Product description", "Hashtags", "Seven-day calendar", "Marketing copy"],
        default="Facebook captions",
        key="content_generator",
    )
    definitions = {
        "Facebook captions": ("facebook_caption", "Post topic", "Objective", "Facebook captions"),
        "Product description": ("product_description", "Product name", "Channel or objective", "Product description"),
        "Hashtags": ("hashtags", "Topic", "Optional context", "Hashtag set"),
        "Seven-day calendar": ("content_calendar", "Weekly goal", "Channels", "Seven-day content calendar"),
    }
    if generator == "Marketing copy":
        with st.form("marketing_copy_form"):
            title = st.text_input("Asset title", "Marketing copy")
            brief = st.text_area("Offer and brief")
            audience = st.text_input("Target audience")
            submit_marketing = st.form_submit_button("Generate and save draft", icon=":material/auto_awesome:", type="primary")
        if submit_marketing:
            try:
                prompt = marketing_prompt("marketing", {"offer": brief, "audience": audience})
                prompt += f"\n\nApproved business knowledge:\n{load_knowledge(ROOT / 'knowledge')}"
                if answer := generate(prompt):
                    content_id = db.create_marketing_content("marketing_copy", title, answer, brief)
                    st.session_state["latest_marketing_result"] = (content_id, answer)
                    st.success(f"Saved draft #{content_id}.")
            except (ValueError, sqlite3.Error, OSError) as exc:
                logger.exception("Could not save marketing copy")
                st.error(str(exc))
    elif generator:
        content_type, subject_label, context_label, default_title = definitions[generator]
        with st.form("dedicated_generator_form"):
            title = st.text_input("Asset title", default_title)
            subject = st.text_area(subject_label)
            context = st.text_input(context_label)
            hashtag_count = st.slider("Number of hashtags", 3, 30, 10, disabled=content_type != "hashtags")
            submitted = st.form_submit_button("Generate and save draft", icon=":material/auto_awesome:", type="primary")
        if submitted:
            try:
                request = MarketingRequest(content_type, title, subject, context, hashtag_count)
                with st.spinner("Codex is creating your draft…"):
                    content_id, answer = marketing_service.generate_and_save(request)
                st.session_state["latest_marketing_result"] = (content_id, answer)
                st.success(f"Saved draft #{content_id}.")
            except (CodexError, ValueError, sqlite3.Error, OSError) as exc:
                logger.exception("Marketing generation failed")
                st.error(str(exc))
    if latest := st.session_state.get("latest_marketing_result"):
        content_id, result = latest
        st.markdown(f"#### Draft #{content_id}")
        st.markdown(result)
        st.download_button("Export this draft", result, f"marketing-draft-{content_id}.md", "text/markdown")

elif page == "Calendar":
    st.subheader("Marketing calendar generator")
    with st.form("calendar_form"):
        duration=st.segmented_control("Duration",[7,30],default=7,format_func=lambda x:f"{x} days")
        start=st.date_input("Start date")
        platforms=st.multiselect("Platforms",list(PLATFORMS),default=["Facebook"])
        objective=st.text_area("Calendar objective")
        make_calendar=st.form_submit_button("Generate calendar",type="primary",icon=":material/calendar_month:")
    if make_calendar:
        text=f"Create a {duration}-day calendar starting {start.isoformat()} for {', '.join(platforms)}. Objective: {objective}. Include every required calendar field."
        try:
            cid,data=marketing_manager.execute(MarketingTaskRequest(text,"content_calendar","Multi-platform",language="English",start_date=start.isoformat(),duration_days=duration))
            st.success(f"Calendar content #{cid} is awaiting approval."); st.json(data)
        except Exception as exc: st.error(str(exc))
    calendar_platform=st.selectbox("Filter calendar platform",["All",*PLATFORMS])
    calendars=db.list_calendar_entries(None if calendar_platform=="All" else calendar_platform)
    if calendars: st.dataframe(calendars,hide_index=True,alt="Saved marketing calendar entries")
    else: st.info("No saved calendars yet.")

elif page == "SEO & listings":
    st.subheader("SEO and marketplace listing tools")
    tool=st.segmented_control("Tool",["SEO keywords","Shopee listing","Lazada listing"],default="SEO keywords")
    mapping={"SEO keywords":"seo_keywords","Shopee listing":"shopee_listing","Lazada listing":"lazada_listing"}
    products=db.list_products(); names={p["id"]:p["name"] for p in products}
    with st.form("listing_form"):
        pid=st.selectbox("Product",list(names),format_func=names.get) if names else None
        brief=st.text_area("Verified brief")
        submit_listing=st.form_submit_button("Generate optimized draft",type="primary")
    if submit_listing:
        try:
            platform="Shopee" if tool=="Shopee listing" else "Lazada" if tool=="Lazada listing" else "Multi-platform"
            cid,data=marketing_manager.execute(MarketingTaskRequest(brief,mapping[tool],platform,pid,names.get(pid,"")))
            st.success(f"Draft #{cid} is awaiting approval."); st.json(data)
        except Exception as exc: st.error(str(exc))

elif page == "Campaigns":
    st.subheader("Campaign manager")
    with st.form("campaign_form"):
        cname=st.text_input("Campaign name"); objective=st.text_area("Objective")
        channels=st.multiselect("Platforms",list(PLATFORMS)); start=st.date_input("Start"); end=st.date_input("End")
        create_campaign=st.form_submit_button("Create campaign plan",type="primary")
    if create_campaign:
        try:
            cid,data=marketing_manager.execute(MarketingTaskRequest(f"Campaign {cname}: {objective}. Dates {start} to {end}. Platforms {channels}","campaign_planning","Multi-platform"))
            with db.connect() as connection:
                connection.execute("INSERT INTO campaigns(name,objective,platforms_json,start_date,end_date,strategy_json) VALUES (?,?,?,?,?,?)",(cname,objective,json.dumps(channels),start.isoformat(),end.isoformat(),json.dumps(data)))
            st.success(f"Campaign plan saved; content #{cid} awaits approval.")
        except Exception as exc: st.error(str(exc))

elif page == "Products":
    st.subheader("Product management")
    products=db.list_products()
    if products: st.dataframe(products,hide_index=True,alt="Esse Co products")
    with st.form("product_form"):
        pname=st.text_input("Product name"); category=st.text_input("Category"); description=st.text_area("Verified description")
        ingredients=st.text_input("Verified ingredients or materials (comma-separated)")
        variants=st.text_input("Verified variants (comma-separated)"); price=st.number_input("Price (PHP; 0 means unknown)",min_value=0.0)
        stock=st.text_input("Stock status (leave blank if unknown)"); verified=st.checkbox("I confirm these details are verified")
        save_product=st.form_submit_button("Add product",type="primary")
    if save_product:
        try:
            pid=db.save_product({"name":pname,"category":category,"description":description,"ingredients":[x.strip() for x in ingredients.split(',') if x.strip()],"variants":[x.strip() for x in variants.split(',') if x.strip()],"price":price or None,"stock_status":stock or None,"verified":verified})
            st.success(f"Product #{pid} saved."); st.rerun()
        except Exception as exc: st.error(str(exc))

elif page == "Approval queue":
    st.subheader("Approval queue")
    records=db.list_generated_content("pending_approval")
    if not records: st.info("No content is waiting for approval.")
    for record in records:
        with st.container(border=True):
            edited_title=st.text_input("Title",record["title"],key=f"edit_title_{record['id']}")
            edited_caption=st.text_area("Content",record["caption"] or record["structured_json"],key=f"edit_caption_{record['id']}")
            st.caption(f"{record['platform']} · {record['content_type']}")
            note=st.text_input("Review note",key=f"note_{record['id']}")
            with st.container(horizontal=True):
                if st.button("Save edits",key=f"save_content_{record['id']}"):
                    db.update_generated_content(record["id"],edited_title,edited_caption); st.rerun()
                if record["content_type"] in SKILLS and st.button("Regenerate",key=f"regenerate_{record['id']}"):
                    marketing_manager.execute(MarketingTaskRequest(f"Regenerate and improve: {edited_caption}",record["content_type"],record["platform"],record["product_id"])); st.rerun()
                if st.button("Approve",key=f"v2_approve_{record['id']}",type="primary"):
                    db.transition_generated_content(record["id"],"approved",note); st.rerun()
                if st.button("Reject",key=f"v2_reject_{record['id']}"):
                    db.transition_generated_content(record["id"],"rejected",note); st.rerun()

elif page == "Content history":
    st.subheader("Content history")
    with st.container(horizontal=True):
        hstatus=st.selectbox("Status",["All","draft","pending_approval","approved","rejected","scheduled","published"])
        hplatform=st.selectbox("Platform",["All",*PLATFORMS,"Multi-platform"])
    records=db.list_generated_content(None if hstatus=="All" else hstatus,None if hplatform=="All" else hplatform)
    if not records: st.info("No matching content history.")
    else:
        st.dataframe(records,hide_index=True,alt="Generated marketing content history")
        with st.container(horizontal=True):
            st.download_button("Export CSV",marketing_content_to_csv([{"body":r["caption"],"status":r["approval_status"],"brief":"",**r} for r in records]),"esseco-content.csv","text/csv")
            st.download_button("Export JSON",records_to_json(records),"esseco-content.json","application/json")
            st.download_button("Export Markdown",marketing_content_to_markdown([{"body":r["caption"],"status":r["approval_status"],**r} for r in records]),"esseco-content.md","text/markdown")
        actionable=[r for r in records if r["approval_status"] in {"approved","scheduled"}]
        if actionable:
            action_ids={r["id"]:f"#{r['id']} {r['title']} ({r['approval_status']})" for r in actionable}
            selected_action=st.selectbox("Update publication status",list(action_ids),format_func=action_ids.get)
            selected_record=next(r for r in actionable if r["id"]==selected_action)
            if selected_record["approval_status"]=="approved" and st.button("Mark as scheduled"):
                db.transition_generated_content(selected_action,"scheduled","Owner scheduled content externally"); st.rerun()
            if selected_record["approval_status"]=="scheduled":
                confirmed=st.checkbox("I confirm this content was actually published externally")
                if st.button("Confirm published",disabled=not confirmed):
                    db.transition_generated_content(selected_action,"published","Owner confirmed actual publication"); st.rerun()

elif page == "Content library":
    st.subheader("Saved marketing content")
    with st.container(horizontal=True, vertical_alignment="bottom"):
        status_filter = st.selectbox(
            "Status", ["All", "draft", "pending_approval", "approved", "rejected"], key="library_status"
        )
        type_filter = st.selectbox(
            "Content type",
            ["All", "facebook_caption", "product_description", "hashtags", "content_calendar", "marketing_copy"],
            key="library_type",
        )
    records = db.list_marketing_content(
        None if status_filter == "All" else status_filter,
        None if type_filter == "All" else type_filter,
    )
    if not records:
        st.info("No saved content matches these filters.")
    else:
        with st.container(horizontal=True):
            st.download_button(
                "Export CSV", marketing_content_to_csv(records), "marketing-content.csv", "text/csv", icon=":material/download:"
            )
            st.download_button(
                "Export Markdown",
                marketing_content_to_markdown(records),
                "marketing-content.md",
                "text/markdown",
                icon=":material/download:",
            )
        for record in records:
            with st.container(border=True):
                st.markdown(f"#### {record['title']}")
                st.caption(f"#{record['id']} · {record['content_type']} · {record['status']} · {record['created_at']}")
                st.markdown(record["body"])
                with st.container(horizontal=True):
                    if record["status"] == "draft" and st.button(
                        "Submit for approval", key=f"submit_content_{record['id']}", icon=":material/rate_review:"
                    ):
                        db.transition_marketing_content(record["id"], "pending_approval")
                        logger.info("Content submitted for approval: id=%s", record["id"])
                        st.rerun()
                    if record["status"] == "pending_approval":
                        if st.button("Approve", key=f"approve_content_{record['id']}", type="primary", icon=":material/check:"):
                            db.transition_marketing_content(record["id"], "approved")
                            logger.info("Content approved: id=%s", record["id"])
                            st.rerun()
                        if st.button("Reject", key=f"reject_content_{record['id']}", icon=":material/close:"):
                            db.transition_marketing_content(record["id"], "rejected")
                            logger.info("Content rejected: id=%s", record["id"])
                            st.rerun()
                    if record["status"] == "rejected" and st.button(
                        "Return to draft", key=f"redraft_content_{record['id']}", icon=":material/edit:"
                    ):
                        db.transition_marketing_content(record["id"], "draft")
                        st.rerun()
        st.info("Approval records review readiness only. Codex Bot never publishes content automatically.")

elif page == "Knowledge base":
    st.subheader("Marketing knowledge base")
    st.warning("Store business facts only. Do not enter credentials, private customer data, or regulated information.")
    knowledge_choice = st.segmented_control(
        "Section", ["Business", "Products", "Target audience", "Brand voice", "Marketing goals", "Platform guidelines", "FAQ"], default="Business", key="knowledge_section"
    )
    knowledge_files = {
        "Business": "business.md",
        "Target audience": "target_audience.md",
        "Brand voice": "brand_voice.md",
        "Marketing goals": "marketing_goals.md",
        "Platform guidelines": "platform_guidelines.md",
        "FAQ": "faq.md",
    }
    if knowledge_choice == "Products":
        current_products = read_knowledge_file(ROOT / "knowledge", "products.json")
        with st.form("products_knowledge_form"):
            product_json = st.text_area("Product catalog JSON", current_products, height=400)
            save_product_data = st.form_submit_button("Validate and save products", icon=":material/save:", type="primary")
        if save_product_data:
            try:
                saved = save_products(ROOT / "knowledge", product_json)
                logger.info("Product knowledge updated: %d products", len(saved["products"]))
                st.success(f"Saved {len(saved['products'])} products.")
            except (ValueError, OSError) as exc:
                logger.exception("Product knowledge update failed")
                st.error(str(exc))
    elif knowledge_choice:
        filename = knowledge_files[knowledge_choice]
        current_text = read_knowledge_file(ROOT / "knowledge", filename)
        with st.form("markdown_knowledge_form"):
            knowledge_text = st.text_area(f"{knowledge_choice} knowledge", current_text, height=400)
            save_knowledge = st.form_submit_button("Save knowledge", icon=":material/save:", type="primary")
        if save_knowledge:
            try:
                save_markdown_knowledge(ROOT / "knowledge", filename, knowledge_text)
                logger.info("Knowledge updated: %s", filename)
                st.success(f"Saved {knowledge_choice.lower()} knowledge.")
            except (ValueError, OSError) as exc:
                logger.exception("Knowledge update failed: %s", filename)
                st.error(str(exc))

elif page == "Analytics":
    st.subheader("Marketing analytics")
    st.caption("Metrics are manual stored observations; Codex Bot does not fetch platform analytics in Phase 1.")
    metrics=db.list_metrics()
    if metrics:
        st.dataframe(metrics,hide_index=True,alt="Stored marketing metrics")
        totals={key:sum((row.get(key) or 0) for row in metrics) for key in ("reach","impressions","engagements","clicks","inquiries","orders")}
        with st.container(horizontal=True):
            for key,value in totals.items(): st.metric(key.title(),value,border=True)
    else: st.info("No marketing metrics have been recorded yet.")
    with st.form("metric_form"):
        metric_date=st.date_input("Metric date"); metric_platform=st.selectbox("Platform",list(PLATFORMS))
        reach=st.number_input("Reach",min_value=0); impressions=st.number_input("Impressions",min_value=0)
        engagements=st.number_input("Engagements",min_value=0); inquiries=st.number_input("Inquiries",min_value=0)
        orders=st.number_input("Orders",min_value=0); sales=st.number_input("Sales (PHP)",min_value=0.0)
        add_metric=st.form_submit_button("Save observed metrics",type="primary")
    if add_metric:
        db.add_metric({"metric_date":metric_date.isoformat(),"platform":metric_platform,"reach":reach,"impressions":impressions,"engagements":engagements,"inquiries":inquiries,"orders":orders,"sales":sales})
        st.success("Metrics saved."); st.rerun()

elif page == "Settings":
    st.subheader("Business settings")
    profile=db.get_business_profile() or {}
    with st.form("business_settings"):
        bname=st.text_input("Business name",profile.get("name","")); industry=st.text_input("Industry",profile.get("industry",""))
        market=st.text_input("Market",profile.get("market","Philippines")); model=st.text_input("Business model",profile.get("business_model","Online retail"))
        languages=st.text_input("Languages",", ".join(json.loads(profile.get("languages_json","[]"))))
        personality=st.text_area("Brand personality",profile.get("brand_personality","")); timezone=st.text_input("Timezone",profile.get("timezone","Asia/Manila"),disabled=True)
        save_settings=st.form_submit_button("Save business profile",type="primary")
    if save_settings:
        db.upsert_business_profile({"name":bname,"industry":industry,"market":market,"business_model":model,"languages":[x.strip() for x in languages.split(',') if x.strip()],"timezone":"Asia/Manila","brand_personality":personality})
        st.success("Business profile saved.")
    st.info("Codex uses the authenticated CLI. No API key is stored by this application.")

elif page == "Skills lab":
    st.subheader("Specialist workflows")
    st.caption("Each workflow combines a focused skill with your local knowledge files.")
    with st.form("skills_form"):
        skill = st.selectbox(
            "Specialist",
            ["Content writer", "SEO specialist", "Campaign planner", "Market researcher"],
        )
        subject = st.text_area("Goal, topic, or brief", placeholder="Describe the result you need.")
        audience = st.text_input("Audience, market, or channels")
        format_or_duration = st.text_input("Format or duration", placeholder="For example: Facebook post or four weeks")
        run_skill = st.form_submit_button("Run specialist", icon=":material/auto_awesome:", type="primary")
    if run_skill:
        try:
            request = WorkflowRequest(skill, subject, audience, format_or_duration)
            if answer := generate(workflow.build_prompt(request)):
                st.session_state["skills_result"] = answer
        except ValueError as exc:
            st.error(str(exc))
    if result := st.session_state.get("skills_result"):
        st.markdown(result)
        metrics = analyze_content(result)
        metric_columns = st.columns(4)
        metric_columns[0].metric("Words", metrics["words"], border=True)
        metric_columns[1].metric("Sentences", metrics["sentences"], border=True)
        metric_columns[2].metric("Hashtags", metrics["hashtags"], border=True)
        metric_columns[3].metric("Reading time", f"{metrics['estimated_reading_minutes']} min", border=True)
        st.download_button("Export result", result, "specialist-result.md", "text/markdown")

elif page == "Scheduler":
    st.subheader("Weekly scheduled generation")
    st.info("Creating a Windows task changes your system. Codex Bot always stages it first; you must explicitly approve registration.")
    with st.form("schedule_form"):
        name = st.text_input("Task name", "Weekly content calendar")
        weekday = st.selectbox("Day", ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"])
        time = st.text_input("Time (24-hour HH:MM)", "09:00")
        prompt = st.text_area("Generation prompt", "Create a seven-day marketing content calendar for my business.")
        stage = st.form_submit_button("Stage for approval", type="primary")
    if stage:
        try:
            request = ScheduleRequest(name, weekday, time, prompt)
            command = build_schtasks_command(request, ROOT)
            approval_id = db.create_approval("windows_task_scheduler", json.dumps(command))
            logger.info("Scheduled task staged for approval: %s", approval_id)
            st.success("Task staged. Review and approve it below.")
        except ValueError as exc:
            st.error(str(exc))
    pending = db.list_approvals("pending")
    for item in pending:
        with st.container(border=True):
            st.write(f"**Pending:** {item['action_type']} · request #{item['id']}")
            command = json.loads(item["payload"])
            st.code(" ".join(command), language="powershell")
            approve, reject = st.columns(2)
            if approve.button("Approve and register", key=f"approve_{item['id']}", type="primary", width="stretch"):
                db.set_approval(item["id"], "approved")
                try:
                    output = register_task(command)
                    db.set_approval(item["id"], "completed", output)
                    logger.info("Scheduled task registered: %s", item["id"])
                    st.success(output or "Task registered.")
                except Exception as exc:
                    db.set_approval(item["id"], "failed", str(exc))
                    logger.exception("Task registration failed")
                    st.error(str(exc))
                st.rerun()
            if reject.button("Reject", key=f"reject_{item['id']}", width="stretch"):
                db.set_approval(item["id"], "rejected")
                logger.info("Scheduled task rejected: %s", item["id"])
                st.rerun()

else:
    st.subheader("Activity & health")
    c1, c2, c3 = st.columns(3)
    c1.metric("Conversations", len(db.list_conversations()))
    c2.metric("Approval requests", len(db.list_approvals()))
    c3.metric("Codex CLI", "Ready" if codex_available() else "Not found")
    log_path = settings.log_dir / "activity.log"
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-100:]
        st.code("\n".join(lines) or "No activity yet.", language="text")
    else:
        st.info("No activity has been logged yet.")

