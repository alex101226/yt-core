# app/tasks/server_instance_status_checker.py
from enum import Enum

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate
from app.core.logger import logger

from app.models.cmp.instance_status_check_task import InstanceStatusCheckTask
from app.models.cmp.instance_create_task import InstanceCreateTask

from app.common.dependencies import get_cmp_db

# logger = logger.getLogger(__name__)
# logger.basicConfig(level=logger.INFO)

scheduler = None


def check_instance_status():
    db: Session = next(get_cmp_db())
    try:
        # 查询所有轮询中任务
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
                if task.status == 1:      # PENDING
                    task.status = 2       # RUNNING
                elif task.status == 2:    # RUNNING
                    task.status = 3       # SUCCESS

                task.check_count += 1
                task.updated_at = datetime.now(timezone.utc)

                # 超过最大轮询次数
                if task.check_count >= task.max_check and task.status in [1, 2]:
                    task.status = 4
                    task.error_message = "超过最大轮询次数"
                    logger.warning(f"任务 {task.id} 超过最大轮询次数")

                # ⭐⭐ 核心逻辑：根据任务类型更新主表和实例状态 ⭐⭐
                process_main_task(db, task)

            except Exception as e:
                logger.error(f"任务 {task.id} 轮询异常: {e}")

        db.commit()

    except Exception as e:
        logger.error(f"轮询任务整体异常: {e}")
        db.rollback()
    finally:
        db.close()


# class ServerInstanceStatus(str, Enum):
#     INIT = "INIT"   # 初始化
#     PREPARE_START = "PREPARE_START" # 开机
#     PREPARE_STOP = "PREPARE_STOP"   # 关机
#     PREPARE_REBOOT = "PREPARE_REBOOT"   # 重启
#     IMAGE_CREATING="IMAGE_CREATING" # 创建镜像
#     IMAGE_REPLACING="IMAGE_REPLACING"   # 更换镜像
#     PREPARE_RELEASE="PREPARE_RELEASE"   # 释放

# 根据主任务类型（创建 or 操作）处理状态。
def process_main_task(db: Session, check_task: type[InstanceStatusCheckTask]):

    # -------------------
    # 1）创建任务 CREATE
    # -------------------
    instance = db.query(InstanceCreateTask).filter_by(
       id=check_task.main_task_id
    ).first()
    # logger.info(f'查看状态 {check_task.status} {instance.last_operation}')
    if not instance:
        return
    if check_task.status == 3:
        if instance.last_operation == 'INIT' or instance.last_operation == 'PREPARE_START' or instance.last_operation == 'PREPARE_REBOOT':
            instance.status = 'RUNNING'

        elif instance.last_operation == 'PREPARE_STOP':
            instance.status = 'STOPPED'

    # if check_task.status == 3:  # SUCCESS
    #     # 根据 last_operation 决定最终状态
    #     if instance.last_operation == "START":
    #         instance.status = 2  # 运行中
    #     elif instance.last_operation == "STOP":
    #         instance.status = 8  # 已关机
    #     elif instance.last_operation == "REBOOT":
    #         instance.status = 2  # 重启完成，运行中
    #     instance.updated_at = datetime.now(timezone.utc)


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
