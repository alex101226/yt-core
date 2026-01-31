import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any, Optional

from app.core.logger import logger


# 定义裸金属的过滤
def is_bare_metal(instance_family: str) -> bool:
    return instance_family.startswith("ecs.ebm")

def match_instance_type(instance_family: str, type_: str) -> bool:
    if type_ == "emb":
        return instance_family.startswith("ecs.ebm")
    if type_ == "cloud":
        return not instance_family.startswith("ecs.ebm")
    return True  # 不传 type，则全部返回

# 过滤可用区规格的信息
async def filter_spec(instance_type_ids: List[str], all_spec_list):
    if not instance_type_ids:
        return {}
    spec_list = [spec for spec in all_spec_list if spec['instance_type_id'] in instance_type_ids]
    # return spec_list
    return {r['instance_type_id']: r for r in spec_list}

#  在内存中过滤（CPU / 内存 / GPU 等）
def filter_available_instances(
    available_map: Dict[str, Dict[str, Any]],
    db_map: Dict[str, Any],
    cpu_number: Optional[int],
    memory_number: Optional[int],
    gpu_name: Optional[str],
    instance_spec: Optional[str],
    hide_soldout: bool,
    model_type: Optional[str] = None,
):
    """
    available_map: {instance_type_id: {"status_category": "...", ...}}
    db_map: {instance_type_id: InstanceType}
    返回符合过滤条件的、合并好基础信息的 list（未分页、未查价格）
    """
    # logger.info(f'传递给你的map {available_map}')
    out = []
    soldout_categories = {"WithoutStock", "ClosedWithoutStock"}  # 根据需调整
    for it_id, avail in available_map.items():
        inst = db_map.get(it_id)
        # logger.info(f"it_id={inst}, avail={avail}")
        if not inst:
            # DB 没有该规格（可能是新规格），跳过或记录日志
            continue
        # ⭐ model_type（裸金属 / 云服务器）过滤
        if not match_instance_type(inst["instance_family"], model_type):
            continue

        # ⭐ 裸金属必须有 GPU
        if model_type == "emb":
            if not inst.get("gpu_amount") or inst.get("gpu_amount", 0) <= 0:
                continue
        # 隐藏售罄
        status_cat = avail.get("status_category") or ""
        if hide_soldout and status_cat not in ("WithStock",):
            continue
        # logger.info(f'cpu_number {cpu_number} {memory_number} {gpu_name} {instance_spec}')
        # cpu 过滤
        if cpu_number and inst['cpu_core_count'] != cpu_number:
            continue

        # memory 过滤（假设以整数 GB 匹配）
        if memory_number and inst['memory_size'] != memory_number:
            continue

        # gpu_name 过滤（模糊匹配 GPU 制造商或名称）
        if gpu_name:
            gpname = (inst['instance_type_id'] or "").split()[0]  # 简单提取
            if gpu_name.lower() not in gpname.lower():
                continue

        # gpu_spec 过滤（模糊匹配，比如 "A10"）
        if instance_spec and (not inst['gpu_spec'] or instance_spec.lower() not in inst['gpu_spec'].lower()):
            continue

        out.append({
            "instance_type_id": it_id,
            "status_category": status_cat,
            "instance_family": inst['instance_family'],
            "cpu_core_count": inst['cpu_core_count'],
            "memory_size": inst['memory_size'],
            "gpu_amount": inst['gpu_amount'],
            "gpu_spec": inst['gpu_spec'],
            "gpu_memory": inst['gpu_memory'],
            "architecture": inst['architecture'],
        })
    return out


# 获取规格价格
def fetch_prices_concurrent(
    client,
    region_id: str,
    instance_type_ids: List[str],
    instance_charge_type: str,
    system_disk_category: str,
    max_workers: int = 10,
    per_call_timeout: float = 8.0,
    retry: int = 1,
    ) -> Dict[str, float]:
    prices: Dict[str, float] = {}

    def _call_price(it_id: str):
        last_exc = None
        for attempt in range(retry + 1):
            try:
                # 这里调用你们的 client.list_pricing 或 client.describe_price 的封装
                # 如果你的 client 支持传 timeout，请在 client 层实现并传入。
                res = client.instance_price(region_id, it_id, instance_charge_type, system_disk_category)
                # logger.info(f'是异步函数嘛？{res}')
                # 你的 client 可能返回 dict 嵌套，取 instancetype 字段或按你的实现调整
                # 下面兼容常见两种结构
                if isinstance(res, dict):
                    price = res.get("instancetype") or res.get("instanceType") or res.get("price") or 0
                else:
                    price = getattr(res, "price", 0)
                return it_id, price
            except Exception as e:
                last_exc = e
                logger.warning("price fetch failed (attempt %s) for %s: %s", attempt + 1, it_id, e)
                # 简短退避
                time.sleep(0.2 * (attempt + 1))
        # 全部重试失败
        logger.error("price fetch ultimately failed for %s: %s", it_id, last_exc)
        return it_id, 0

    # 使用 ThreadPoolExecutor 并发
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        future_to_it = {exe.submit(_call_price, it_id): it_id for it_id in instance_type_ids}
        for fut in as_completed(future_to_it):
            it_id = future_to_it[fut]
            try:
                # fut.result() 默认会阻塞直到完成；这里也可以加超时保护
                res_it, price = fut.result(timeout=per_call_timeout)
            except FuturesTimeoutError:
                logger.error("price request timeout for %s", it_id)
                price = 0
            except Exception as e:
                logger.exception("unexpected error when fetching price for %s: %s", it_id, e)
                price = 0
            prices[it_id] = price
    return prices