#-=- encoding: utf-8 -=-
from flask import Flask, jsonify, request
from nginx import nginx

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
    result = nginxController.add(site, ip)
    return jsonify({'slug': result})


@app.route('/<slug>', methods=['DELETE'])
def delete(slug):
    nginxController.delete(slug)
    return 'OK'


@app.route('/<slug>', methods=['PUT'])
def edit(slug):
    ip = request.json['ip']
    site = request.json['site']
    nginxController.delete(slug)
    result = nginxController.add(site, ip)
    return jsonify({'slugs': result})


if __name__ == "__main__":
    app.debug = DEBUG
    app.run(IP, PORT)
