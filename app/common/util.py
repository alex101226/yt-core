from datetime import datetime

def gen_random_name(type):
    return f"{type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

