"""Published Moodle teaching units and the weekly progress controls."""
import re
from datetime import datetime, timezone
from html import escape


MATERIAL_PATTERNS = {
    'Module': r'^(?:Module\s+{n}\.\d+(?=\s|[-–—:]|$)|Lecture\s+(?:Notes|Slides)\b)',
    'Topic': r'^(?:Lecture\s+(?:Notes|Slides)\b|Topic\s+{n}\s+Slides\b)',
    'Week': (r'^(?:(?:Week|Session)\s+{n}\s*[:–—-]?\s*)?(?:(?:Teaching |Lecture )?Slides|Lecture Notes)\b'
             r'|^Lecture\s+{n}\s+(?:Slides|Notes)\b'),
}


def is_open(details, now):
    unlock_at = details.get('unlock_at') or None
    if unlock_at:
        try:
            unlock_at = datetime.fromisoformat(str(unlock_at).replace('Z', '+00:00'))
        except ValueError:
            return False
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


def build_rows(courses, modules, checked_on, site, now):
    rows = []
    for course in courses:
        if course.get('inactive') or course.get('user_excluded'):
            continue
        code = course['code']
        sections = modules.get(code) or []
        options = [(unit, published_units(sections, unit, pattern, now))
                   for unit, pattern in MATERIAL_PATTERNS.items()]
        unit, numbers = max(options, key=lambda option: len(option[1]))
        if not numbers:
            continue
        course_id = int(course['id'])
        label, separator, _ = (course.get('name') or '').partition(':')
        rows.append({
            'code': label.strip() if separator and label.strip() else code,
            'course_id': course_id,
            'storage_key': f'{site}:{course_id}',
            'unit': unit,
            'units': numbers,
            'checked_on': checked_on.get(code),
        })
    return rows


CSS = """
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
"""


SCRIPT = """
function initCourseProgress(section, storagePrefix) {
  const notice = section.querySelector('.course-progress-notice');
  for (const slider of section.querySelectorAll('input[data-course-units]')) {
    const units = [null, ...slider.dataset.courseUnits.split(',').map(Number)];
    const unitName = slider.dataset.unitName;
    const output = section.querySelector(`output[for="${slider.id}"]`);
    const ticks = slider.parentElement.querySelectorAll('.course-progress-ticks li');
    const key = `${storagePrefix}:${slider.dataset.courseKey}`;
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
"""


def render_progress(rows):
    cards = []
    for row in rows:
        code = escape(row['code'])
        unit = escape(row['unit'])
        course_id = int(row['course_id'])
        units = row['units']
        storage_key = escape(str(row.get('storage_key', course_id)), quote=True)
        date = escape(row.get('checked_on') or '')
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
                f' data-course-units="{options}" data-unit-name="{unit}" data-course-key="{storage_key}" disabled>'
                f'<ol class="course-progress-ticks" aria-hidden="true">{ticks}</ol></div></div>'
            )
            published = f'已发到 {unit} {units[-1]}'
        checked = f'<time datetime="{date}" title="Moodle 检查日期">{date[5:]}</time>' if date else ''
        cards.append(f'<div class="course-progress-row"><div class="course-progress-header"><h3 class="code">{code}</h3>{value}</div>{slider}'
                     f'<p class="meta course-progress-source">{published}{checked}</p></div>')
    return ('<section id="course-progress" class="course-progress" aria-labelledby="course-progress-title">'
            '<h2 id="course-progress-title">课程学习进度</h2>'
            '<p class="meta">拖动选择学到的章节，进度保存在当前浏览器。刻度对应已发布的正课课件。</p>'
            '<div class="card course-progress-list">' + ''.join(cards) + '</div>'
            '<p class="meta course-progress-notice" role="status" hidden>当前浏览器无法保存进度。</p></section>')
