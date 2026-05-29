import grpc
from concurrent import futures
import monitor_pb2
import monitor_pb2_grpc

class MonitorServiceServicer(monitor_pb2_grpc.MonitorServiceServicer):
    def __init__(self):
        self.metrics_store = {}
        self.registered_instances = {}

    def RegisterInstance(self, request, context):
        print(f"Registrando instancia: {request.instance_id} con IP: {request.ip_address}")
        self.registered_instances[request.instance_id] = request.ip_address
        return monitor_pb2.RegisterResponse(success=True, message="Instancia registrada con éxito")

    def SendMetrics(self, request, context):
        print(f"Métricas recibidas de {request.instance_id}: CPU={request.cpu_utilization}%, RAM={request.memory_utilization}%")
        self.metrics_store[request.instance_id] = {
            'cpu_utilization': request.cpu_utilization,
            'memory_utilization': request.memory_utilization,
            'timestamp': request.timestamp
        }
        return monitor_pb2.MetricsResponse(success=True)

    def GetMetrics(self, request, context):
        response = monitor_pb2.MetricsList()
        for instance_id, metrics in self.metrics_store.items():
            response.instances.add(
                instance_id=instance_id,
                cpu_utilization=metrics['cpu_utilization'],
                memory_utilization=metrics['memory_utilization'],
                timestamp=metrics['timestamp']
            )
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    monitor_pb2_grpc.add_MonitorServiceServicer_to_server(MonitorServiceServicer(), server)
    server.add_insecure_port('0.0.0.0:50051')
    print("MonitorS (Servidor) iniciando en el puerto 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
