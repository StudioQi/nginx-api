# NGINX-API

Small REST API to add and remove site. Currently used with [vagrant-control](https://github.com/Pheromone/vagrant-control) to route local vagrant machines. 

Can be used with [htpasswd-api](https://github.com/Pheromone/htpasswd-api) to generate a htpasswd file.

The API can be run as root or any other user, as long as nginx has access to the sites generated.

## Roadmap

    - Better configuration management
    - Complete abstraction of vagrant
    - Configurable main TLD restriction
