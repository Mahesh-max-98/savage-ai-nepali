"""Public RSS collection and short Nepali news briefs."""
import hashlib, html, json, logging, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import requests

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "SavageAINepaliNews/1.0"}
FEEDS = [
 {"name":"NEB (official notices)","url":"https://news.google.com/rss/search?q=site%3Aneb.gov.np+(result+OR+notice+OR+exam)&hl=ne&gl=NP&ceid=NP%3Ane","official":True},
 {"name":"BBC Nepali","url":"https://news.google.com/rss/search?q=site%3Abbc.com%2Fnepali+Nepal&hl=ne&gl=NP&ceid=NP%3Ane"},
 {"name":"RONB / RONB Post","url":"https://news.google.com/rss/search?q=site%3Aronbpost.com+Nepal&hl=ne&gl=NP&ceid=NP%3Ane"},
 {"name":"Onlinekhabar","url":"https://www.onlinekhabar.com/feed"},
 {"name":"OK Khabar","url":"https://news.google.com/rss/search?q=site%3Aokkhabar.com+Nepal&hl=ne&gl=NP&ceid=NP%3Ane"},
 {"name":"Laligurash Media Network","url":"https://news.google.com/rss/search?q=site%3Alaligurash.com+Nepal&hl=ne&gl=NP&ceid=NP%3Ane"},
]

def _value(node, tag):
    item=node.find(tag)
    if item is None: return ""
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",item.text or ""))).strip()

def _date(value):
    try:
        dt=parsedate_to_datetime(value)
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError,ValueError,OverflowError): return None

def collect_news():
    stories=[]; status=[]
    for feed in FEEDS:
        try:
            response=requests.get(feed["url"],headers=HEADERS,timeout=15); response.raise_for_status()
            root=ET.fromstring(response.content); count=0
            for item in root.findall(".//item")[:8]:
                title=_value(item,"title"); link=_value(item,"link")
                if not title or not link: continue
                key=hashlib.sha256((title.lower().strip()+"|"+link).encode()).hexdigest()
                stories.append({"id":key,"title":title[:240],"url":link,"excerpt":_value(item,"description")[:700],"source":feed["name"],"official":feed.get("official",False),"published_at":_date(_value(item,"pubDate"))})
                count+=1
            status.append({"source":feed["name"],"ok":True,"items":count})
        except (requests.RequestException,ET.ParseError,ValueError) as exc:
            logger.warning("Feed %s failed: %s",feed["name"],exc)
            status.append({"source":feed["name"],"ok":False,"error":str(exc)[:180]})
    unique={}
    for story in stories: unique.setdefault(story["id"],story)
    return list(unique.values()),status

def create_news_brief(story):
    api_key=os.getenv("GROQ_API_KEY")
    if not api_key: raise RuntimeError("GROQ_API_KEY is missing.")
    prompt=f"""तपाईं नेपाली समाचार सम्पादक हुनुहुन्छ। तलको स्रोत सामग्रीका आधारमा मात्र छोटो, निष्पक्ष नेपाली समाचार लेख्नुहोस्।
शीर्षक: {story['title']}
स्रोत: {story['source']}
प्रकाशित समय: {story.get('published_at') or 'स्रोतमा उपलब्ध छैन'}
छोटो अंश: {story.get('excerpt') or 'अंश उपलब्ध छैन'}
नियम:
- ३ देखि ८ लाइन; पहिलो लाइन तथ्यपरक शीर्षक होस्।
- शीर्षकपछि २–६ छोटा वाक्यमा मुख्य तथ्य मात्र लेख्नुहोस्।
- नाम, संख्या, उद्धरण, कारण वा विवरण आफैँ नथप्नुहोस्।
- अपुष्ट दाबीलाई सत्यझैँ नलेख्नुहोस्; आवश्यक भए "स्रोतका अनुसार" भन्नुहोस्।
- पुरानो समाचारलाई ताजा घटना भनेर नलेख्नुहोस्।
- राजनीतिक/विवादास्पद विषयमा पक्ष नलिनुहोस्।
- अन्तिम लाइन "स्रोत: {story['source']}" होस्।
- इमोजी, ह्यासट्याग, markdown र URL नराख्नुहोस्।
- सामग्री अपर्याप्त भए postable=false राख्नुहोस्।
JSON मात्र: {{"postable":true,"text":"शीर्षक\\nसमाचारका लाइनहरू\\nस्रोत: नाम","reason":""}}"""
    response=requests.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},json={"model":os.getenv("GROQ_MODEL","openai/gpt-oss-120b"),"messages":[{"role":"system","content":"You are a careful Nepali news editor. Never invent facts. Return JSON only."},{"role":"user","content":prompt}],"temperature":0.2,"max_completion_tokens":700,"response_format":{"type":"json_object"}},timeout=90)
    if not response.ok: raise RuntimeError(f"Groq API error {response.status_code}: {response.text[:350]}")
    try: result=json.loads(((response.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")
    except json.JSONDecodeError as exc: raise RuntimeError("AI returned invalid news JSON.") from exc
    lines=[x.strip() for x in str(result.get("text","")).splitlines() if x.strip()]
    if not result.get("postable") or not 3<=len(lines)<=8 or not lines[-1].lower().startswith("स्रोत:"): return None
    return "\n".join(lines)
