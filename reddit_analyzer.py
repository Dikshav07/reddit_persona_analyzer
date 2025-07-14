import praw
from textblob import TextBlob
import spacy
from config import *
import re
from datetime import datetime
from collections import Counter

class RedditPersonaAnalyzer:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        self.nlp = spacy.load("en_core_web_sm")

    def get_user(self, url):
        match = re.search(r'reddit.com/user/([^/]+)', url)
        return match.group(1) if match else None

    def fetch_data(self, uname):
        user = self.reddit.redditor(uname)
        res = {
            'uname': uname,
            'posts': [],
            'comments': [],
            'subs': set(),
            'created': None
        }

        try:
            res['created'] = user.created_utc

            for p in user.submissions.new(limit=50):
                res['posts'].append({
                    'title': p.title,
                    'text': p.selftext,
                    'sub': p.subreddit.display_name,
                    'url': f"https://reddit.com{p.permalink}",
                    'created': p.created_utc,
                    'score': p.score
                })
                res['subs'].add(p.subreddit.display_name)

            for c in user.comments.new(limit=100):
                res['comments'].append({
                    'text': c.body,
                    'sub': c.subreddit.display_name,
                    'url': f"https://reddit.com{c.permalink}",
                    'created': c.created_utc,
                    'score': c.score
                })
                res['subs'].add(c.subreddit.display_name)
        except Exception as e:
            print(f"Error collecting data: {str(e)}")

        return res

    def find_demo(self, texts):
        demo = {
            'gender': {'hint': None, 'src': None},
            'age': {'hint': None, 'src': None},
            'place': {'hint': None, 'src': None},
            'job': {'hint': None, 'src': None}
        }

        pat = {
            'gender': [
                (r'\b(?:i am|i\'m)\s+(?:a\s+)?(guy|man|male|woman|female|girl)\b', 1),
                (r'\bas\s+a\s+(guy|man|male|woman|female|girl)\b', 1)
            ],
            'age': [
                (r'\b(?:i am|i\'m)\s+(\d+)\s+years?\s+old\b', 1),
                (r'\bin\s+my\s+(20s|30s|40s|50s|teens)\b', 1),
                (r'(\d+)\s+year\s+old\b', 1)
            ],
            'place': [
                (r'\bi(?:\'m| am) from\s+([A-Za-z\s,]+)', 1),
                (r'\blive in\s+([A-Za-z\s,]+)', 1),
                (r'\b(NYC|New York|LA|London|Tokyo)\b', 1)
            ],
            'job': [
                (r'\bi(?:\'m| am) (?:a\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b(?:\s+at\b|\s+for\b)?', 1),
                (r'\bwork(?:ing)? as (?:a\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b', 1)
            ]
        }

        for item in texts:
            t = item.get('text', '').lower()
            link = item.get('url', '')

            for kind, pats in pat.items():
                if not demo[kind]['hint']:
                    for p, grp in pats:
                        m = re.search(p, t, re.IGNORECASE)
                        if m:
                            demo[kind] = {
                                'hint': m.group(grp),
                                'src': link
                            }
                            break

        return demo

    def style_check(self, texts):
        pats = {
            'formal': r'\b(therefore|however|furthermore|consequently|nevertheless)\b',
            'casual': r'\b(lol|haha|yeah|nah|tbh)\b',
            'tech': r'\b(algorithm|framework|implementation|system|data)\b',
            'emoji': r'[\U0001F300-\U0001F9FF]'
        }

        style = {
            'formal': 0,
            'casual': 0,
            'tech': 0,
            'emoji': 0,
            'avg_len': 0,
            'samples': []
        }

        total_s = 0
        total_w = 0

        for item in texts:
            txt = item['text']
            url = item['url']

            style['formal'] += len(re.findall(pats['formal'], txt, re.IGNORECASE))
            style['casual'] += len(re.findall(pats['casual'], txt, re.IGNORECASE))
            style['tech'] += len(re.findall(pats['tech'], txt, re.IGNORECASE))
            style['emoji'] += len(re.findall(pats['emoji'], txt))

            s = len(re.split(r'[.!?]+', txt))
            w = len(txt.split())

            if s > 0:
                total_s += s
                total_w += w
                if len(txt) > 50:
                    style['samples'].append((txt, url))

        style['avg_len'] = total_w / total_s if total_s > 0 else 0
        return style

    def build_persona(self, data):
        texts = [{'text': p['text'], 'url': p['url']} for p in data['posts']]
        texts += [{'text': c['text'], 'url': c['url']} for c in data['comments']]

        demo = self.find_demo(texts)
        style = self.style_check(texts)
        likes = self._top_subs(data)
        vibe = self._vibes(texts)

        output = f""" Reddit User Persona: u/{data['uname']}

 Demographics
{self._demo_text(demo)}

 Interests & Communities
{self._subs_text(likes, data['posts'])}

 Communication Style
{self._style_text(style)}

 Personality Traits
{self._vibe_text(vibe)}

 Activity Analysis
- Account age: {self._age(data['created'])}
- Total Posts: {len(data['posts'])}
- Total Comments: {len(data['comments'])}
- Active Communities: {len(data['subs'])}

 Summary
{self._wrap_up(data, demo, style, likes)}
"""
        return output

    def _top_subs(self, data):
        subs = {}
        for p in data['posts']:
            name = p['sub']
            if name not in subs:
                subs[name] = {'posts': [], 'score': 0}
            subs[name]['posts'].append(p)
            subs[name]['score'] += p['score']
        return dict(sorted(subs.items(), key=lambda x: x[1]['score'], reverse=True))

    def _vibes(self, texts):
        types = {
            'analytical': {'count': 0, 'words': ['think', 'analyze', 'consider', 'data']},
            'social': {'count': 0, 'words': ['people', 'community', 'together', 'share']},
            'helpful': {'count': 0, 'words': ['help', 'suggest', 'recommend', 'advice']},
            'strong_opinion': {'count': 0, 'words': ['should', 'must', 'never', 'always']}
        }

        found = {}

        for item in texts:
            txt = item['text'].lower()
            url = item['url']
            for t, val in types.items():
                if any(word in txt for word in val['words']):
                    types[t]['count'] += 1
                    if t not in found and len(txt) > 20:
                        found[t] = (txt, url)

        return {'traits': types, 'found': found}

    def _subs_text(self, subs, posts):
        text = ""
        for sub, info in list(subs.items())[:4]:
            if info['posts']:
                p = info['posts'][0]
                title = p.get('title', '').strip()
                body = p.get('text', '').strip()
                quote = body if body else title
                if quote:
                    text += f"- **r/{sub}**\n"
                    text += f'   Citation: "{quote[:100]}..."'
                    text += f" — {p['url']}\n\n"
        return text

    def _demo_text(self, demo):
        text = ""
        for tag, val in demo.items():
            text += f"- **{tag.title()}:** {val['hint'] or 'Not specified'}\n"
            if val['src'] and val['hint']:
                text += f'   Citation: "{val["hint"]}" found at {val["src"]}\n\n'
            else:
                text += "   Citation: No direct mention\n\n"
        return text

    def _style_text(self, style):
        if not style['samples']:
            return "No distinct writing style patterns identified."

        main = "formal" if style['formal'] > style['casual'] else "casual"
        samples = [s for s in style['samples'] if s[0].strip()]
        if samples:
            sample = samples[0]
            clean = sample[0].replace('\n', ' ').strip()
            text = f"- **Primary Style:** {main.title()}\n"
            text += f'   Citation: "{clean[:100]}..."'
            text += f" — {sample[1]}\n\n"
        else:
            text = f"- **Primary Style:** {main.title()}\n"
            text += "   Citation: No clear examples found\n\n"

        if style['emoji'] > 0:
            text += f"- **Emoji Usage:** Frequent ({style['emoji']} times)\n"

        if style['tech'] > 0:
            text += f"- **Technical Language:** Present ({style['tech']} instances)\n"

        return text

    def _vibe_text(self, vibe):
        text = ""
        for t, info in vibe['traits'].items():
            if info['count'] > 0 and t in vibe['found']:
                txt, url = vibe['found'][t]
                clean = txt.replace('\n', ' ').strip()
                text += f"- **{t.title()}** (Found {info['count']} times)\n"
                text += f'   Citation: "{clean[:100]}..."'
                text += f" — {url}\n\n"
        return text or "No clear personality indicators found in recent activity."

    def _age(self, created):
        if not created:
            return "Unknown"
        age = datetime.now().timestamp() - created
        y = int(age / (365.25 * 24 * 3600))
        m = int((age % (365.25 * 24 * 3600)) / (30.44 * 24 * 3600))
        return f"{y} years, {m} months"

    def _wrap_up(self, data, demo, style, subs):
        count = len(data['posts']) + len(data['comments'])
        act = "highly active" if count > 100 else "moderately active" if count > 50 else "occasionally active"
        place = demo['place']['hint'] or "unknown location"
        top = list(subs.keys())[:3]
        write = "formal" if style['formal'] > style['casual'] else "casual"
        if style['tech'] > 5:
            write += " and technical"

        return f"""u/{data['uname']} is a {act} Reddit user based in {place}. 
They maintain a {write} writing style and are most active in {', '.join(top)}. 
Their account shows regular engagement across {len(data['subs'])} different communities, 
with {len(data['posts'])} posts and {len(data['comments'])} comments."""

    def save(self, uname, text):
        fname = f"{uname}_persona_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(text)
        return fname

def main():
    bot = RedditPersonaAnalyzer()
    url = input("Enter Reddit user profile URL: ")
    uname = bot.get_user(url)

    if not uname:
        print("Invalid URL format")
        return

    print(f"Analyzing user: {uname}")
    data = bot.fetch_data(uname)
    out = bot.build_persona(data)
    file = bot.save(uname, out)
    print(f"\nAnalysis complete! Results saved to: {file}")

if __name__ == "__main__":
    main()
