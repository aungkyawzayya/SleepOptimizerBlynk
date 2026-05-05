import grpc
from concurrent import futures
import logging
import os

import sensor_data_pb2
import sensor_data_pb2_grpc
from database import save_sensor_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SensorDataService(sensor_data_pb2_grpc.SensorDataServiceServicer):
    def SendSensorData(self, request, context):
        try:
            data = {
                "temperature": request.temperature,
                "sound": request.sound,
                "light": request.light,
                "dust": request.dust,
                "motion": request.motion,
                "fan": request.fan
            }
            save_sensor_data(data)
            return sensor_data_pb2.SensorDataResponse(success=True, message="Data successfully saved via gRPC.")
        except Exception as e:
            logger.error(f"Error saving sensor data via gRPC: {e}")
            return sensor_data_pb2.SensorDataResponse(success=False, message=str(e))

def serve():
    port = os.getenv("GRPC_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sensor_data_pb2_grpc.add_SensorDataServiceServicer_to_server(SensorDataService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"gRPC Server started, listening on {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
