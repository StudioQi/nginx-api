# -=- encoding: utf-8 -=-
from flask import Flask, jsonify, request, abort
from nginx import nginx, DomainNotFound
from os.path import abspath, realpath
from os import remove

PORT = 5001
IP = '0.0.0.0'
DEBUG = True
SSL_PATH = '/etc/ssl/private'
app = Flask(__name__)

nginxController = nginx()


@app.route('/', methods=['GET'])
def list():
    return jsonify({'domains': nginxController.list()})


@app.route('/', methods=['POST'])
def add():
    id = request.json['id']
    uri = request.json['uri']
    upstreams = request.json['upstreams']
    aliases = request.json['aliases']

    access = None
    ssl_key = None

    if 'htpasswd' in request.json:
        access = request.json['htpasswd']
    if 'ssl_key' in request.json:
        ssl_key = request.json['ssl_key']

    result = nginxController.add(id, uri, aliases, upstreams, access, ssl_key)
    return jsonify({'slug': result})


@app.route('/<int:id>', methods=['DELETE'])
def deleteById(id):
    try:
        nginxController.delete(id)
    except DomainNotFound:
        abort(404)

    return 'OK'


@app.route('/<int:id>', methods=['PUT'])
def edit(id):
    try:
        nginxController.delete(id)
    except Exception:
        pass

    aliases = request.json['aliases']
    upstreams = request.json['upstreams']
    uri = request.json['uri']
    access = None
    ssl_key = None

    if 'htpasswd' in request.json:
        access = request.json['htpasswd']
    if 'ssl_key' in request.json:
        ssl_key = request.json['ssl_key']

    result = nginxController.add(id, uri, aliases, upstreams, access, ssl_key)
    return jsonify({'slugs': result})


@app.route('/ssl', methods=['POST'])
def add_ssl():
    """Receive an SSL certificate"""
    query = request.get_json()
    name = query.get('name')
    cert = query.get('cert')
    key = query.get('key')
    with open('{0}/{1}.crt'.format(SSL_PATH, name), 'w') as f:
        f.write(cert)
    with open('{0}/{1}.key'.format(SSL_PATH, name), 'w') as f:
        f.write(key)


@app.route('/ssl/<name>', methods=['DELETE'])
def delete_ssl(name):
    """Delete an SSL certificate"""
    # Resolve the path
    key_path = abspath(
        realpath(
            '{0}/{1}.key'.format(SSL_PATH, name)))
    cert_path = abspath(
        realpath(
            '{0}/{1}.key'.format(SSL_PATH, name)))
    if not key_path.startswith(SSL_PATH) or \
       not cert_path.startswith(SSL_PATH):
        return False
    remove(key_path)
    remove(cert_path)

if __name__ == "__main__":
    app.debug = DEBUG
    app.run(IP, PORT)
