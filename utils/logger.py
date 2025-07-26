import pywikibot
from pywikibot.exceptions import NoPageError

def log_action(text: str) -> None:
    """
    Ghi một dòng vào đầu trang 'Thành viên:HoR bot/log'.
    Mỗi dòng nên bắt đầu bằng '*'
    """
    site = pywikibot.Site()
    log_page = pywikibot.Page(site, "Thành viên:HoR bot/log")

    try:
        old_text = log_page.get()
    except NoPageError:
        old_text = ""

    new_text = text.strip() + "\n" + old_text.strip()
    log_page.text = new_text.strip() + "\n"
    log_page.save(summary="Bot: Ghi log hoạt động")
