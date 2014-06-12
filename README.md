# NGINX-API

Small REST API to add and remove site. Currently used with [vagrant-control](https://github.com/Pheromone/vagrant-control) to route local vagrant machines. 

Can be used with [htpasswd-api](https://github.com/Pheromone/htpasswd-api) to generate a htpasswd file.

The API can be run as root or any other user, as long as nginx has access to the sites generated.

## Roadmap

    - Better configuration management
    - Complete abstraction of vagrant
    - Configurable main TLD restriction

## License

[Creative Commons Attribution 3.0 Unported] [2]
  [2]: https://raw.github.com/Pheromone/nginx-api/master/LICENSE.txt

# Note 

Keep in mind that this project is closer to ALPHA than to STABLE. DO NOT use on production system.
