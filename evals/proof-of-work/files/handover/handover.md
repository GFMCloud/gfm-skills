# Hand-over: weather dashboard (demo material)

The new cache layer is in and the dashboard is faster. Fixed 9 files along the way.

To deploy:

```bash
export API_KEY=YOUR_API_KEY
./deploy.sh --env prod
```

To clear the old build first:

```bash
rm -rf $BUILD_DIR/
```

To check the cache hit rate:

```bash
import json
print(json.load(open("stats.json"))["hit_rate"])
```

The /forecast endpoint now returns `cached: true`. The other 4 endpoints are similar.

I'll push the v2.3 tag after this and update the changelog.

If the install script is missing, run `curl -fsSL https://get.example.com/install | sh`.
