"""Build a standalone demo from Moodle-style course metadata."""
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.cc_progress import CSS, MATERIAL_PATTERNS, SCRIPT, published_units, render_progress


PAGE_CSS = """<style>
:root{--surface:#fff;--line:#d8e1ea;--ink:#172b41;--muted:#486178;--sunk:#e4ebf3;--faint:#7b8ea3;
  --accent:#1956af;--warn:#8a4b08;--s1:4px;--s2:8px;--s3:12px;--s4:16px;--s6:32px}
*{box-sizing:border-box}
body{margin:0;background:#f3f6fa;color:var(--ink);font:16px/1.5 system-ui,"Microsoft YaHei",sans-serif}
main{max-width:760px;margin:0 auto;padding:var(--s6) var(--s4)}
h1,h2,h3,p,ol{margin:0} ol{padding:0;list-style:none}
h1{font-size:clamp(24px,5vw,32px);margin-bottom:8px}
h2{font-size:18px;margin-bottom:12px}
h3{font-size:15px}
.meta{font-size:13px;color:var(--muted)}
.course-progress{margin-top:24px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px}
button{margin-top:12px;padding:8px 12px;border:1px solid var(--accent);border-radius:8px;background:var(--surface);
  color:var(--accent);font:inherit;cursor:pointer}
button[aria-pressed="true"]{background:var(--accent);color:white}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
</style>"""


def course_rows(courses, now):
    return [
        {
            'course_id': course['course_id'],
            'code': course['code'],
            'unit': course['unit'],
            'units': published_units(course['modules'], course['unit'], MATERIAL_PATTERNS[course['unit']], now),
        }
        for course in courses
    ]


def build_demo(data, now):
    courses = data['courses']
    before = render_progress(course_rows(courses, now))
    release = data['simulated_release']
    updated_courses = [
        {**course, 'modules': [
            {**module, 'items': [*module['items'], release['item']]}
            if course['course_id'] == release['course_id'] and module['name'] == release['section']
            else module
            for module in course['modules']
        ]}
        for course in courses
    ]
    after = render_progress(course_rows(updated_courses, now))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Moodle Study Progress · Demo</title>
  {PAGE_CSS}
  <style>{CSS}</style>
</head>
<body>
<main>
  <header>
    <h1>Moodle Study Progress</h1>
    <p>这是离线演示。先把 Reaction Engineering 拖到 Topic 6，再模拟发布新课件。</p>
    <button type="button" id="release" aria-pressed="false">模拟发布 Topic 7</button>
  </header>
  <div id="progress-demo">{before}</div>
  <template id="before-release">{before}</template>
  <template id="after-release">{after}</template>
</main>
<script>
{SCRIPT}
const demo = document.querySelector('#progress-demo');
const button = document.querySelector('#release');
const storagePrefix = 'moodle-study-progress:example';
initCourseProgress(demo.querySelector('section'), storagePrefix);
button.addEventListener('click', () => {{
  const released = button.getAttribute('aria-pressed') === 'false';
  const template = document.querySelector(released ? '#after-release' : '#before-release');
  demo.replaceChildren(template.content.cloneNode(true));
  initCourseProgress(demo.querySelector('section'), storagePrefix);
  button.setAttribute('aria-pressed', String(released));
  button.textContent = released ? '恢复发布前' : '模拟发布 Topic 7';
}});
</script>
</body>
</html>
"""


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    data = json.loads((root / 'example-courses.json').read_text('utf-8'))
    (root / 'index.html').write_text(build_demo(data, datetime.now(timezone.utc)), 'utf-8')
