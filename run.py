import pywikibot
import threading
from utils.control import is_task_enabled
from utils.logger import log_action

# Import các task
from tasks import task1_protection
from tasks import task2_filewatch


def run_task(task_number: int, task_func) -> None:
    """
    Kiểm tra trạng thái của task và chạy nếu được bật.
    """
    if is_task_enabled(task_number):
        print(f"Bắt đầu chạy Task {task_number}.")
        try:
            task_func.run()
            print(f"Hoàn tất Task {task_number}.")
        except Exception as e:
            print(f'Lỗi khi chạy Task {task_number}: "{str(e)}"')
    else:
        print(f"Task {task_number} đang bị tắt.")


if __name__ == "__main__":
    # Tạo hai thread cho mỗi task
    t1 = threading.Thread(target=run_task, args=(1, task1_protection))
    t2 = threading.Thread(target=run_task, args=(2, task2_filewatch))

    # Khởi động thread
    t1.start()
    t2.start()

    # Chờ cả hai thread hoàn tất
    t1.join()
    t2.join()

    print("Đã chạy xong tất cả task.")
