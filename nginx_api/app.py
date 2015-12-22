# -=- encoding: utf-8 -=-
from nginx_api import app, DEBUG, PORT, IP

if __name__ == "__main__":
    app.debug = DEBUG
    app.run(IP, PORT)
