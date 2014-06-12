# -=- encoding: utf-8 -=-
from path import path
from jinja2 import Environment, PackageLoader
from sh import service
import slugify
import re
import logging
import os

env = Environment(loader=PackageLoader('nginx', 'templates'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/var/log/nginx-api/debug.log')
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
    NGINX_PATH = '/etc/nginx/vagrant-sites-enabled/'

    def __init__(self):
        self._reload()

    def _reload(self):
        sitesPath = path(self.NGINX_PATH).files()
        self.sites = []
        for site in sitesPath:
            content = site.text()

            slug = unicode(site.name)
            (ip, port) = self._get_ip_port(content)
            domain = self._get_domain(content)
            htpasswd = self._get_htpasswd(content)
            sslkey = self._get_sslkey(content)
            self.sites.append(
                {
                    'slug': slug,
                    'ip': ip,
                    'port': port,
                    'domain': domain,
                    'htpasswd': htpasswd,
                    'sslkey': sslkey,
                }
            )

    def _reload_server(self):
        service('nginx', 'reload', _bg=True, silent=True)

    def slugify(self, string):
        if type(string) == str:
            string = unicode(string)
        return slugify.slugify(string)

    def add(self, _site, _ip, _htpasswd=None, _sslkey=None):
        slug = self.slugify(_site)
#        if '.pheromone.ca' not in _site:
#            raise InvalidDomain('Given {} domain is invalid'.format(_site))

        if not self._find(slug):
            logger.debug('Adding site {}'.format(_site))
            configFile = path(self.NGINX_PATH + slug)
            config = self._compile_config(_site, slug, _ip, _htpasswd, _sslkey)
            # logger.debug(' {}'.format(config))
            configFile.write_text(config)
            self._reload()
            self._reload_server()

            return slug
        else:
            raise DomainAlreadyExists

    def delete(self, _site):
        slug = self.slugify(_site)
        if self._find(slug):
            logger.debug('Deleting site {}'.format(_site))
            config = path(self.NGINX_PATH + slug)
            config.remove()
            self._reload()
            self._reload_server()
        else:
            raise DomainNotFound()

    def list(self):
        self._reload()
        logger.debug('list : {}'.format(self.sites))
        return self.sites

    def _get_domain(self, content):
        match = re.search(r'server_name (.*);', content)
        domain = None
        if match:
            domain = match.group(1)

        return domain

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

    def _get_sslkey(self, content):
        sslkey = None
        match = re.search(r'ssl_certificate_key (.*)/(.*).key;', content)
        if match:
            sslkey = match.group(2)

        return sslkey

    def _get_htpasswd(self, content):
        match = re.search(r'passwords/(.*);', content)
        htpasswd = None
        if match:
            htpasswd = match.group(1)

        logger.debug('htpasswd {}'.format(htpasswd))
        return htpasswd

    def _find(self, slug):
        for domain in self.sites:
            if domain['slug'] == slug:
                return domain

        return None

    def _compile_config(self, _site, _slug, _ip, _htpasswd=None, _sslkey=None):
        server = self._compile_config_partial(_site, _slug, _ip, _htpasswd)
        if _sslkey:
            # We call the same function with the SSL param
            server += os.linesep + self._compile_config_partial(
                _site,
                '{}ssl'.format(_slug),
                _ip,
                _htpasswd,
                _sslkey
            )
        return server

    def _compile_config_partial(self, _site, _slug, _ip, _htpasswd=None,
                                _sslkey=None):
        port = 80
        if _sslkey:
            port = 443

        server = env.get_template('server')
        server = server.render(site=_site, port=port, sslkey=_sslkey)

        upstream = env.get_template('upstream')
        upstream = upstream.render(slug=_slug, ip=_ip, port=port)

        location = env.get_template('location')
        location = location.render(slug=_slug, sslkey=_sslkey)

        ssl = None
        if _sslkey:
            ssl = env.get_template('ssl')
            ssl = ssl.render(sslkey=_sslkey)

        if _htpasswd:
            htpasswd = env.get_template('access')
            htpasswd = htpasswd.render(site=_site, htpasswd=_htpasswd)
            location = location.replace('#htpasswd', htpasswd)
        else:
            location = location.replace('#htpasswd', '')

        server = server.replace('#upstream', upstream)
        server = server.replace('#location', location)
        if ssl:
            server = server.replace('#ssl', ssl)
        else:
            server = server.replace('#ssl', '')

        return server
