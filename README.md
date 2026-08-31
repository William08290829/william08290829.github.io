# williamchen.me

My portfolio website, built with a custom static site generator. Template from [sagarreddypatil/portfolio-website](https://github.com/sagarreddypatil/portfolio-website).

## Dependencies

```
pnpm install
uv sync
```

## Development

```
uv run python src/build.py --output dist
pnpm dev
```

## Production

```
pnpm build
```

## Images

High-resolution originals live in the ignored OneDrive-backed `assets-original/`
directory. Generate optimized derivatives under `public/assets/` with:

```
pnpm images
pnpm images -- --force
```

## Map

```
williamchen.me
├── README.md                     # this file
├── dist                          # output directory
├── LICENSE                       # MIT License
├── package.json                  # JS dependencies & dev server target
├── pnpm-lock.yaml
├── tailwind.config.js
├── pyproject.toml                # Python dependencies
├── uv.lock
├── build.sh                      # prod build script, called by pnpm build
├── public
│   ├── assets/                   # static assets, images
│   └── photography/              # photos (optional)
├── src
│   ├── build.py                  # main entrypoint
│   ├── dev-server.py             # live reload server
│   ├── index.css                 # just tailwind imports
│   ├── optimize_images.py        # image optimization script
│   └── templates
│       ├── components            # reusable components
│       │   ├── button.html
│       │   └── fieldset.html
│       ├── index.html            # landing page
│       └── layout.html           # base layout
```
