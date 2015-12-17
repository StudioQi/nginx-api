# -=- encoding: utf-8 -=-
from path import path
from jinja2 import Environment, PackageLoader
from sh import service
import slugify
import re
import logging
import os
from os.path import abspath, realpath
from os import remove

env = Environment(loader=PackageLoader('nginx_api', 'templates'))
SSL_PATH = os.environ.get('SSL_PATH', '/etc/ssl/private')
LOGS = os.environ.get('LOGS', '/var/log/nginx-api/debug.log')
NGINX_CONFIG_PATH = os.environ.get('NGINX_CONFIG_PATH',
                                   '/etc/nginx/vagrant-sites-enabled/')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(LOGS)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)


class DomainNotFound(Exception):
    pass


class DomainAlreadyExists(Exception):
    pass


class InvalidDomain(Exception):
    pass


class nginx():
    sites = []
    NGINX_PATH = NGINX_CONFIG_PATH

    def __init__(self):
        self._reload()

    def _reload(self):
        sitesPath = path(self.NGINX_PATH).files()
        self.sites = []
        for site in sitesPath:
            print(site)
            content = site.text()

            slug = unicode(site.name)
            id = self._get_id(content)
            uri = self._get_uri(content)
            aliases = self._get_aliases(content)
            htpasswd = self._get_htpasswd(content)
            ssl_key = self._get_ssl_key(content)
            self.sites.append(
                {
                    'id': int(id),
                    'slug': slug,
                    'uri': uri,
                    'aliases': aliases,
                    'htpasswd': htpasswd,
                    'ssl_key': ssl_key,
                }
            )

    def _reload_server(self):
        service('nginx', 'reload', _bg=True, silent=True)

    def slugify(self, string):
        if type(string) == str:
            string = unicode(string)
        return slugify.slugify(string)

    def add(
            self, _id,
            _uri, _aliases, _upstreams,
            _htpasswd=None, _ssl_key=None):
        slug = self.slugify(_uri)
        self._reload()
#        if '.pheromone.ca' not in _site:
#            raise InvalidDomain('Given {} domain is invalid'.format(_site))

        if not self._find(slug):
            logger.debug('Adding site {}'.format(_uri))
            configFile = path(self.NGINX_PATH + slug)
            config = self._compile_config(
                _id, _uri, _aliases,
                slug, _upstreams, _htpasswd, _ssl_key)
            configFile.write_text(config)
            self._reload()
            self._reload_server()

            return slug
        else:
            raise DomainAlreadyExists

    def save_ssl(self, name, key, cert):
        """This should save the file in the desired folder for SSL"""
        with open('{0}/{1}.crt'.format(SSL_PATH, name), 'w') as f:
            f.write(cert)
        with open('{0}/{1}.key'.format(SSL_PATH, name), 'w') as f:
            f.write(key)
        return name

    def delete_ssl(self, name):
        # Resolve the path
        key_path = abspath(
            realpath(
                '{0}/{1}.key'.format(SSL_PATH, name)))
        cert_path = abspath(
            realpath(
                '{0}/{1}.crt'.format(SSL_PATH, name)))
        if not key_path.startswith(SSL_PATH) or \
           not cert_path.startswith(SSL_PATH):
            return False
        remove(key_path)
        remove(cert_path)

    def delete(self, _id):
        self._reload()
        domain = self._findById(_id)
        if domain is not None:
            logger.debug('Deleting site {}'.format(domain['uri']))
            config = path(self.NGINX_PATH + domain['slug'])
            config.remove()
            self._reload()
            self._reload_server()
        else:
            raise DomainNotFound()

    def list(self):
        self._reload()
        logger.debug('list : {}'.format(self.sites))
        return self.sites

    def _get_id(self, content):
        match = re.search(r'#id: (.*)', content)
        id = None
        if match:
            id = match.group(1)

        return id

    def _get_uri(self, content):
        match = re.search(r'server_name (.*);', content)
        uri = None
        if match:
            uri = match.group(1).split(' ')[0]

        return uri

    def _get_aliases(self, content):
        match = re.search(r'server_name (.*);', content)
        aliases = None
        if match:
            aliases = match.group(1).split(' ')[1:]

        return aliases

    def _get_ip_port(self, content):
        ip = None
        port = None
        match = re.search(r'server (.*);', content)
        if match:
            infos = match.group(1)
            # Should be [ip, port]
            infos = infos.split(':')
            ip = infos[0]
            if len(infos) > 1:
                port = infos[1]

        return (ip, port)

    def _get_ssl_key(self, content):
        ssl_key = None
        match = re.search(r'ssl_certificate_key (.*)/(.*).key;', content)
        if match:
            ssl_key = match.group(2)

        return ssl_key

    def _get_htpasswd(self, content):
        match = re.search(r'passwords/(.*);', content)
        htpasswd = None
        if match:
            htpasswd = match.group(1)

        return htpasswd

    def _find(self, slug):
        for domain in self.sites:
            if domain['slug'] == slug:
                return domain

    def _findById(self, id):
        for domain in self.sites:
            if domain['id'] == int(id):
                return domain

        return None

    def _compile_config(self, _id, _site, _aliases, _slug, _upstreams, _htpasswd=None,
                        _ssl_key=None):
        server = self._compile_config_partial(
            _id,
            _site,
            _aliases,
            _slug,
            _upstreams,
            _htpasswd
        )
        if _ssl_key:
            # We call the same function with the SSL param
            server += os.linesep + self._compile_config_partial(
                _id,
                _site,
                _aliases,
                _slug,
                _upstreams,
                _htpasswd,
                _ssl_key
            )
        return server

    def _compile_config_partial(
            self, _id, _site, _aliases,
            _slug, _upstreams, _htpasswd=None,
            _ssl_key=None):
        port = 80
        if _ssl_key:
            port = 443

        _upstreams_has_ssl = False
        for upstream in _upstreams:
            if 'port_ssl' in upstream and upstream['port_ssl'] != 0:
                _upstreams_has_ssl = True

        _slug = _slug
        if _upstreams_has_ssl and _ssl_key:
            _slug = '{}ssl'.format(_slug)

        server = env.get_template('server')
        server = server.render(
            id=_id, site=_site, aliases=_aliases,
            port=port, ssl_key=_ssl_key)

        def get_upstream_by_location():
            locations = {}
            _locations = []
            upstreams = []
            # populate a dict of locations, with all their respective upstreams
            for upstream in _upstreams:
                upstream_location = upstream.get('location', '/')
                if not upstream_location.startswith('/'):
                    upstream_location = "/" + upstream_location
                if upstream_location not in locations:
                    locations[upstream_location] = []
                locations[upstream_location].append(upstream)
                logger.debug(locations)
            try:
                for loc in locations:
                    # we need special slugs for each location/upstream
                    l_slug = _slug
                    if loc is not None:
                        l_slug = '{}_{}'.format(
                            _slug,
                            loc.replace('/', '_'))
                    upstream = env.get_template('upstream')
                    # create an upstream section specific to the location
                    upstreams.append(
                        upstream.render(
                            slug=l_slug,
                            upstreams=locations[loc],
                            location=loc,
                            ssl_key=_ssl_key,
                            upstreams_has_ssl=_upstreams_has_ssl))

                    location = env.get_template('location')
                    try:
                        # if any upstream is not marked as 'websocket'
                        # then the location is not
                        ws = all([x.get('websocket') for x in locations[loc]])
                        t = location.render(
                            slug=l_slug, ssl_key=_ssl_key,
                            websocket=ws,
                            location=loc,
                            upstreams_has_ssl=_upstreams_has_ssl)
                        _locations.append(t)
                    except Exception as e:
                        logger.debug(e)
            except Exception as e:
                logger.debug(e)
            return [
                '\n'.join(_locations),
                '\n'.join(upstreams)
                ]

        location, upstream = get_upstream_by_location()

        ssl = None
        if _ssl_key:
            ssl = env.get_template('ssl')
            ssl = ssl.render(ssl_path=SSL_PATH, ssl_key=_ssl_key)

        if _htpasswd:
            htpasswd = env.get_template('access')
            htpasswd = htpasswd.render(site=_site, htpasswd=_htpasswd)
            server = server.replace('#htpasswd', htpasswd)
        else:
            server = server.replace('#htpasswd', '')

        server = server.replace('#upstream', upstream)
        server = server.replace('#location', location)
        if ssl:
            server = server.replace('#ssl', ssl)
        else:
            server = server.replace('#ssl', '')

        return server
