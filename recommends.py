import csv
import json
import time
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler


def timeit(f):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print(f'time: {te - ts}')
        return result

    return timed


@timeit
def read_file():
    file_name = 'recommends.csv'
    data = csv.DictReader(open(file_name), fieldnames=['sku', 'recommended_sku', 'index'])
    return data


@timeit
def prepare_result_dict(data):
    res_dict = defaultdict(dict)
    for num, i in enumerate(data):
        res_dict[i['sku']][i['recommended_sku']] = i['index']
    return res_dict


@timeit
def find_value(value, res_dict, index_rec=None):
    if index_rec is None or index_rec == 0:
        return res_dict[value]
    else:
        indexed_res_dict = {sku: index for sku, index in res_dict[value].items() if index_rec <= float(index)}
        return indexed_res_dict


class Server(BaseHTTPRequestHandler):

    def do_GET(self):
        params = {}
        param_SKU = None
        param_index = None
        message = b'Success 200\n'
        try:
            params = {param.split(sep='=')[0]: param.split(sep='=')[1] for param in self.path[2:].split(sep='&')}
            param_SKU = params['SKU']
        except (KeyError, IndexError):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Error 400. '
                             b'Enter GET-parameters "SKU"(necessarily) and "index"(optional) to get data. '
                             b'For example: http://localhost:8000/?SKU=WP260qJAo6&index=0.8')
        try:
            param_index = float(params['index'])
        except KeyError:
            message = b'\nSuccess, but "index" is not introduced. The parameter sets to "None" \n '
        except ValueError:
            message = b'\nSuccess, but an error occurred to the "index", it must be like "0.0". ' \
                      b'The parameter sets to "None" \n '
        if param_SKU is not None:
            user_dict = find_value(value=param_SKU, res_dict=result_dict, index_rec=param_index)
            user_encode_data = json.dumps(user_dict, indent=2).encode('utf-8')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message)
            self.wfile.write(user_encode_data)


raw_data = read_file()
print('Ожидайте примерно 2-3 минуты, чтобы в оперативную память загрузились данные')
result_dict = prepare_result_dict(raw_data)
httpd = HTTPServer(('localhost', 8000), Server)
print('Сервер запущен, сделайте запрос по адресу localhost:8000 с параметрами SKU и index')
print('Например http://localhost:8000/?SKU=WP260qJAo6&index=0.8')
httpd.serve_forever()
