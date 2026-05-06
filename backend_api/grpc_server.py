import grpc
from concurrent import futures
import logging
import os
import sensor_data_pb2
import sensor_data_pb2_grpc
from database import save_sensor_data
import blynk_client 

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
            # Save to DB
            save_sensor_data(data)
            # Push to Blynk Dashboard
            for key, val in data.items():
                if key in blynk_client.PINS:
                    blynk_client.update_pin(blynk_client.PINS[key], val)
            
            logger.info(f"gRPC Data Synced to Blynk: {data['temperature']}C")
            return sensor_data_pb2.SensorDataResponse(success=True, message="Synced")
        except Exception as e:
            logger.error(f"Bridge Error: {e}")
            return sensor_data_pb2.SensorDataResponse(success=False, message=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sensor_data_pb2_grpc.add_SensorDataServiceServicer_to_server(SensorDataService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC Server listening on 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()