# capstone-display

Minimal display-side subscriber for `capstone-center`.

Current scope:

- no heartbeat
- no HTML rendering yet
- subscribe to display messages from `capstone-center`
- print the latest raw payload to stdout when a message arrives

## Config

The runtime reads config from `DISPLAY_CONFIG_PATH`.
If unset, it falls back to `config/config.yml`.

Included configs:

- `config/config.yml`
  - default standalone container config
- `config/config.dev.yml`
  - local dev variant
- `config/config.compose.yml`
  - service-to-service config for the monorepo development compose stack

## Run

```bash
docker compose up --build display
```

For monorepo development, the parent compose file can override
`DISPLAY_CONFIG_PATH` with `config/config.compose.yml`.
