# create deployment and service
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Load Kubernetes configuration
config.load_kube_config()

# Apps API for Deployments
apps_api = client.AppsV1Api()

# Core API for Services
core_api = client.CoreV1Api()

# --- Deployment ---
deployment = client.V1Deployment(
    api_version="apps/v1",
    kind="Deployment",
    metadata=client.V1ObjectMeta(name="my-flask-app"),
    spec=client.V1DeploymentSpec(
        replicas=1,
        selector=client.V1LabelSelector(
            match_labels={"app": "my-flask-app"}
        ),
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": "my-flask-app"}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="my-flask-container",
                        image="521819599734.dkr.ecr.ap-south-1.amazonaws.com/my_monitoring_app_image:latest",
                        ports=[client.V1ContainerPort(container_port=5000)]
                    )
                ]
            )
        )
    )
)

try:
    apps_api.create_namespaced_deployment(namespace="default", body=deployment)
    print("Deployment created.")
except ApiException as e:
    if e.status == 409:  # AlreadyExists
        apps_api.replace_namespaced_deployment(
            name="my-flask-app",
            namespace="default",
            body=deployment
        )
        print("Deployment updated.")
    else:
        raise

# --- Service ---
service = client.V1Service(
    api_version="v1",
    kind="Service",
    metadata=client.V1ObjectMeta(name="my-flask-service"),
    spec=client.V1ServiceSpec(
        selector={"app": "my-flask-app"},
        ports=[client.V1ServicePort(port=5000, target_port=5000)],
        type="LoadBalancer"  # 👉 change to "NodePort" if not using cloud LB
    )
)

try:
    core_api.create_namespaced_service(namespace="default", body=service)
    print("Service created.")
except ApiException as e:
    if e.status == 409:  # AlreadyExists
        core_api.replace_namespaced_service(
            name="my-flask-service",
            namespace="default",
            body=service
        )
        print("Service updated.")
    else:
        raise

# --- Get External Service URL ---
service_obj = core_api.read_namespaced_service(name="my-flask-service", namespace="default")
if service_obj.status.load_balancer.ingress:
    lb_ip = service_obj.status.load_balancer.ingress[0].hostname or service_obj.status.load_balancer.ingress[0].ip
    print(f"Access your app at: http://{lb_ip}:5000")
else:
    print("Waiting for LoadBalancer to get an external IP/hostname...")
