import json, os
from datetime import datetime, timezone
from pathlib import Path
from services.news import collect_news, create_news_brief
from services.facebook import publish_text

OUT=Path(__file__).parent/"generated"
INDEX=OUT/"news_index.json"

def load_history():
    try:
        data=json.loads(INDEX.read_text(encoding="utf-8"))
        if isinstance(data,dict) and isinstance(data.get("processed"),dict): return data
    except (OSError,json.JSONDecodeError): pass
    return {"processed":{},"last_run":None}

def main():
    OUT.mkdir(exist_ok=True); history=load_history()
    stories,feed_status=collect_news()
    limit=max(1,min(5,int(os.getenv("NEWS_MAX_POSTS_PER_RUN","2"))))
    dry_run=os.getenv("NEWS_DRY_RUN","true").lower()!="false"
    published=0
    for story in stories:
        if story["id"] in history["processed"]: continue
        try:
            brief=create_news_brief(story)
            if not brief:
                history["processed"][story["id"]]={"status":"skipped_insufficient_source","title":story["title"],"source":story["source"],"url":story["url"]}
                continue
            status="draft"; fb_id=None
            if not dry_run and published<limit:
                fb_id=publish_text(brief); status="published"; published+=1
            history["processed"][story["id"]]={"status":status,"title":story["title"],"source":story["source"],"url":story["url"],"brief":brief,"facebook_post_id":fb_id,"processed_at":datetime.now(timezone.utc).isoformat()}
            print("["+status+"] "+brief)
        except Exception as exc: print("[ERROR] "+story["source"]+": "+str(exc))
    history["last_run"]={"at":datetime.now(timezone.utc).isoformat(),"dry_run":dry_run,"feed_status":feed_status,"stories_seen":len(stories),"published_this_run":published}
    history["processed"]=dict(list(history["processed"].items())[-1000:])
    INDEX.write_text(json.dumps(history,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(history["last_run"],ensure_ascii=False))

if __name__=="__main__": main()
