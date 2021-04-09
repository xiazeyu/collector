# collector
Collect files and rename it using python

extremely lightweight. no js, each HTML files < 2KB.

### Usage

```bash
docker run --detach \
  --name collector \
  --env "VIRTUAL_HOST=collector.domain.com" \
  --env "LETSENCRYPT_HOST=collector.domain.com" \
  --volume /collector/db:/app/db \
  --volume /collector/received:/app/received \
  --volume /etc/localtime:/etc/localtime:ro \
  --restart=always \
  xiazeyu2011/collector
```

