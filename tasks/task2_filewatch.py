import pywikibot
from pywikibot.data.api import Request
import datetime
import re
import time

SITE = pywikibot.Site('vi', 'wikipedia')
SITE.login()
COMMONS = pywikibot.Site('commons', 'commons')

CONFIG_PAGE = 'Thành viên:HoR bot/Task 2/config'
REPORT_PAGE_PREFIX = 'Thành viên:HoR bot/hình/'

MAX_FILES_PER_HOUR = 5

# page = pywikibot.Page(site, change['title'])

def load_config():
    page = pywikibot.Page(SITE, CONFIG_PAGE)
    text = page.text
    config = {
        'trustedUserRights': set(),
        'trustedUploader': set(),
        'uploadDays': 365
    }

    tu_match = re.search(r"trustedUserRights\s*=\s*(.*?)$", text, re.M)
    if tu_match:
        rights = re.findall(r"'([^']+)'", tu_match.group(1))
        config['trustedUserRights'].update(rights)

    uploader_match = re.search(r"trustedUploader\s*=\s*(.*?)$", text, re.M)
    if uploader_match:
        rights = re.findall(r"'([^']+)'", uploader_match.group(1))
        config['trustedUploader'].update(rights)

    days_match = re.search(r"uploadDays\s*=\s*(\d+)", text)
    if days_match:
        config['uploadDays'] = int(days_match.group(1))

    return config

def is_trusted(user, config):
    try:
        user_obj = pywikibot.User(SITE, user)
        return not set(user_obj.groups()).isdisjoint(config['trustedUserRights'])
    except Exception:
        return False

def get_recent_changes(start_timestamp):
    req = Request(site=SITE, parameters={
        'action': 'query',
        'list': 'recentchanges',
        'rcnamespace': 0,
        'rctype': 'edit|new',
        'rcshow': '!bot',
        'rctag': 'Thêm tập tin',
        'rcstart': start_timestamp,
        'rclimit': 50,
        'rcprop': 'user|comment|ids|title|timestamp|tags|sizes|flags'
    })
    data = req.submit()
    return data.get('query', {}).get('recentchanges', [])

def extract_new_files(oldtext, newtext):
    old_files = set(re.findall(r'\[\[(?:[Ff]ile|[Tt]ập tin):([^|\]]+)', oldtext))
    new_files = set(re.findall(r'\[\[(?:[Ff]ile|[Tt]ập tin):([^|\]]+)', newtext))
    return new_files - old_files

def is_commons_file(filename, config):
    try:
        file_page = pywikibot.FilePage(COMMONS, f'File:{filename}')
        if not file_page.exists():
            return False

        file_history = file_page.get_file_history()
        if not file_history:
            return False

        # Lấy lần upload đầu tiên (bản sớm nhất)
        first_key = list(file_history.keys())[-1]
        fileinfo = file_history[first_key]

        upload_time = fileinfo.timestamp
        uploader = fileinfo.user

        # Kiểm tra thời gian upload
        days_diff = (datetime.datetime.utcnow() - upload_time).days
        if days_diff > config['uploadDays']:
            return False

        # Kiểm tra quyền người upload
        uploader_user = pywikibot.User(COMMONS, uploader)
        if not set(uploader_user.groups()).isdisjoint(config['trustedUploader']):
            return False

        return True
    except Exception as e:
        print(f'[Lỗi kiểm tra Commons] {filename}: {e}')
        return False

def write_report(filename, rev_id, user, title):
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    report_title = REPORT_PAGE_PREFIX + today
    report_page = pywikibot.Page(SITE, report_title)

    diff_link = f'[[Đặc biệt:Khác/{rev_id}|{title}]]'
    file_link = f'[[:c:File:{filename}]]'
    user_link = f'{{{{user|{user}}}}}'
    line = f'|-\n| {diff_link} || {file_link} || {user_link}'

    if not report_page.exists():
        report_page.text = (
            '{| class="wikitable"\n'
            '! Bài !! Tập tin thêm vào !! Người thêm\n' f'{line}\n|}}'
        )
    else:
        text = report_page.text.strip()
        if text.endswith('|}'):
            text = text[:-2].rstrip() + f'\n{line}\n|}}'
        else:
            text += f'\n{line}'
        report_page.text = text

    report_page.save(summary='Bot: Ghi báo cáo hình ảnh từ Commons')

def run():
    config = load_config()
    last_timestamp = datetime.datetime.utcnow().isoformat()
    file_count = 0
    start_time = time.time()

    print("Task 2 started. Listening for RC...")

    while True:
        try:
            if time.time() - start_time >= 3600:
                file_count = 0
                start_time = time.time()

            if file_count >= MAX_FILES_PER_HOUR:
                print("Đã đạt giới hạn 5 tập tin/giờ. Tạm dừng.")
                time.sleep(60)
                continue

            changes = get_recent_changes(last_timestamp)
            if not changes:
                time.sleep(10)
                continue

            for change in reversed(changes):
                user = change['user']
                title = change['title']
                revid = change['revid']

                if is_trusted(user, config):
                    continue

                page = pywikibot.Page(SITE, title)
                try:
                    newtext = page.get(get_redirect=True)
                    oldtext = page.getOldVersion(oldid=change['old_revid'])
                except Exception:
                    continue

                files_added = extract_new_files(oldtext, newtext)

                for fname in files_added:
                    if file_count >= MAX_FILES_PER_HOUR:
                        break
                    if is_commons_file(fname, config):
                        write_report(fname, revid, user, title)
                        file_count += 1

                last_timestamp = change['timestamp']

            time.sleep(10)
        except Exception as e:
            print(f'[Lỗi vòng lặp] {e}')
            time.sleep(30)

if __name__ == '__main__':
    run()
