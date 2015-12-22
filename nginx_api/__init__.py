from flask import Flask, jsonify, request, abort
from nginx_api.nginx import nginx, DomainNotFound
import os

PORT = 5001
IP = '0.0.0.0'
DEBUG = os.environ.get('DEBUG', "1") == "1"
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
    return jsonify({'state': nginxController.save_ssl(name, key, cert)})


@app.route('/ssl/<name>', methods=['DELETE'])
def delete_ssl(name):
    """Delete an SSL certificate"""
    return jsonify({'state': nginxController.delete_ssl(name)})
