def cloud_regions_key(cloud_code: str):
    return f"cloud:{cloud_code}:regions"


def cloud_zones_key(cloud_code: str, region_id: str):
    return f"cloud:{cloud_code}:{region_id}:zones"


def cloud_images_key(cloud_code: str, region_id: str):
    return f"cloud:{cloud_code}:{region_id}:images"


def cloud_instance_types_key(cloud_code: str, region_id: str):
    return f"cloud:{cloud_code}:{region_id}:instance_types"


def cloud_available_types_key(cloud_code: str, region_id: str):
    return f"cloud:{cloud_code}:{region_id}:available_types"


def cloud_system_disks_key(cloud_code: str, region_id: str):
    return f"cloud:{cloud_code}:{region_id}:system_disks"


def cloud_prices_key(cloud_code: str, region_id: str):
    return f"cloud:{cloud_code}:{region_id}:prices"
