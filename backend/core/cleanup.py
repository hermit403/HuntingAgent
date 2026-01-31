from datetime import datetime, timedelta
import logging

from database import SessionLocal, AuditResult, Task
from core.config import settings

logger = logging.getLogger(__name__)


async def cleanup_old_data(days: int = 30):
    """
    清理指定天数前的已完成任务和相关数据

    Args:
        days: 要保留的天数，默认为 30 天
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    db = SessionLocal()
    try:
        deleted_results = db.query(AuditResult).filter(
            AuditResult.created_at < cutoff_date
        ).delete()
        logger.info(f"Deleted {deleted_results} old audit results")

        deleted_tasks = db.query(Task).filter(
            Task.status == "completed",
            Task.completed_at < cutoff_date
        ).delete()
        logger.info(f"Deleted {deleted_tasks} old completed tasks")

        db.commit()
        logger.info(f"Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


async def cleanup_old_results(days: int = 30):
    """
    仅清理旧的审计结果

    Args:
        days: 要保留的天数，默认为 30 天
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    db = SessionLocal()
    try:
        deleted = db.query(AuditResult).filter(
            AuditResult.created_at < cutoff_date
        ).delete()
        logger.info(f"Deleted {deleted} old audit results")
        db.commit()
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
