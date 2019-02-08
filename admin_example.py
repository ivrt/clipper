from clipper_admin import ClipperConnection, KubernetesContainerManager
from clipper_admin.deployers import keras as keras_deployer

import os
import keras
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Embedding, GlobalAveragePooling1D, InputLayer
from keras.layers import Dropout, LSTM, Bidirectional, GlobalMaxPool1D
import  keras.backend as K
from keras.models import load_model, model_from_json
import gzip
import dill as pickle

import urllib3
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

# Create a clipper connection
clipper_conn = ClipperConnection(KubernetesContainerManager(
    useInternalIP=True,
    kubernetes_proxy_addr="127.0.0.1:8001",
    create_namespace_if_not_exists=True,
    ))

# Connect to an already-running Clipper cluster
clipper_conn.connect()

# Clear and rebuild cluster
# clipper_conn.stop_all()
# clipper_conn.start_clipper()

def reformat_model_name(old_name):
    new_name = ''
    for letter in old_name:
        if letter.isupper():
            new_name += '-'
        new_name += letter.lower()
    return new_name

for file in os.listdir('models'):
    file_name, file_ext = file.split('.')
    if file_ext == "h5" and file_name != 'termDefinite':
        shortname = reformat_model_name(file_name)
        architecture_path = [x for x in os.listdir('models') if x.split('.')[1] == "json" and file_name in x][0]
        model_weights_path = [x for x in os.listdir('models') if x.split('.')[1] == "h5" and file_name in x][0]
        preprocessor_path = [x for x in os.listdir('models') if x.split('.')[1] == "pkl" and file_name in x][0]

        print(shortname, architecture_path, model_weights_path, preprocessor_path)

        clipper_conn.register_application(name=shortname, input_type='strings', default_output='Unknown', slo_micros=100000000)

        # Loading pre-trained Keras model
        model = model_from_json(open(os.path.join('models', architecture_path)).read())
        model.load_weights(os.path.join('models', model_weights_path))
        with open(os.path.join('models', preprocessor_path), 'rb') as file:
            text2Dataset = pickle.load(file)

        # setup model
        def get_result(model, strings):
            preprocessed_strings = []
            for string in strings:
                text = ','.join([words for words in string.decode('utf-8').split(',')]).strip().replace('\n', '')
                X = text2Dataset.words2idx(text)
                X = text2Dataset.add_ngram([X])
                X = sequence.pad_sequences(X, maxlen=100)
                preprocessed_strings.append(X)

            raw_result = [model.predict(x) for x in preprocessed_strings]
            clean_result = []
            for r in raw_result:
                clean_result.append([(text2Dataset.idx2label[idx], r[idx]) for idx in range(len(r))])

            return clean_result


        keras_deployer.deploy_keras_model(clipper_conn=clipper_conn,
            name=shortname,
            version="1",
            pkgs_to_install=["docker","keras"],
            input_type="strings",
            func=get_result,
            model_path_or_object=model,
            base_image='keras-container')

        clipper_conn.link_model_to_app(app_name=shortname, model_name=shortname)

    elif file_ext == "h5" and file_name == 'termDefinite':
        shortname = reformat_model_name(file_name)
        architecture_path = [x for x in os.listdir('models') if x.split('.')[1] == "json" and file_name in x][0]
        model_weights_path = [x for x in os.listdir('models') if x.split('.')[1] == "h5" and file_name in x][0]
        preprocessor_path = [x for x in os.listdir('models') if x.split('.')[1] == "pkl" and file_name in x][0]

        print(shortname, architecture_path, model_weights_path, preprocessor_path)

        clipper_conn.register_application(name=shortname, input_type='strings', default_output='Unknown', slo_micros=100000000)

        # Loading pre-trained Keras model
        model = model_from_json(open(os.path.join('models', architecture_path)).read())
        model.load_weights(os.path.join('models', model_weights_path))
        with open(os.path.join('models', preprocessor_path), 'rb') as file:
            text2Dataset = pickle.load(file)

        # setup model
        def get_result(model, strings):
            preprocessed_strings = []
            for string in strings:
                text = ','.join([words for words in string.decode('utf-8').split(',')]).strip().replace('\n', '')
                X = text2Dataset.words2idx(text)
                X = text2Dataset.add_ngram([X])
                X = sequence.pad_sequences(X, maxlen=200)
                preprocessed_strings.append(X)

            raw_result = [model.predict(x) for x in preprocessed_strings]
            clean_result = []
            for r in raw_result:
                clean_result.append([(text2Dataset.idx2label[idx], r[idx]) for idx in range(len(r))])

            return clean_result


        keras_deployer.deploy_keras_model(clipper_conn=clipper_conn,
            name=shortname,
            version="1",
            input_type="strings",
            func=get_result,
            model_path_or_object=model,
            registry="registry.pactly.ai",
            base_image='keras-container')

        clipper_conn.link_model_to_app(app_name=shortname, model_name=shortname)


models = clipper_conn.get_all_models()
print('models')
print(models)

apps = clipper_conn.get_all_apps()
print('apps')
print(apps)
