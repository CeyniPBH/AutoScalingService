from concurrent import futures
import time
import grpc
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
        print(
            f"Métricas recibidas de {request.instance_id}: "
            f"status={request.status}, "
            f"CPU={request.cpu_percent}%, "
            f"RAM={request.ram_percent}%, "
            f"load={request.load_percent}%, "
            f"effective_load={request.effective_load_percent}%, "
            f"active_requests={request.active_requests}"
        )
        self.metrics_store[request.instance_id] = {
            'status': request.status,
            'cpu_percent': request.cpu_percent,
            'ram_percent': request.ram_percent,
            'load_percent': request.load_percent,
            'effective_load_percent': request.effective_load_percent,
            'active_requests': request.active_requests,
            'timestamp': request.timestamp
        }
        return monitor_pb2.MetricsResponse(success=True)

    def GetMetrics(self, request, context):
        response = monitor_pb2.MetricsList()
        for instance_id, metrics in self.metrics_store.items():
            instance_metrics = monitor_pb2.InstanceMetrics(
                instance_id=instance_id,
                status=metrics['status'],
                cpu_percent=metrics['cpu_percent'],
                ram_percent=metrics['ram_percent'],
                load_percent=metrics['load_percent'],
                effective_load_percent=metrics['effective_load_percent'],
                active_requests=metrics['active_requests'],
                timestamp=metrics['timestamp']
            )
            response.instances.append(instance_metrics)
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    monitor_pb2_grpc.add_MonitorServiceServicer_to_server(MonitorServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("MonitorS (Servidor) iniciando en el puerto 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
