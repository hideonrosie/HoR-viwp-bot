import json
import pywikibot

Site = pywikibot.Site('vi', 'wikipedia')
Page = pywikibot.Page

from utils.logger import log_action
from utils.wikiutils import get_page_text, set_page_text, get_last_editor_rights

def is_task_enabled(task_number: int) -> bool:
    """
    Kiểm tra xem Task X có được bật không.
    Nếu bị tắt (false) và người tắt không có quyền, sẽ tự bật lại và ghi log.
    """
    site = pywikibot.Site()
    run_page = pywikibot.Page(site, f"Thành viên:HoR bot/Task {task_number}/run")
    text = get_page_text(run_page).strip().lower()

    if text == "true":
        return True

    # Task đang bị tắt → kiểm tra quyền người sửa cuối
    try:
        last_rev = next(run_page.revisions(total=1))
        user = last_rev.user
    except StopIteration:
        user = None

    if not user:
        return False

    user_rights = get_last_editor_rights(site, run_page)
    if "patroller" in user_rights or "rollbacker" in user_rights:
        # Có quyền → tôn trọng việc tắt task
        return False
    else:
        # Không có quyền → bật lại và ghi log
        set_page_text(run_page, "true", summary="Tự động bật lại do người vô hiệu hóa không có quyền tuần tra")
        log_action(
            f"* {pywikibot.Timestamp.now().strftime('%H:%M, ngày %d tháng %m năm %Y')}: "
            f"[[Thành viên:{user}]] đã vô hiệu hóa Task {task_number}, nhưng không có quyền phù hợp. Bot đã bật lại."
        )
        return True

def read_config(task_name: str, user: str = "HoR bot") -> dict:
    """
    Đọc trang config kiểu JSON từ không gian tên Thành viên.
    """
    site = Site
    config_page = Page(site, f"Thành viên:{user}/{task_name}/config")
    if not config_page.exists():
        return {}
    try:
        return json.loads(config_page.text)
    except json.JSONDecodeError:
        return {}