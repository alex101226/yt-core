# app/tasks/server_instance_status_checker.py

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.cmp.instance_status_check_task import InstanceStatusCheckTask
from app.common.dependencies import get_cmp_db  # 获取 DB session

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

scheduler = None

def check_instance_status():
    db: Session = next(get_cmp_db())
    try:
        # 查询待轮询任务
        tasks = db.query(InstanceStatusCheckTask).filter(
            InstanceStatusCheckTask.status.in_([1, 2])
        ).all()

        if not tasks:
            logger.info(f"{datetime.now(timezone.utc)} - 无待轮询任务")
            return

        logger.info(f"{datetime.now(timezone.utc)} - 扫描到 {len(tasks)} 个任务")

        for task in tasks:
            try:
                # 模拟状态推进
                if task.status == 1:  # PENDING → RUNNING
                    task.status = 2
                elif task.status == 2:  # RUNNING → SUCCESS
                    task.status = 3

                task.check_count += 1

                # 超过最大轮询次数
                if task.check_count >= task.max_check and task.status in [1, 2]:
                    task.status = 4
                    task.error_message = "超过最大轮询次数"
                    logger.warning(f"任务 {task.id} 超过最大轮询次数")

            except Exception as e:
                logger.error(f"任务 {task.id} 轮询异常: {e}")

        db.commit()
    except Exception as e:
        logger.error(f"轮询任务整体异常: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler(interval_seconds: int = 10):
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_instance_status, "interval", seconds=interval_seconds)
    scheduler.start()
    logger.info("实例状态轮询任务已启动")

def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("实例状态轮询任务已停止")

if __name__ == "__main__":
    start_scheduler()
    import time
    while True:
        time.sleep(60)
