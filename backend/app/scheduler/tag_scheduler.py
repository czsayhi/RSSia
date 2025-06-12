"""
标签缓存定时任务调度器
实现标签缓存的定时更新和清理
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import atexit

from app.services.tag_cache_service import tag_cache_service


class TagScheduler:
    """标签缓存调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # 注册关闭处理
        atexit.register(self.shutdown)
        
        # 启动定时任务
        self._setup_jobs()
        
        logger.info("标签缓存调度器已启动")
    
    def _setup_jobs(self):
        """设置定时任务"""
        
        # 任务1: 每10分钟检查并更新需要刷新的用户标签缓存
        self.scheduler.add_job(
            func=self._update_user_tags_job,
            trigger=IntervalTrigger(minutes=10),
            id='update_user_tags',
            name='更新用户标签缓存',
            replace_existing=True
        )
        
        # 任务2: 每天凌晨2点清理过期缓存
        self.scheduler.add_job(
            func=self._cleanup_expired_cache_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_expired_cache',
            name='清理过期标签缓存',
            replace_existing=True
        )
        
        # 任务3: 每小时强制更新活跃用户标签（确保数据新鲜度）
        self.scheduler.add_job(
            func=self._force_update_active_users_job,
            trigger=IntervalTrigger(hours=1),
            id='force_update_active_users',
            name='强制更新活跃用户标签',
            replace_existing=True
        )
        
        logger.info("标签缓存定时任务已设置")
    
    def _update_user_tags_job(self):
        """更新用户标签缓存任务"""
        try:
            logger.info("开始执行用户标签缓存更新任务")
            
            # 获取需要更新的用户
            users_need_update = tag_cache_service.get_users_need_cache_update()
            
            if not users_need_update:
                logger.info("没有用户需要更新标签缓存")
                return
            
            # 批量更新
            result = tag_cache_service.batch_update_user_tags(users_need_update)
            
            logger.info(f"用户标签缓存更新完成: {result}")
            
        except Exception as e:
            logger.error(f"用户标签缓存更新任务失败: {e}")
    
    def _cleanup_expired_cache_job(self):
        """清理过期缓存任务"""
        try:
            logger.info("开始执行过期缓存清理任务")
            
            deleted_count = tag_cache_service.cleanup_expired_cache(days=7)
            
            logger.info(f"过期缓存清理完成: 删除{deleted_count}条记录")
            
        except Exception as e:
            logger.error(f"过期缓存清理任务失败: {e}")
    
    def _force_update_active_users_job(self):
        """强制更新活跃用户标签任务"""
        try:
            logger.info("开始执行活跃用户标签强制更新任务")
            
            # 获取活跃用户（最近24小时有订阅的用户）
            active_users = tag_cache_service.get_users_need_cache_update()
            
            if not active_users:
                logger.info("没有活跃用户需要强制更新")
                return
            
            # 限制每次更新的用户数量，避免性能问题
            max_users_per_batch = 50
            users_to_update = active_users[:max_users_per_batch]
            
            result = tag_cache_service.batch_update_user_tags(users_to_update)
            
            logger.info(f"活跃用户标签强制更新完成: {result}")
            
        except Exception as e:
            logger.error(f"活跃用户标签强制更新任务失败: {e}")
    
    def get_job_status(self):
        """获取任务状态"""
        jobs = self.scheduler.get_jobs()
        job_status = []
        
        for job in jobs:
            job_status.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return job_status
    
    def trigger_manual_update(self, user_id: int = None):
        """手动触发标签更新"""
        try:
            if user_id:
                # 更新指定用户
                result = tag_cache_service.update_user_tags_cache(user_id)
                logger.info(f"手动更新用户{user_id}标签缓存: {len(result)}个标签")
                return {"user_id": user_id, "tags_count": len(result)}
            else:
                # 更新所有需要更新的用户
                users_need_update = tag_cache_service.get_users_need_cache_update()
                result = tag_cache_service.batch_update_user_tags(users_need_update)
                logger.info(f"手动批量更新标签缓存: {result}")
                return result
                
        except Exception as e:
            logger.error(f"手动触发标签更新失败: {e}")
            raise
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("标签缓存调度器已关闭")


# 创建全局调度器实例
tag_scheduler = TagScheduler() 