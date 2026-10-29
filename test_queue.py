from core.sensor_simulator import IoTSensorSimulator
from core.queue_manager import IoTQueueManager

simulator = IoTSensorSimulator()
queue = IoTQueueManager()

for _ in range(10):
    queue.add_reading(simulator.generate_reading())

print("Queue statistics:")
print(queue.get_statistics())
assert queue.get_queue_size() == 10
print("Queue test passed!")
