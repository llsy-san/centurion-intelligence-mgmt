#!/usr/bin/env python3
"""
测试 Celery 集成
"""
import asyncio
import time
from celery_app import celery_app
from app.celery_tasks import sync_orders, sync_full_orders, data_analysis, custom_task


def test_celery_connection():
    """测试 Celery 连接"""
    try:
        # 检查 Celery 连接
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery 连接成功")
            print(f"活跃 Worker 数量: {len(stats)}")
            for worker_name in stats.keys():
                print(f"  - {worker_name}")
        else:
            print("⚠️  没有发现活跃的 Worker")
            
        return stats is not None
        
    except Exception as e:
        print(f"❌ Celery 连接失败: {e}")
        return False


def test_task_submission():
    """测试任务提交"""
    try:
        print("\n🚀 测试任务提交...")
        
        # 测试自定义任务
        task_result = custom_task.delay(
            task_name="test_task",
            params={"message": "Hello Celery!"}
        )
        
        print(f"✅ 任务已提交: {task_result.id}")
        
        # 等待任务完成
        print("⏳ 等待任务完成...")
        result = task_result.get(timeout=30)
        
        print(f"✅ 任务完成: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 任务提交失败: {e}")
        return False


def test_task_status():
    """测试任务状态查询"""
    try:
        print("\n📊 测试任务状态查询...")
        
        # 获取注册的任务
        inspect = celery_app.control.inspect()
        registered = inspect.registered()
        
        if registered:
            print("✅ 已注册的任务:")
            for worker, tasks in registered.items():
                print(f"  Worker: {worker}")
                for task in tasks:
                    print(f"    - {task}")
        
        # 获取活跃任务
        active = inspect.active()
        if active:
            print("✅ 活跃任务:")
            for worker, tasks in active.items():
                print(f"  Worker: {worker} - {len(tasks)} 个任务")
        else:
            print("ℹ️  当前没有活跃任务")
            
        return True
        
    except Exception as e:
        print(f"❌ 查询任务状态失败: {e}")
        return False


def test_scheduled_tasks():
    """测试定时任务配置"""
    try:
        print("\n⏰ 测试定时任务配置...")
        
        beat_schedule = celery_app.conf.beat_schedule
        
        if beat_schedule:
            print("✅ 已配置的定时任务:")
            for name, config in beat_schedule.items():
                print(f"  - {name}:")
                print(f"    任务: {config['task']}")
                print(f"    调度: {config['schedule']}")
                if 'options' in config:
                    print(f"    选项: {config['options']}")
        else:
            print("⚠️  没有配置定时任务")
            
        return True
        
    except Exception as e:
        print(f"❌ 检查定时任务配置失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 Celery 集成测试开始...\n")
    
    success_count = 0
    total_tests = 4
    
    # 测试连接
    if test_celery_connection():
        success_count += 1
        
    # 测试任务状态
    if test_task_status():
        success_count += 1
        
    # 测试定时任务配置
    if test_scheduled_tasks():
        success_count += 1
        
    # 只有在有Worker的情况下才测试任务提交
    inspect = celery_app.control.inspect()
    stats = inspect.stats()
    
    if stats:
        if test_task_submission():
            success_count += 1
    else:
        print("\n⚠️  跳过任务提交测试（没有活跃的 Worker）")
        total_tests -= 1
    
    print(f"\n📋 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！Celery 集成成功！")
        print("\n💡 下一步:")
        print("1. 启动 Worker: celery -A celery_app worker --loglevel=info")
        print("2. 启动 Beat: celery -A celery_app beat --loglevel=info")
        print("3. 启动 Flower: celery -A celery_app flower --port=5555")
        print("4. 访问监控界面: http://localhost:5555")
    else:
        print("❌ 部分测试失败，请检查配置")
        
    return success_count == total_tests


if __name__ == "__main__":
    main()