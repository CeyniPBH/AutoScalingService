from concurrent import futures
import requests

import grpc
import metrics_pb2 
import metrics_pb2_grpc 

# Constants for the Flask app endpoints
FLASK_METRICS_URL = "http://127.0.0.1:5000/metrics"
FLASK_HEALTH_URL = "http://127.0.0.1:5000/health"


class MonitorService(metrics_pb2_grpc.MonitorServiceServicer):

    def Ping(self, request, context):
        try:
            response = requests.get(FLASK_HEALTH_URL,timeout=2)

            if response.status_code != 200:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("App healthcheck failed")
                return metrics_pb2.Pong() # type: ignore
            data = response.json()

            if data.get("status") != "alive":
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("App not alive")
                return metrics_pb2.Pong() # type: ignore
            return metrics_pb2.Pong(message="pong")# type: ignore

        except Exception as e:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"AppInstance unreachable: {str(e)}")
            return metrics_pb2.Pong()# type: ignore

    def GetMetrics(self, request, context):
        try:
            response = requests.get(FLASK_METRICS_URL,timeout=2)

            if response.status_code != 200:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Metrics endpoint failed")
                return metrics_pb2.MetricsResponse()# type: ignore
            data = response.json()

            return metrics_pb2.MetricsResponse(# type: ignore
                status=data["status"],
                cpu_percent=data["cpu_percent"],
                ram_percent=data["ram_percent"],
                load_percent=data["load_percent"],
                effective_load_percent=data["effective_load_percent"],
                active_requests=data["active_requests"],
                timestamp=data["timestamp"]
            )

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return metrics_pb2.MetricsResponse()# type: ignore

def serve():

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    metrics_pb2_grpc.add_MonitorServiceServicer_to_server(
        MonitorService(),
        server
    )

    server.add_insecure_port("[::]:50051")
    server.start()
    print("MonitorC gRPC server running on port 50051")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()