import pywikibot
import json
import re
import time
import datetime
from pywikibot import Category

from utils.wikiutils import get_page_text, set_page_text
from utils.logger import log_action
from utils.control import read_config

task_number=1

def has_any_protection_template(text: str, templates: list[str]) -> bool:
    for template in templates:
        pattern = r"\{\{\s*%s(?:\s*\|[^}]*?)?\s*\}\}" % re.escape(template)
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def add_protection_template(page: pywikibot.Page, template: str, small: bool = True, noinclude: bool = False) -> None:
    try:
        text = page.get()
        template_code = f"{{{{{template}"
        if small:
            template_code += "|small=yes"
        template_code += "}}"

        if noinclude:
            template_code = f"<noinclude>{template_code}</noinclude>"

        new_text = f"{template_code}\n{text}"
        page.text = new_text
        page.save(summary="Bot: Thêm bản mẫu khóa trang")
    except Exception as e:
        log_action(f"* {page.title()}: Lỗi khi thêm bản mẫu – {e}")

def scan_protected_pages(site, config) -> None:
    protection_templates = config.get("protectionTemplate", [])
    run_namespaces = config.get("runinNamespace", {})
    default_templates = config.get("defaultinNamespace", {})
    small_namespaces = set(map(int, config.get("smallinNamespace", [])))
    noinclude_namespaces = set(map(int, config.get("noincludeinNamespace", [])))

    count = 0
    for page in site.protectedpages(type="edit", total=50):
        if not page.exists():
            continue
        if count >= 5:
            break
        if not run_namespaces.get(str(page.namespace()), False):
            continue
        try:
            text = page.get()
        except Exception:
            continue
        if has_any_protection_template(text, protection_templates):
            continue
        default_template = default_templates.get(str(page.namespace()), "pp-protected")
        add_protection_template(
            page,
            default_template,
            small=page.namespace() in small_namespaces,
            noinclude=page.namespace() in noinclude_namespaces
        )
        count += 1
        time.sleep(720)

def scan_protection_log(site, config):
    protection_templates = config.get("protectionTemplate", [])
    default_templates = config.get("defaultinNamespace", {})
    small_namespaces = set(map(int, config.get("smallinNamespace", [])))
    noinclude_namespaces = set(map(int, config.get("noincludeinNamespace", [])))

    now = datetime.datetime.utcnow()
    time_cutoff = now - datetime.timedelta(hours=6)
    log_entries = site.logevents(logtype="protect", start=time_cutoff)

    for entry in log_entries:
        page = entry.page()
        if not page or not page.exists():
            continue
        try:
            text = page.get()
        except Exception as e:
            log_action(f"Lỗi đọc trang {page.title()}: {e}")
            continue

        if has_any_protection_template(text, protection_templates):
            continue

        default_template = default_templates.get(str(page.namespace()), "pp-protected")
        add_protection_template(
            page,
            default_template,
            small=page.namespace() in small_namespaces,
            noinclude=page.namespace() in noinclude_namespaces
        )
        count += 1
        time.sleep(720)


def fix_invalid_protection_category(site, config, limit=5):
    protection_templates = config.get("protectionTemplate", [])
    pattern_names = [re.escape(name) for name in protection_templates]
    pattern = re.compile(r"(?i)\{\{\s*(" + "|".join(pattern_names) + r")(\s*\|[^}]*)?\}\}")

    cat = Category(site, "Thể loại:Trang có tham số bản mẫu khóa trang không đúng")
    count = 0

    for page in cat.members():
        if count >= limit:
            break

        try:
            text = page.text
        except Exception as e:
            log_action(f"* Lỗi đọc trang {page.title()}: {e}")
            continue

        protections = dict(page.protection())
        if "edit" in protections or "move" in protections:
            continue

        new_text, num_subs = pattern.subn("", text)
        if num_subs == 0:
            continue

        try:
            page.text = new_text.strip()
            page.save(summary="Gỡ bản mẫu khóa vì trang không còn bị khóa")
            # log_action(f"Đã gỡ {num_subs} bản mẫu khỏi trang {page.title()}")
            count += 1
            time.sleep(720)
        except Exception as e:
            log_action(f"* Lỗi khi lưu trang {page.title()}: {e}")


from concurrent.futures import ThreadPoolExecutor

def run():
    site = pywikibot.Site()
    config = read_config(task_name=f"Task {task_number}")
    if not config:
        log_action("Không thể tải cấu hình cho task 1.")
        return

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(scan_protected_pages, site, config)
        executor.submit(scan_protection_log, site, config)
        executor.submit(fix_invalid_protection_category, site, config)
