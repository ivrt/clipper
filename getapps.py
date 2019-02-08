from clipper_admin import ClipperConnection, KubernetesContainerManager
clipper_conn = ClipperConnection(KubernetesContainerManager(useInternalIP=True, kubernetes_proxy_addr="127.0.0.1:8001"))
clipper_conn.connect()
print(clipper_conn.get_all_models())
