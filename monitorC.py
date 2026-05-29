from concurrent import futures
import requests

import grpc
import monitor_pb2 
import monitor_pb2_grpc 

# Constants for the Flask app endpoints
FLASK_METRICS_URL = "http://127.0.0.1:5000/metrics"
FLASK_HEALTH_URL = "http://127.0.0.1:5000/health"


class MonitorService(monitor_pb2_grpc.MonitorServiceServicer):

    def Ping(self, request, context):
        try:
            response = requests.get(FLASK_HEALTH_URL,timeout=2)

            if response.status_code != 200:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("App healthcheck failed")
                return monitor_pb2.Pong() # type: ignore
            data = response.json()

            if data.get("status") != "alive":
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("App not alive")
                return monitor_pb2.Pong() # type: ignore
            return monitor_pb2.Pong(message="pong")# type: ignore

        except Exception as e:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"AppInstance unreachable: {str(e)}")
            return monitor_pb2.Pong()# type: ignore

    def GetNodeMetrics(self, request, context):
        try:
            response = requests.get(FLASK_METRICS_URL,timeout=2)

            if response.status_code != 200:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Metrics endpoint failed")
                return monitor_pb2.InstanceMetrics()# type: ignore
            data = response.json()

            return monitor_pb2.InstanceMetrics(# type: ignore
                instance_id="local_flask_instance",
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
            return monitor_pb2.InstanceMetrics()# type: ignore

def serve():

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    monitor_pb2_grpc.add_MonitorServiceServicer_to_server(
        MonitorService(),
        server
    )

    server.add_insecure_port("[::]:50052")
    server.start()
    print("MonitorC gRPC server running on port 50052")

    # Registrar esta instancia en MonitorS (que corre en el puerto 50051)
    try:
        print("Intentando registrar instancia en MonitorS...")
        channel = grpc.insecure_channel('127.0.0.1:50051')
        stub = monitor_pb2_grpc.MonitorServiceStub(channel)
        request = monitor_pb2.RegisterRequest(
            instance_id="nodo_flask_1",
            ip_address="127.0.0.1"
        )
        response = stub.RegisterInstance(request, timeout=5)
        print(f"Éxito: {response.message}")
    except Exception as e:
        print(f"Advertencia: No se pudo registrar en MonitorS: {e}")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()