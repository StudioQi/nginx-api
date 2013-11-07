#-=- encoding: utf-8 -=-
from path import path
from jinja2 import Environment, PackageLoader
from sh import service
import slugify
import re

env = Environment(loader=PackageLoader('nginx', 'templates'))


class nginx():
    sites = []
    NGINX_PATH = '/etc/nginx/sites-enabled/'

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
                    'domain': domain
                }
            )
        service('nginx', 'restart')

    def slugify(self, string):
        if type(string) == str:
            string = unicode(string)
        return slugify.slugify(string)

    def add(self, _site, _ip):
        slug = self.slugify(_site)
        if not self._find(slug) and '.pheromone.ca' in _site:
            template = env.get_template('site')
            config = template.render(slug=slug, ip=_ip, site=_site)
            configFile = path(self.NGINX_PATH + slug)
            configFile.write_text(config)
            self._reload()

            return slug

    def delete(self, _site):
        slug = self.slugify(_site)

        if self._find(slug):
            config = path(self.NGINX_PATH + slug)
            config.remove()
            self._reload()

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
