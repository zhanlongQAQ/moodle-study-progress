"""Build a standalone demo from Moodle-style course metadata."""
import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

MATERIAL_PATTERNS = {
    'Module': r'^Module\s+{n}\.\d+(?=\s|[-–—:]|$)',
    'Topic': r'^Lecture\s+(?:Notes|Slides)\b',
    'Week': r'^(?:Week|Session)\s+{n}\s+(?:Teaching Slides|Lecture (?:Notes|Slides))\b',
}


def is_open(details, now):
    unlock_at = details.get('unlock_at')
    if unlock_at:
        unlock_at = datetime.fromisoformat(unlock_at.replace('Z', '+00:00'))
        if unlock_at.tzinfo is None:
            unlock_at = unlock_at.replace(tzinfo=timezone.utc)
    return not details.get('locked_for_user') and (unlock_at is None or unlock_at <= now)


def published_units(modules, unit, material_pattern, now):
    units = set()
    for module in modules:
        match = re.match(rf'^{unit}\s+(\d+)(?=\s|[-–—:]|$)', module.get('name') or '', re.I)
        if not match or not is_open(module, now):
            continue
        number = int(match[1])
        pattern = re.compile(material_pattern.format(n=number), re.I)
        if any(item.get('type') == 'File'
               and pattern.match(item.get('title') or '')
               and is_open(item.get('content_details') or {}, now)
               for item in module.get('items') or []):
            units.add(number)
    return sorted(units)


CSS = """<style>
.course-progress > .meta{margin:-4px 0 var(--s3)}
.course-progress-list{padding:0 var(--s4)}
.course-progress-row{padding:var(--s3) 0}
.course-progress-row + .course-progress-row{border-top:1px solid var(--line)}
.course-progress-header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:0 var(--s2)}
.course-progress-value{font-weight:600}
.course-progress-scroll{overflow-x:auto;padding-top:4px}
.course-progress-scale{--course-thumb:16px;--course-track:6px;min-width:calc(36px * var(--course-stops))}
.course-progress-scale input{appearance:none;display:block;height:28px;margin:0 auto;background:none;cursor:pointer;
  width:calc(100% - 100% / var(--course-stops) + var(--course-thumb))}
.course-progress-scale input:disabled{cursor:default}
.course-progress-scale input::-webkit-slider-runnable-track{height:var(--course-track);border-radius:999px;
  background:linear-gradient(to right,var(--accent) var(--course-fill,0%),var(--sunk) var(--course-fill,0%))}
.course-progress-scale input::-moz-range-track{height:var(--course-track);border-radius:999px;
  background:linear-gradient(to right,var(--accent) var(--course-fill,0%),var(--sunk) var(--course-fill,0%))}
.course-progress-scale input::-webkit-slider-thumb{appearance:none;width:var(--course-thumb);height:var(--course-thumb);
  margin-top:calc((var(--course-track) - var(--course-thumb)) / 2);border:0;border-radius:50%;background:var(--accent)}
.course-progress-scale input::-moz-range-thumb{width:var(--course-thumb);height:var(--course-thumb);
  border:0;border-radius:50%;background:var(--accent)}
.course-progress-ticks{display:grid;grid-template-columns:repeat(var(--course-stops),minmax(0,1fr));
  text-align:center;font-size:12px;line-height:1.25;color:var(--muted)}
.course-progress-ticks li{padding:0 2px}
.course-progress-ticks li::before{content:"";display:block;width:1px;height:5px;margin:0 auto 4px;background:var(--faint)}
.course-progress-ticks .is-selected{color:var(--accent);font-weight:600}
.course-progress-ticks .is-selected::before{background:var(--accent);width:2px}
.course-progress-source{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:0 var(--s2)}
.course-progress-scroll + .course-progress-source{margin-top:var(--s2)}
.course-progress-notice{margin-top:var(--s2);color:var(--warn)}
</style>"""


SCRIPT = """<script>
function initCourseProgress(section) {
  const notice = section.querySelector('.course-progress-notice');
  for (const slider of section.querySelectorAll('input[data-course-units]')) {
    const units = [null, ...slider.dataset.courseUnits.split(',').map(Number)];
    const unitName = slider.dataset.unitName;
    const output = document.querySelector(`output[for="${slider.id}"]`);
    const ticks = slider.parentElement.querySelectorAll('.course-progress-ticks li');
    const key = `moodle-study-progress:example:${slider.dataset.courseId}`;
    const display = () => {
      const index = slider.valueAsNumber;
      const number = units[index];
      const label = number === null ? '未设置' : `${unitName} ${number}`;
      output.textContent = label;
      slider.setAttribute('aria-valuetext', label);
      slider.style.setProperty('--course-fill', `${index * 100 / (units.length - 1)}%`);
      ticks.forEach((tick, i) => tick.classList.toggle('is-selected', i === index));
    };

    try {
      const saved = Number(localStorage.getItem(key));
      const index = units.findLastIndex(number => number !== null && number <= saved);
      slider.value = Math.max(0, index);
    } catch {
      notice.hidden = false;
    }
    display();
    slider.disabled = false;
    slider.addEventListener('input', () => {
      display();
      try {
        const number = units[slider.valueAsNumber];
        if (number === null) localStorage.removeItem(key);
        else localStorage.setItem(key, String(number));
      } catch {
        notice.hidden = false;
      }
    });
  }
}
</script>"""


def render_progress(rows):
    cards = []
    for row in rows:
        code = escape(row['code'])
        unit = escape(row['unit'])
        course_id = int(row['course_id'])
        units = row['units']
        value = ''
        slider = ''
        published = '暂无已核实课件'
        if units:
            options = ','.join(map(str, units))
            slider_id = f'course-progress-{course_id}'
            value = f'<p class="course-progress-value">我的进度 <output for="{slider_id}">未设置</output></p>'
            ticks = '<li>未设置</li>' + ''.join(f'<li>{unit} {number}</li>' for number in units)
            slider = (
                f'<div class="course-progress-scroll"><div class="course-progress-scale" style="--course-stops:{len(units) + 1}">'
                f'<input type="range" id="{slider_id}" min="0" max="{len(units)}" value="0" step="1"'
                f' aria-label="{code} 我的学习进度" aria-valuetext="未设置"'
                f' data-course-units="{options}" data-unit-name="{unit}" data-course-id="{course_id}" disabled>'
                f'<ol class="course-progress-ticks" aria-hidden="true">{ticks}</ol></div></div>'
            )
            published = f'已发到 {unit} {units[-1]}'
        cards.append(f'<div class="course-progress-row"><div class="course-progress-header"><h3 class="code">{code}</h3>{value}</div>{slider}'
                     f'<p class="meta course-progress-source">{published}</p></div>')
    return ('<section id="course-progress" class="course-progress" aria-labelledby="course-progress-title">'
            '<h2 id="course-progress-title">课程学习进度</h2>'
            '<p class="meta">拖动选择学到的章节，进度保存在当前浏览器。刻度对应已发布的正课课件。</p>'
            '<div class="card course-progress-list">' + ''.join(cards) + '</div>'
            '<p class="meta course-progress-notice" role="status" hidden>当前浏览器无法保存进度。</p></section>')


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
  {CSS}
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
{SCRIPT}
<script>
const demo = document.querySelector('#progress-demo');
const button = document.querySelector('#release');
initCourseProgress(demo.querySelector('section'));
button.addEventListener('click', () => {{
  const released = button.getAttribute('aria-pressed') === 'false';
  const template = document.querySelector(released ? '#after-release' : '#before-release');
  demo.replaceChildren(template.content.cloneNode(true));
  initCourseProgress(demo.querySelector('section'));
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
