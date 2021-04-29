[![GitHub license](https://img.shields.io/github/license/xiazeyu/collector)](https://github.com/xiazeyu/collector/blob/main/LICENSE) [![GitHub stars](https://img.shields.io/github/stars/xiazeyu/collector)](https://github.com/xiazeyu/collector/stargazers)

![Docker Cloud Automated build](https://img.shields.io/docker/cloud/automated/xiazeyu2011/collector)![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/xiazeyu2011/collector)![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/xiazeyu2011/collector)

![GitHub top language](https://img.shields.io/github/languages/top/xiazeyu/collector)![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/xiazeyu/collector)

# collector

Collect files and rename it using python

lightweight. easy to use.

### Usage

```bash
docker run --detach \
  --name collector \
  --env "PRODUCTION=1" \
  --env "VIRTUAL_HOST=collector.domain.com" \
  --env "LETSENCRYPT_HOST=collector.domain.com" \
  --volume /collector/db:/app/db \
  --volume /collector/received:/app/received \
  --volume /etc/localtime:/etc/localtime:ro \
  --restart=always \
  xiazeyu2011/collector
```

## Online update

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower --cleanup --run-once collector
```

