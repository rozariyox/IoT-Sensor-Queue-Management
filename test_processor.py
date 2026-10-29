from core.sensor_simulator import IoTSensorSimulator
from core.queue_manager import IoTQueueManager
from core.data_processor import SensorDataProcessor
from database.database_manager import DatabaseManager

queue = IoTQueueManager()
simulator = IoTSensorSimulator()
database = DatabaseManager()
processor = SensorDataProcessor(queue, database)

for _ in range(10):
    queue.add_reading(simulator.generate_reading())

print("Before processing:", queue.get_statistics())
while queue.get_queue_size():
    result = processor.process_next()
    print(result["sensor_id"], result["value"], result["unit"],
          result["status"], result["processing_time_ms"], "ms")
print("After processing:", queue.get_statistics())
print("Processor test passed!")
