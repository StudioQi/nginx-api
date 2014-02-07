#-=- encoding: utf-8 -=-
#salut
from flask import Flask, jsonify, request, abort
from nginx import nginx, DomainNotFound

PORT = 5000
IP = '0.0.0.0'
DEBUG = True
app = Flask(__name__)

nginxController = nginx()


@app.route('/', methods=['GET'])
def list():
    return jsonify({'domains': nginxController.list()})


@app.route('/', methods=['POST'])
def add():
    site = request.json['site']
    ip = request.json['ip']
    access = None
    if 'htpasswd' in request.json:
        access = request.json['htpasswd']

    result = nginxController.add(site, ip, access)
    return jsonify({'slug': result})


@app.route('/<slug>', methods=['DELETE'])
def delete(slug):
    try:
        nginxController.delete(slug)
    except DomainNotFound:
        abort(404)

    return 'OK'


@app.route('/<slug>', methods=['PUT'])
def edit(slug):
    ip = request.json['ip']
    site = request.json['site']
    try:
        nginxController.delete(slug)
        htpasswd = None
        if 'htpasswd' in request.json:
            htpasswd = request.json['htpasswd']

        result = nginxController.add(site, ip, htpasswd)
    except DomainNotFound:
        abort(404)
    else:
        return jsonify({'slugs': result})


if __name__ == "__main__":
    app.debug = DEBUG
    app.run(IP, PORT)
