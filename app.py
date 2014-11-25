# -=- encoding: utf-8 -=-
from flask import Flask, jsonify, request, abort
from nginx import nginx, DomainNotFound

PORT = 5001
IP = '0.0.0.0'
DEBUG = True
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

    access = None
    ssl_key = None

    if 'htpasswd' in request.json:
        access = request.json['htpasswd']
    if 'ssl_key' in request.json:
        ssl_key = request.json['ssl_key']

    result = nginxController.add(id, uri, upstreams, access, ssl_key)
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
    site = request.json['uri']
    try:
        nginxController.delete(id)
    except Exception:
        pass

    upstreams = request.json['upstreams']
    uri = request.json['uri']
    access = None
    ssl_key = None

    if 'htpasswd' in request.json:
       access = request.json['htpasswd']
    if 'ssl_key' in request.json:
       ssl_key = request.json['ssl_key']


    result = nginxController.add(id, uri, upstreams, access, ssl_key)
    return jsonify({'slugs': result})


if __name__ == "__main__":
    app.debug = DEBUG
    app.run(IP, PORT)
