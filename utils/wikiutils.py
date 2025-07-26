import pywikibot
from pywikibot.exceptions import NoPageError

def get_page_text(page: pywikibot.Page) -> str:
    """
    Trả về nội dung wikitext của một trang. Nếu trang chưa tồn tại, trả về chuỗi rỗng.
    """
    try:
        return page.get()
    except NoPageError:
        return ""
    except pywikibot.IsRedirectPage:
        return page.getRedirectTarget().get()


def set_page_text(page: pywikibot.Page, text: str, summary: str = "") -> None:
    """
    Ghi nội dung mới vào trang.
    """
    page.text = text
    page.save(summary=summary or "Bot: Cập nhật nội dung trang")


def get_last_editor_rights(site: pywikibot.Site, page: pywikibot.Page) -> list[str]:
    """
    Lấy danh sách quyền (rights) của người sửa đổi gần nhất trang.
    """
    revs = list(site.recentchanges(total=1, pages=[page.title()], changetype='edit', dir='older'))
    if not revs:
        return []

    user = revs[0].get('user')
    if not user:
        return []

    try:
        user_obj = pywikibot.User(site, user)
        return list(user_obj.groups())
    except Exception:
        return []
