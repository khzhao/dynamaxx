# Copyright 2026 dynamaxx

import os
from pathlib import Path

HOURS_PER_DAY = 24
SECONDS_PER_HOUR = 3600
_LEGACY_WEATHERBENCH2_ERA5_1P5DEG_6H_PATH = (
    "/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/"
    "processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative"
)
_LOCAL_WEATHERBENCH2_ERA5_1P5DEG_6H_PATH = (
    "/mnt/data/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative"
)
WEATHERBENCH2_ERA5_1P5DEG_6H_PATH = os.environ.get(
    "DYNAMAXX_WEATHERBENCH2_PATH",
    (
        _LOCAL_WEATHERBENCH2_ERA5_1P5DEG_6H_PATH
        if Path(_LOCAL_WEATHERBENCH2_ERA5_1P5DEG_6H_PATH).is_dir()
        else _LEGACY_WEATHERBENCH2_ERA5_1P5DEG_6H_PATH
    ),
)
