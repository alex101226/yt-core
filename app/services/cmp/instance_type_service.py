from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

from app.models.cmp.instance_type import InstanceType
from app.services.public.cloud_service import CloudService

from app.repositories.public.cloud_provider_repo import CloudProviderRepository

from app.repositories.cmp.instance_type_repo import InstanceTypeRepo

from app.schemas.cmp.instance_type_schema import InstanceTypeSearch, InstanceTypeBase

from app.core.logger import logger

class InstanceTypeService:
    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.instance_type_repo = InstanceTypeRepo(cmp_db)
        self.provider_repo = CloudProviderRepository(public_db)

    #   全量的类型
    def list_instance_types(self, provider_code: str):
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client_region = CloudService(
            self.db,
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        instance_types = client_region.list_instance_types(provider_code)
        return instance_types

    def full_instance_table(self, type_id: str) -> Optional[type[InstanceType]]:
        data = self.instance_type_repo.get_by_instance_type_find(type_id)
        if not data:
            return None
        return data

    def _filter_available_instances(
            self,
            available_map: Dict[str, Dict[str, Any]],
            db_map: Dict[str, InstanceType],
            cpu_number: Optional[int],
            memory_number: Optional[int],
            gpu_spec: Optional[str],
            gpu_name: Optional[str],
            hide_soldout: bool
    ) -> List[Dict[str, Any]]:
        """
        available_map: {instance_type_id: {"status_category": "...", ...}}
        db_map: {instance_type_id: InstanceType}
        返回符合过滤条件的、合并好基础信息的 list（未分页、未查价格）
        """
        out = []
        soldout_categories = {"WithoutStock", "ClosedWithoutStock"}  # 根据需调整
        for it_id, avail in available_map.items():
            inst = db_map.get(it_id)
            if not inst:
                # DB 没有该规格（可能是新规格），跳过或记录日志
                continue

            # 隐藏售罄
            status_cat = avail.get("status_category") or avail.get("StatusCategory") or ""
            if hide_soldout and status_cat not in ("WithStock",):
                continue

            # cpu 过滤
            if cpu_number and inst.cpu_core_count != cpu_number:
                continue

            # memory 过滤（假设以整数 GB 匹配）
            if memory_number and inst.memory_size != memory_number:
                continue

            # gpu_spec 过滤（模糊匹配，比如 "A10"）
            if gpu_spec and (not inst.gpu_spec or gpu_spec.lower() not in inst.gpu_spec.lower()):
                continue

            # gpu_name 过滤（模糊匹配 GPU 制造商或名称）
            if gpu_name:
                gpname = (inst.instance_type_id or "").split()[0]  # 简单提取
                if gpu_name.lower() not in gpname.lower():
                    continue

            out.append({
                "instance_type_id": it_id,
                "status_category": status_cat,
                "cpu_core_count": inst.cpu_core_count,
                "memory_size": inst.memory_size,
                "gpu_amount": inst.gpu_amount,
                "gpu_spec": inst.gpu_spec,
                "gpu_memory": inst.gpu_memory,
                "architecture": inst.architecture,
            })
        return out

    def _fetch_prices_concurrent(
            self,
            client,
            region_id: str,
            instance_type_ids: List[str],
            instance_charge_type: str,
            system_disk_category: str,
            max_workers: int = 10,
            per_call_timeout: float = 8.0,
            retry: int = 1,
    ) -> Dict[str, float]:
        """
        并发请求 DescribePrice（或你 client 的 list_pricing），返回 {instance_type_id: price}
        - per_call_timeout: 单次请求等待超时时间（秒）
        - retry: 失败重试次数（默认再试 1 次）
        如果失败或超时，价格设为 0（可改为 None）。
        """
        prices: Dict[str, float] = {}

        def _call_price(it_id: str):
            last_exc = None
            for attempt in range(retry + 1):
                try:
                    # 这里调用你们的 client.list_pricing 或 client.describe_price 的封装
                    # 如果你的 client 支持传 timeout，请在 client 层实现并传入。
                    res = client.list_pricing(region_id, it_id, instance_charge_type, system_disk_category)
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

    #   可用区
    #   provider_code: 云厂商, region_id: 区域, zone_id: 可用区, instance_charge_type: 付费方式, cpu_number: cpu核数,
    #   memory_number: 内存, gpu_spec: gpu规格, gpu_name: 规格名称, hide_soldout: , 隐藏售罄规格 page, page_size
    def list_available_instance_types(self, search: InstanceTypeSearch):

        provider = self.provider_repo.get_by_code(search.provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client = CloudService(
            self.db,
            search.provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        available_raw = client.list_available_type(
            search.region_id,
            search.zone_id,
            search.instance_charge_type,
            'cloud_essd'
        )
        available_map = {}

        for item in available_raw:
            it_id = item.get("instance_type_id") or item.get("Value") or item.get("InstanceType")
            # 标准化状态字段名
            status = item.get("status_category") or item.get("StatusCategory") or item.get("status") or item.get(
                "Status")
            available_map[it_id] = {"status_category": status}

        if not available_map:
            return {"total": 0, "page": search.page, "page_size": search.page_size, "items": []}

            # 3) 批量从 DB 里拿这些 instanceType 的详细信息（一次 SQL）
        all_ids = list(available_map.keys())
        db_map = self.instance_type_repo.batch_fetch_instance_types_from_db(all_ids)

        # 4) 在内存中过滤（CPU / 内存 / GPU 等）
        filtered = self._filter_available_instances(
            available_map=available_map,
            db_map=db_map,
            cpu_number=search.cpu_number,
            memory_number=search.memory_number,
            gpu_spec=search.gpu_spec,
            gpu_name=search.gpu_name,
            hide_soldout=bool(search.hide_soldout),
        )

        # 5) 分页（注意：分页在过滤之后）
        page = max(1, int(search.page or 1))
        page_size = max(1, int(search.page_size or 10))
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        if not page_items:
            return {"total": total, "page": page, "page_size": page_size, "items": []}

        # 6) 并发查询价格（只查当前页的 items，避免 N 次全量调用）
        instance_type_ids_page = [it["instance_type_id"] for it in page_items]

        prices = self._fetch_prices_concurrent(
            client=client,
            region_id=search.region_id,
            instance_type_ids=instance_type_ids_page,
            instance_charge_type=search.instance_charge_type,
            system_disk_category="cloud_essd",
            max_workers=10,
        )

        # 7) 合并并返回（把价格合并到每个 item）
        out_items = []
        for it in page_items:
            it_id = it["instance_type_id"]
            out_items.append({
                "instance_type_id": it_id,
                "cpu_core_count": it["cpu_core_count"],
                "memory_size": it["memory_size"],
                "gpu_amount": it["gpu_amount"],
                "gpu_spec": it["gpu_spec"],
                "gpu_memory": it["gpu_memory"],
                "architecture": it["architecture"],
                "zone_id": search.zone_id,
                "price": prices.get(it_id, 0),
                "status_category": it.get("status_category"),
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": out_items,
        }

        # instance_all = []
        # for available in available_list:
        #     type_id = available.get('instance_type_id')
        #     #   按instance_type_id来查找全量规格信息
        #     inst = self.full_instance_table(type_id)
        #     if inst:
        #         #   请求价格
        #         price = client.list_pricing(
        #             search.region_id,
        #             type_id,
        #             search.instance_charge_type,
        #             'cloud_essd'
        #         )
        #         # logger.info(f'查看获取到的价格 {price}')
        #         instance_all.append({
        #             "instance_type_id": available['instance_type_id'],
        #             "price": price.get("instancetype", 0),
        #             "cpu_core_count": inst.cpu_core_count,
        #             "gpu_amount": inst.gpu_amount,
        #             "gpu_spec": inst.gpu_spec,
        #             "gpu_memory": inst.gpu_memory,
        #             "zone_id": search.zone_id,
        #             "architecture": inst.architecture,
        #             "memory_size": inst.memory_size,
        #         })
        # return instance_all
