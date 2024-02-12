from rich import print
import psutil

virtual_memory = psutil.virtual_memory()
for key, value in virtual_memory._asdict().items():
    if value < 100:
        print(f"{key:<10}:{value:>10.2f} %")
    else:
        print(f"{key:<10}: {value / 1024 / 1024:>10.2f} MB")

sensors = psutil.sensors_temperatures()
print(sensors)
