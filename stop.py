from clipper_admin import ClipperConnection, DockerContainerManager
from clipper_admin.deployers import keras as keras_deployer
clipper_conn = ClipperConnection(DockerContainerManager())
clipper_conn.stop_all()
