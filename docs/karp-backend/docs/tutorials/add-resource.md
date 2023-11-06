# Add a resource to karp

In this tutorial we are gonna add the resource `Lex Lex` to Karp.

All commands are supposed to run after `poetry shell` (that is, in an activated virtual environment).

1. [Create a resource config](create-resource-config.md)
   - In this example we have saved the config in `path/to/parolelexplus.json`
2. Add an entry repository: `karp-cli entry-repo create path/to/parolelexplus.json`
3. Add a resource: `karp-cli resource create path/to/parolelexplus.json`
   - This command will list currently non-deleted entry-repos along with numbers, choose the highest number for your resource
   - In our running example, choose: `parolelexplus`
4. Publish the resource: `karp-cli resource publish <resource_id>`
   - In our example: `karp-cli resource publish parolelexplus`
5. Before adding entries, we can dry-run and validate them: `karp-cli entries validate --resource_id <resource_id> <path/to/entries>`
   - In our example: `karp-cli entries validate --resource_id parolelexplus path/to/parolelexplus.jsonl`
6. Adding entries, can be done in 2 ways, both methods can read `json`, `jsonl`, `json.gz` or `jsonl.gz` files:
   1. Add all in one go: `karp-cli entries add <resource_id> <path/to/entries>`
      - In our example: `karp-cli entries add parolelexplus path/to/parolelexplus.jsonl`
   2. Add all but in chunks: `karp-cli entries add <resource_id> <path/to/entries> --chunked --chunk-size <number (default: 1000)>`
      - This version works by addind `<chunk-size>` entries to the database and indexes them in the search-service (e.g. ElasticSearch).
      - The pro with this method is that not all entries are held in memory.
      - The con is that if a later chunk fails, all previously added chunks are stored, that is the resource is partially added. Manual intervention can be needed.
      - In our example: `karp-cli entries add parolelexplus path/to/parolelexplus.jsonl --chunked --chunk-size 10000`
   3. **NOTE** If are going to add a large resource this can take several hours, please use `nohup` for better experience.
      - For instance `nohup karp-cli entries add <resource_id> <path/to/entries> --chunked > stdout.log 2> stderr.log.jsonl &`.
      - Karp print logs to stderr in jsonl format.
      - In our example: `nohup karp-cli entries add parolelexplus path/to/parolelexplus.jsonl --chunked > stdout.log 2> stderr.log.jsonl &`
