# Token Compressor

MCP server that compresses text to save LLM tokens. Three strategies: smart
truncation, deduplication, JSON minification.

## Architecture
- `src/token_compressor/server.py` — MCP server entry point
- `src/token_compressor/compressors/` — compression strategies
- `src/token_compressor/token_counter.py` — tiktoken wrapper (cl100k_base)

## Commands
- Run tests: `.venv/bin/python3 -m pytest tests/ -v`
- Run server: `.venv/bin/python3 -m token_compressor.server`
- Quick test: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | .venv/bin/python3 -m token_compressor.server`

## Code Standards
- Type hints on all public functions
- pytest for testing
- No external API calls (fully local compression)
