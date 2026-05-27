#!/usr/bin/env python3
"""
Dynamic HTML card generator for Xiaohongshu-style articles.
Takes structured article data and generates 5-15 cards with content-aware layouts.
"""
import os, json, hashlib, random
from pathlib import Path
from typing import List, Dict, Any

CARD_WIDTH = 1080
CARD_HEIGHT = 1440

# ── Color themes ──────────────────────────────────────────
THEMES = {
    "tech": {
        "bg": "linear-gradient(145deg, #0f0f1a 0%, #1a1a2e 30%, #16213e 70%, #0f3460 100%)",
        "text": "#e8e8f0",
        "text_secondary": "#94a3b8",
        "accent1": "#6366f1", "accent2": "#ec4899", "accent3": "#f59e0b",
        "card_bg": "rgba(255,255,255,0.03)",
        "card_border": "rgba(255,255,255,0.06)",
        "tag_bg": "rgba(99,102,241,0.12)",
        "tag_border": "rgba(99,102,241,0.2)",
        "title_gradient": "linear-gradient(135deg, #f0f0ff 0%, #a5b4fc 50%, #f0abfc 100%)",
        "glow1": "rgba(99,102,241,0.15)",
        "glow2": "rgba(236,72,153,0.12)",
    },
    "warm": {
        "bg": "linear-gradient(145deg, #1a0f0f 0%, #2e1a1a 30%, #3e2116 70%, #60200f 100%)",
        "text": "#f0e8e0",
        "text_secondary": "#b8a894",
        "accent1": "#f472b6", "accent2": "#fb923c", "accent3": "#fbbf24",
        "card_bg": "rgba(255,248,240,0.03)",
        "card_border": "rgba(255,200,150,0.08)",
        "tag_bg": "rgba(244,114,182,0.12)",
        "tag_border": "rgba(244,114,182,0.2)",
        "title_gradient": "linear-gradient(135deg, #fff0f0 0%, #fbcfe8 50%, #fde68a 100%)",
        "glow1": "rgba(244,114,182,0.15)",
        "glow2": "rgba(251,146,60,0.12)",
    },
    "nature": {
        "bg": "linear-gradient(145deg, #0a1a0f 0%, #0f2e1a 30%, #163e21 70%, #0f3a20 100%)",
        "text": "#e0f0e8",
        "text_secondary": "#94b8a4",
        "accent1": "#34d399", "accent2": "#60a5fa", "accent3": "#f59e0b",
        "card_bg": "rgba(240,255,248,0.03)",
        "card_border": "rgba(100,200,150,0.08)",
        "tag_bg": "rgba(52,211,153,0.12)",
        "tag_border": "rgba(52,211,153,0.2)",
        "title_gradient": "linear-gradient(135deg, #f0fff8 0%, #a7f3d0 50%, #93c5fd 100%)",
        "glow1": "rgba(52,211,153,0.15)",
        "glow2": "rgba(96,165,250,0.12)",
    },
    "minimal": {
        "bg": "#0c0c0c",
        "text": "#f0f0f0",
        "text_secondary": "#888888",
        "accent1": "#ffffff", "accent2": "#aaaaaa", "accent3": "#666666",
        "card_bg": "rgba(255,255,255,0.02)",
        "card_border": "rgba(255,255,255,0.08)",
        "tag_bg": "rgba(255,255,255,0.05)",
        "tag_border": "rgba(255,255,255,0.12)",
        "title_gradient": "linear-gradient(135deg, #ffffff 0%, #cccccc 100%)",
        "glow1": "rgba(255,255,255,0.05)",
        "glow2": "rgba(255,255,255,0.03)",
    },
}


def pick_theme(title: str) -> str:
    """Deterministically pick a theme based on article title"""
    idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(THEMES)
    return list(THEMES.keys())[idx]


def generate_card(article: Dict[str, Any], card_index: int, total_cards: int,
                  output_dir: str) -> str:
    """Generate a single card HTML. Each card has a layout driven by its content."""
    theme_name = article.get("theme", pick_theme(article.get("title", "")))
    theme = THEMES[theme_name]
    
    sections = article.get("sections", [])
    title = article.get("title", "")
    subtitle = article.get("subtitle", "")
    tags = article.get("tags", [])
    date = article.get("date", "")
    author = article.get("author", "灵魂攻城狮")
    
    # Determine card type from content
    if card_index == 0:
        return _render_title_card(theme, title, subtitle, tags, date, author, article)
    
    # Content cards - each one gets a different layout
    section_idx = card_index - 1
    if section_idx < len(sections):
        section = sections[section_idx]
        # Pick layout variant based on section content
        layout_type = _pick_layout(section, section_idx)
        return _render_content_card(theme, section, layout_type, card_index, total_cards, article)
    
    # Summary / ending card
    if card_index == total_cards - 1:
        return _render_summary_card(theme, title, tags, author, article)
    
    return _render_content_card(theme, {"title": "…", "content": ""}, "text", card_index, total_cards, article)


def _pick_layout(section: Dict, idx: int) -> str:
    """Pick layout based on section content characteristics"""
    content = section.get("content", "")
    title = section.get("title", "")
    
    if any(k in content for k in ["%", "倍", "x", "×"]):
        return "data_highlight"
    if len(content) > 200:
        return "long_text"
    if any(k in content for k in ["注意", "警告", "❗", "⚠️"]):
        return "callout"
    if any(k in title for k in ["对比", "vs", "VS", "区别"]):
        return "comparison"
    if any(k in content for k in ["排名", "Top", "TOP", "最佳"]):
        return "list"
    if idx % 4 == 0:
        return "quote"
    if idx % 3 == 0:
        return "data_highlight"
    return "text"


def _render_title_card(t, title, subtitle, tags, date, author, article):
    """Title/cover card - the most visually impactful"""
    cat = article.get("category", "AI · 深度解读")
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
body{{width:1080px;height:1440px;font-family:'Noto Sans SC',sans-serif;
  background:{t['bg']};color:{t['text']};display:flex;flex-direction:column;
  padding:60px;overflow:hidden;position:relative}}
body::before{{content:'';position:absolute;top:-250px;right:-200px;width:700px;height:700px;
  background:radial-gradient(circle,{t['glow1']} 0%,transparent 70%);border-radius:50%;pointer-events:none}}
body::after{{content:'';position:absolute;bottom:-180px;left:-180px;width:500px;height:500px;
  background:radial-gradient(circle,{t['glow2']} 0%,transparent 70%);border-radius:50%;pointer-events:none}}
.category{{display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(135deg,{t['accent1']}30,{t['accent2']}20);
  border:1px solid {t['accent1']}60;border-radius:20px;padding:8px 20px;font-size:14px;
  color:{t['accent1']}90;align-self:flex-start;margin-bottom:24px;letter-spacing:1px}}
.category .dot{{width:8px;height:8px;background:{t['accent1']};border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.title{{font-size:{48 if len(title)<20 else 42}px;font-weight:900;line-height:1.3;margin-bottom:24px;
  background:{t['title_gradient']};-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;letter-spacing:-0.5px}}
.subtitle{{font-size:22px;font-weight:300;line-height:1.6;color:{t['text_secondary']};margin-bottom:32px}}
.meta{{display:flex;align-items:center;gap:16px;margin-bottom:40px;font-size:14px;color:{t['text_secondary']}}}
.meta .sep{{width:4px;height:4px;background:{t['text_secondary']};border-radius:50%}}
.meta .hl{{color:{t['accent2']};font-weight:500}}
.divider{{width:100%;height:1px;
  background:linear-gradient(90deg,transparent,{t['accent1']}50,{t['accent2']}50,transparent);margin-bottom:40px}}
.preview{{flex:1;display:flex;align-items:center;justify-content:center;
  background:{t['card_bg']};border-radius:24px;border:1px solid {t['card_border']};
  margin-bottom:30px;padding:40px}}
.preview-text{{font-size:20px;font-weight:300;color:{t['text_secondary']};text-align:center;line-height:2;
  max-width:80%}}
.preview-text em{{font-style:normal;color:{t['text']}}}
.tags{{display:flex;flex-wrap:wrap;gap:10px;margin-top:auto;padding-top:40px}}
.tag{{padding:6px 16px;background:{t['tag_bg']};border:1px solid {t['tag_border']};
  border-radius:12px;font-size:13px;color:{t['accent1']}90}}
.footer{{margin-top:24px;text-align:center;font-size:12px;color:{t['text_secondary']};letter-spacing:2px}}
</style></head><body>
<div class="category"><span class="dot"></span>{cat}</div>
<h1 class="title">{title}</h1>
{f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
<div class="meta">
  <span>📅 {date}</span>
  <span class="sep"></span>
  <span class="hl">🔥 热门</span>
</div>
<div class="divider"></div>
<div class="preview">
  <div class="preview-text">
    {chr(10).join(f'✦ {s["title"]}' for s in article.get("sections", [])[:4])}
  </div>
</div>
<div class="tags">{''.join(f'<span class="tag">{t}</span>' for t in tags[:6])}</div>
<div class="footer">关注 {author} · 每天一篇深度解读</div>
</body></html>"""


def _render_content_card(t, section, layout_type, idx, total, article):
    """Content cards with dynamic layout"""
    title = section.get("title", "")
    content = section.get("content", "")
    emoji = section.get("emoji", "💡")
    
    if layout_type == "data_highlight":
        card_style = f"""
.section{{background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:16px;
  padding:32px;margin-bottom:24px;position:relative;flex:1;display:flex;flex-direction:column}}
.section::before{{content:'';position:absolute;left:0;top:16px;bottom:16px;width:4px;
  background:linear-gradient(180deg,{t['accent1']},{t['accent2']});border-radius:4px}}
.section-title{{font-size:22px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
.hero-data{{display:flex;justify-content:center;gap:24px;margin-bottom:24px;flex-wrap:wrap}}
.hero-item{{text-align:center;background:rgba(255,255,255,0.04);border-radius:16px;padding:20px 28px;min-width:160px;
  border:1px solid rgba(255,255,255,0.06)}}
.hero-value{{font-size:44px;font-weight:900;
  background:linear-gradient(135deg,{t['accent1']},{t['accent2']});
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.2}}
.hero-label{{font-size:14px;color:{t['text_secondary']};margin-top:6px}}
.section-content{{font-size:16px;line-height:1.8;color:{t['text_secondary']};font-weight:300}}
.section-content strong{{color:{t['text']};font-weight:500}}
"""
    elif layout_type == "callout":
        card_style = f"""
.section{{background:linear-gradient(135deg,{t['accent3']}10,{t['accent2']}08);
  border:1px solid {t['accent3']}30;border-radius:16px;padding:32px;margin-bottom:24px;flex:1;
  position:relative}}
.section::before{{content:'❗';position:absolute;top:-12px;left:-12px;font-size:24px}}
.section-title{{font-size:22px;font-weight:700;margin-bottom:16px;color:{t['accent3']};display:flex;align-items:center;gap:10px}}
.section-content{{font-size:17px;line-height:1.8;color:{t['text']};font-weight:400}}
"""
    elif layout_type == "quote":
        card_style = f"""
.section{{flex:1;display:flex;flex-direction:column;justify-content:center;
  padding:60px;text-align:center;background:{t['card_bg']};border-radius:24px;
  border:1px solid {t['card_border']};margin-bottom:24px;position:relative}}
.section::before{{content:'❝';position:absolute;top:20px;left:30px;font-size:48px;color:{t['accent1']}40;
  font-family:serif}}
.quote-text{{font-size:28px;font-weight:300;line-height:1.6;color:{t['text']};
  margin-bottom:20px;font-style:italic}}
.quote-source{{font-size:15px;color:{t['text_secondary']}}}
.section-title{{font-size:16px;font-weight:500;color:{t['accent1']}80;margin-bottom:10px}}
"""
    elif layout_type == "list":
        card_style = f"""
.section{{background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:16px;
  padding:32px;margin-bottom:24px;flex:1}}
.section-title{{font-size:22px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:10px}}
.list-item{{display:flex;gap:14px;margin-bottom:14px;align-items:flex-start}}
.list-num{{flex-shrink:0;width:28px;height:28px;background:linear-gradient(135deg,{t['accent1']},{t['accent2']});
  border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;
  color:#fff}}
.list-text{{font-size:16px;line-height:1.6;color:{t['text_secondary']};padding-top:4px}}
.list-text strong{{color:{t['text']};font-weight:500}}
"""
    else:
        card_style = f"""
.section{{background:{t['card_bg']};border:1px solid {t['card_border']};border-radius:16px;
  padding:32px;margin-bottom:24px;position:relative;flex:1}}
.section::before{{content:'';position:absolute;left:0;top:16px;bottom:16px;width:4px;
  background:linear-gradient(180deg,{t['accent1']},{t['accent2']});border-radius:4px}}
.section-title{{font-size:22px;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:10px}}
.section-content{{font-size:16px;line-height:1.9;color:{t['text_secondary']};font-weight:300}}
.section-content strong{{color:{t['text']};font-weight:500}}
"""

    progress = f'<div style="text-align:right;font-size:12px;color:{t["text_secondary"]};margin-top:auto;padding-top:20px">{idx}/{total}</div>' if idx < total - 1 else ''

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
body{{width:1080px;height:1440px;font-family:'Noto Sans SC',sans-serif;
  background:{t['bg']};color:{t['text']};display:flex;flex-direction:column;
  padding:60px;overflow:hidden;position:relative}}
body::before{{content:'';position:absolute;top:-200px;right:-150px;width:500px;height:500px;
  background:radial-gradient(circle,{t['glow1']} 0%,transparent 70%);border-radius:50%;pointer-events:none}}
{card_style}
.tags{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.tag{{padding:4px 12px;background:{t['tag_bg']};border:1px solid {t['tag_border']};
  border-radius:8px;font-size:12px;color:{t['accent1']}80}}
</style></head><body>
<div class="section">
  <div class="section-title"><span>{emoji}</span> {title}</div>
  {_render_content_body(section, layout_type)}
</div>
{progress}
</body></html>"""


def _render_content_body(section, layout_type):
    """Render content body based on layout type"""
    content = section.get("content", "")
    
    if layout_type == "data_highlight":
        # Extract and render data points as hero elements
        lines = content.split("\n")
        hero_items = []
        body_lines = []
        for line in lines:
            if any(c in line for c in ["%", "倍", "x", "×"]) and len(line) < 60:
                import re
                nums = re.findall(r'[\d.]+', line)
                if nums:
                    val = nums[0]
                    unit = "%" if "%" in line else "倍" if "倍" in line else ""
                    label = line.replace(val, "").strip()
                    label = re.sub(r'^[提升降低增超]+', '', label).strip()
                    hero_items.append((val + unit, label if label else line.strip()))
                else:
                    body_lines.append(line)
            else:
                body_lines.append(line)
        
        parts = []
        if hero_items:
            items_html = "".join(
                f'<div class="hero-item"><div class="hero-value">{v}</div><div class="hero-label">{l}</div></div>'
                for v, l in hero_items[:4]
            )
            parts.append(f'<div class="hero-data">{items_html}</div>')
        if body_lines:
            text = "<br>".join(body_lines)
            parts.append(f'<div class="section-content">{text}</div>')
        return "\n".join(parts)
    
    elif layout_type == "list":
        import re
        items = re.split(r'\d+[\.\)、]', content)
        items = [i.strip() for i in items if i.strip()]
        if len(items) <= 1:
            items = content.split("\n")
            items = [i.strip() for i in items if i.strip() and len(i.strip()) > 5]
        
        items_html = "".join(
            f'<div class="list-item"><div class="list-num">{i+1}</div><div class="list-text">{item}</div></div>'
            for i, item in enumerate(items[:8])
        )
        return f'<div class="list-container">{items_html}</div>'
    
    else:
        return f'<div class="section-content">{content.replace(chr(10), "<br>")}</div>'


def _render_summary_card(t, title, tags, author, article):
    """Ending/summary card"""
    key_points = article.get("key_takeaways", [])
    if not key_points:
        key_points = ["科技正在以前所未有的速度前进", "掌握趋势，才能把握未来"]
    
    points_html = "".join(f'<div>✅ {p}</div>' for p in key_points[:4])
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
body{{width:1080px;height:1440px;font-family:'Noto Sans SC',sans-serif;
  background:{t['bg']};color:{t['text']};display:flex;flex-direction:column;
  padding:60px;overflow:hidden;position:relative;text-align:center;align-items:center;justify-content:center}}
body::before{{content:'';position:absolute;top:-100px;right:-100px;width:400px;height:400px;
  background:radial-gradient(circle,{t['accent1']}12,transparent 70%);border-radius:50%;pointer-events:none}}
body::after{{content:'';position:absolute;bottom:-80px;left:-80px;width:300px;height:300px;
  background:radial-gradient(circle,{t['accent2']}12,transparent 70%);border-radius:50%;pointer-events:none}}
.summary-icon{{font-size:64px;margin-bottom:24px}}
.summary-title{{font-size:32px;font-weight:700;margin-bottom:20px;
  background:{t['title_gradient']};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.points{{font-size:18px;line-height:2.2;color:{t['text_secondary']};margin-bottom:40px;text-align:left}}
.divider{{width:200px;height:1px;
  background:linear-gradient(90deg,transparent,{t['accent1']}60,{t['accent2']}60,transparent);
  margin:20px auto}}
.tags{{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:30px}}
.tag{{padding:6px 16px;background:{t['tag_bg']};border:1px solid {t['tag_border']};
  border-radius:12px;font-size:13px;color:{t['accent1']}90}}
.footer{{font-size:14px;color:{t['text_secondary']};letter-spacing:2px}}
.footer strong{{color:{t['accent2']}}}
</style></head><body>
<div class="summary-icon">🎯</div>
<div class="summary-title">写在最后</div>
<div class="divider"></div>
<div class="points">{points_html}</div>
<div class="divider"></div>
<div class="tags">{''.join(f'<span class="tag">{t}</span>' for t in tags[:8])}</div>
<div class="footer">关注 <strong>{author}</strong> · 不错过每一次技术浪潮</div>
</body></html>"""


def generate_article_cards(article_data: Dict[str, Any], output_dir: str = "/tmp/cards") -> List[Dict[str, str]]:
    """Generate all cards for an article. Returns list of {html_path, png_path} dicts."""
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Determine number of cards based on content
    num_sections = len(article_data.get("sections", []))
    # title card + content cards + summary card
    total_cards = min(max(num_sections + 2, 5), 15)  # 5-15 cards
    # If we need more cards than sections, generate additional detail cards
    if total_cards > num_sections + 2:
        # Add more cards by splitting long sections
        pass  # For now, cap at num_sections + 2
    
    cards = []
    for i in range(total_cards):
        # Generate deterministic theme offset for variety
        html = generate_card(article_data, i, total_cards, output_dir)
        html_path = output_dir_path / f"card_{i+1:02d}.html"
        html_path.write_text(html, encoding='utf-8')
        png_path = output_dir_path / f"card_{i+1:02d}.png"
        cards.append({
            "index": i + 1,
            "total": total_cards,
            "html_path": str(html_path),
            "png_path": str(png_path),
        })
    
    return cards


# ── Main entry point for Hermes ──────────────────────────
if __name__ == "__main__":
    import sys
    data = json.loads(sys.stdin.read())
    cards = generate_article_cards(data, data.get("output_dir", "/tmp/cards"))
    print(json.dumps({"cards": cards, "total": len(cards)}, ensure_ascii=False, indent=2))
