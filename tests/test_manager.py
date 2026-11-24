from codex_bot.database import Database
from codex_bot.marketing_manager import MarketingManager
from codex_bot.models import MarketingTaskRequest
from skills.registry import route_skill


VALID = {"content_type":"video_script","title":"Massage oil intro","platform":"TikTok","hook":"Pause and unwind","caption":"A gentle product introduction.","hashtags":["#EsseCo"],"call_to_action":"Message us to learn more.","visual_prompt":"Warm product flat lay","suggested_publication_date":None,"language":"Taglish","warnings":["Ingredients require owner confirmation."],"calendar_entries":[]}


def test_routes_specialized_tasks():
    assert route_skill("Optimize this for Shopee") == "shopee_listing"
    assert route_skill("Write a TikTok video script") == "video_script"
    assert route_skill("Create a 30-day calendar") == "content_calendar"


def test_manager_validates_saves_and_queues(tmp_path):
    knowledge=tmp_path/"knowledge"; knowledge.mkdir()
    (knowledge/"business.md").write_text("# Esse Co",encoding="utf-8")
    db=Database(tmp_path/"app.db")
    manager=MarketingManager(db,tmp_path,runner=lambda *args: VALID)
    content_id,data=manager.execute(MarketingTaskRequest("TikTok script","video_script","TikTok",language="Taglish"))
    assert data["platform"] == "TikTok"
    assert db.list_generated_content("pending_approval")[0]["id"] == content_id


def test_manager_retries_invalid_output_once(tmp_path):
    knowledge=tmp_path/"knowledge"; knowledge.mkdir(); (knowledge/"business.md").write_text("# Esse Co",encoding="utf-8")
    calls=[]
    def runner(*args):
        calls.append(args[0]); return {} if len(calls)==1 else VALID
    manager=MarketingManager(Database(tmp_path/"app.db"),tmp_path,runner=runner)
    manager.execute(MarketingTaskRequest("TikTok script","video_script","TikTok"))
    assert len(calls) == 2
