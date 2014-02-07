#-=- encoding: utf-8 -=-
from path import path
from jinja2 import Environment, PackageLoader
from sh import service
import slugify
import re
import logging

env = Environment(loader=PackageLoader('nginx', 'templates'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('nginxapi.log')
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
            self.sites.append(
                {
                    'slug': slug,
                    'ip': ip,
                    'port': port,
                    'domain': domain,
                    'htpasswd': 'francois',
                }
            )

    def _reload_server(self):
        service('nginx', 'reload', _bg=True, silent=True)

    def slugify(self, string):
        if type(string) == str:
            string = unicode(string)
        return slugify.slugify(string)

    def add(self, _site, _ip, _htpasswd=None):
        slug = self.slugify(_site)
        if '.pheromone.ca' not in _site:
            raise InvalidDomain

        if not self._find(slug):
            configFile = path(self.NGINX_PATH + slug)
            config = self._compile_config(_site, slug, _ip, _htpasswd)
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
            #Should be [ip, port]
            infos = infos.split(':')
            ip = infos[0]
            if len(infos) > 1:
                port = infos[1]

        return (ip, port)

    def _find(self, slug):
        for domain in self.sites:
            if domain['slug'] == slug:
                return domain

        return None

    def _compile_config(self, _site, _slug, _ip, _htpasswd=None):
        server = env.get_template('server')
        server = server.render(site=_site)

        upstream = env.get_template('upstream')
        upstream = upstream.render(slug=_slug, ip=_ip)

        location = env.get_template('location')
        location = location.render(slug=_slug)

        if _htpasswd:
            htpasswd = env.get_template('access')
            htpasswd = htpasswd.render(site=_site, htpasswd=_htpasswd)
            location = location.replace('#htpasswd', htpasswd)
        else:
            location.replace('#htpasswd', '')

        server = server.replace('#upstream', upstream)
        server = server.replace('#location', location)

        return server
