from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import case, and_

from app.core.logger import logger

from app.models.cmp.network_vpc import Vpc
from app.models.cmp.network_subnet import Subnet
from app.models.cmp.network_security_group import SecurityGroup
from app.models.cmp.storage_gpfs import GPFSFile
from app.models.cmp.storage_cephfs import CephfsFile

from app.models.cmp.storage_mount_point import FileSystemMount
from app.schemas.cmp.fs_mount_schema import FileSystemMountCreate, FileSystemMountPage

class FileMountRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建挂载点 cephfs/gpfs
    def fs_mount_create(self, data: dict) -> bool:
        mount = FileSystemMount(**data)
        self.db.add(mount)
        # self.db.commit()
        # self.db.refresh(mount)
        return mount

    def fs_mount_page_list(
        self,
        page: int,
        page_size: int,
        user_id: int,
        mount_type: str,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        mount_name: Optional[str] = None,
    ):
        query = (
            self.db.query(
                FileSystemMount.id,
                FileSystemMount.mount_id,
                FileSystemMount.mount_alias,
                FileSystemMount.mount_name,
                FileSystemMount.domain_name,
                FileSystemMount.security_group_id,
                FileSystemMount.status,
                FileSystemMount.cloud_provider_code,
                FileSystemMount.region_id,
                FileSystemMount.zone_id,
                FileSystemMount.instance_id,
                FileSystemMount.vpc_id,
                FileSystemMount.subnet_id,
                FileSystemMount.fs_type,
                FileSystemMount.fs_id,
                FileSystemMount.created_at,
                FileSystemMount.updated_at,
                SecurityGroup.sg_name.label("security_group_name"),
                Vpc.vpc_name.label("vpc_name"),
                Subnet.subnet_name.label("subnet_name"),
                case(
                    (FileSystemMount.fs_type == "gpfs", GPFSFile.fs_name),
                    (FileSystemMount.fs_type == "cephfs", CephfsFile.fs_name),
                    else_=None
                ).label("fs_name")
            )
            .outerjoin(
                SecurityGroup,
                SecurityGroup.id == FileSystemMount.security_group_id
            )
            .outerjoin(
                Vpc,
                Vpc.id == FileSystemMount.vpc_id
            )
            .outerjoin(
                Subnet,
                Subnet.id == FileSystemMount.subnet_id
            ).outerjoin(
                GPFSFile, and_(GPFSFile.id == FileSystemMount.fs_id,FileSystemMount.fs_type == "gpfs")
            )
            .outerjoin(
                CephfsFile, and_(CephfsFile.id == FileSystemMount.fs_id, FileSystemMount.fs_type == "cephfs")
            )
        )

        filters = [FileSystemMount.created_by == user_id, FileSystemMount.is_released == 0]
        if mount_type:
            filters.append(FileSystemMount.fs_type == mount_type)
        if provider_code:
            filters.append(FileSystemMount.cloud_provider_code == provider_code)
        if region_id:
            filters.append(FileSystemMount.region_id == region_id)
        if zone_id:
            filters.append(FileSystemMount.zone_id == zone_id)
        if mount_name:
            filters.append(FileSystemMount.mount_name.like(f"%{mount_name}%"))

        if filters:
            query = query.filter(*filters)
        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(FileSystemMount.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total


    # 查询
    def get_by_id(self, mount_id: int) -> Optional[dict]:
        row = self.db.query(FileSystemMount).filter(FileSystemMount.id == mount_id).first()
        return row

    # 卸载
    def uninstall(self, mount_id: int):
        find = self.get_by_id(mount_id)
        if not find:
            return None
        find.status = 'UNMOUNTING'
        # self.db.commit()
        # self.db.refresh(find)
        return find

    def release(self, mount_id: int):
        find = self.get_by_id(mount_id)
        if not find:
            return None
        find.status = 'RELEASED'
        find.is_released = True
        self.db.commit()
        self.db.refresh(find)
        return find