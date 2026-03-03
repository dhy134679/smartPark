"""初始化数据库并填充模拟数据。"""

import asyncio
import sys
from pathlib import Path

# 将 backend 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal
from app.models import Base, SpotStatusLog
from ai.prediction.data_generator import generate_samples


async def init_database():
    """创建表结构（如果尚不存在）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def seed_data():
    """填充模拟的车位状态日志数据（用于 LSTM 预测）。"""
    async with AsyncSessionLocal() as session:
        # 预测日志依赖车位主键，先确认存在至少一个车位。
        spot_row = await session.execute(
            text("SELECT id FROM parking_spots ORDER BY id LIMIT 1")
        )
        first_spot_id = spot_row.scalar()
        if not first_spot_id:
            print("ℹ️  未找到车位数据，跳过状态日志填充")
            return

        cap_row = await session.execute(text("SELECT COUNT(*) FROM parking_spots"))
        capacity = int(cap_row.scalar() or 50)

        # 检查是否已有数据
        result = await session.execute(text("SELECT COUNT(*) FROM spot_status_logs"))
        count = result.scalar()
        if count and count > 0:
            print(f"ℹ️  已有 {count} 条状态日志，跳过数据填充")
            return

        # 生成 7 天的模拟数据
        samples = generate_samples(days=7)
        for sample in samples:
            total_occupied = int(round(sample.occupancy_rate * capacity))
            total_occupied = max(0, min(capacity, total_occupied))
            log = SpotStatusLog(
                spot_id=int(first_spot_id),
                status="occupied" if sample.occupancy_rate >= 0.5 else "free",
                occupancy_rate=sample.occupancy_rate,
                total_occupied=total_occupied,
                total_free=max(0, capacity - total_occupied),
                hour=sample.hour,
                day_of_week=sample.day_of_week,
                is_weekend=sample.is_weekend,
                timestamp=sample.created_at,
            )
            session.add(log)
        await session.commit()
        print(f"✅ 已插入 {len(samples)} 条模拟状态日志")


async def main():
    print("🚀 开始初始化数据库...")
    await init_database()
    await seed_data()
    print("🎉 初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
