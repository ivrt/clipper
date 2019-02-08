from clipper_admin import ClipperConnection, DockerContainerManager
from clipper_admin.deployers import keras as keras_deployer
import os
import keras
import time
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Embedding, GlobalAveragePooling1D, InputLayer
from keras.layers import Dropout, LSTM, Bidirectional, GlobalMaxPool1D
import keras.backend as K
from keras.models import load_model, model_from_json

import gzip
import dill as pickle

import urllib3
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

from pprint import pprint

clipper_conn = ClipperConnection(DockerContainerManager())

# Check if we have a clipper running on k8s and connect
# If not, then rebuild it from scratch
# try:
    # clipper_conn.connect()
# except:
clipper_conn.stop_all()
clipper_conn.start_clipper()
time.sleep(30)

def reformat_model_name(old_name):
    new_name = ''
    for letter in old_name:
        if letter.isupper():
            new_name += '-'
        new_name += letter.lower()
    return new_name

# For testing purposes, if you do not want to load all the models, you can slice the list
# of models. For example os.listdir('models')[:6] preferably in multiples of 3 because
# there are 93 files (31 models architectures, 31 model weights and 31 language vectorizers)
for file in os.listdir('models')[:6]:
    file_ext = file.split('.')[-1:][0]
    file_name = file.split('_')[:1][0]
    if file_ext == "h5":
        shortname = reformat_model_name(file_name)
        print('-' * 20, shortname, '-' * 20)
        architecture_path = [x for x in os.listdir('models') if x.split('.')[-1:][0] == "json" and file_name == x.split('_')[:1][0]][0]
        model_weights_path = [x for x in os.listdir('models') if x.split('.')[-1:][0] == "h5" and file_name == x.split('_')[:1][0]][0]
        preprocessor_path = [x for x in os.listdir('models') if x.split('.')[-1:][0] == "pkl" and file_name == x.split('_')[:1][0]][0]

        print('trying to register app ', shortname)
        try:
            clipper_conn.register_application(name=shortname, input_type='strings', default_output='Unknown', slo_micros=100000000)
        except:
            print('blew up ', shortname)
            continue

        # Loading pre-trained Keras model
        model = model_from_json(open(os.path.join('models', architecture_path)).read())
        model.load_weights(os.path.join('models', model_weights_path))
        with open(os.path.join('models', preprocessor_path), 'rb') as file:
            text2Dataset = pickle.load(file)

        # setup model
        def get_result(model, strings):
            list_of_strings = [x.decode('utf-8').strip() for x in strings]
            preprocessed_strings = text2Dataset.preprocess(list_of_strings)
            raw_result = [model.predict(x) for x in preprocessed_strings]
            clean_result = []
            for r in raw_result:
                clean_result.append([text2Dataset.idx2label[np.argmax(r[0])], r[0]])
            return clean_result


        keras_deployer.deploy_keras_model(clipper_conn=clipper_conn,
            name=shortname,
            version="1",
            input_type="strings",
            func=get_result,
            model_path_or_object=model,
            base_image='keras-container')

        clipper_conn.link_model_to_app(app_name=shortname, model_name=shortname)
        print('Linked and done')
        time.sleep(2)

models = clipper_conn.get_all_models()
print('models')
print(models)

apps = clipper_conn.get_all_apps()
print('apps')
print(apps)
