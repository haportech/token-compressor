"""MCP server for Token Compressor."""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .compressors.compress import compress
from .token_counter import count_tokens

server = Server("token-compressor")


def handle_compress(
    text: str,
    strategy: str = "auto",
    target_tokens: int = 4000,
    strip_keys: str = "",
) -> str:
    """Handle compress tool call (non-async for testing)."""
    keys = [k.strip() for k in strip_keys.split(",") if k.strip()] if strip_keys else None
    return compress(text, strategy=strategy, target_tokens=target_tokens, strip_keys=keys)


def handle_count_tokens(text: str) -> dict:
    """Handle count_tokens tool call."""
    return {
        "tokens": count_tokens(text),
        "chars": len(text),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="compress",
            description=(
                "Compress text to reduce token usage. Strategies: auto (dedup+truncate), "
                "truncate (boundary-aware cut), deduplicate (collapse repeats), "
                "json (minify+strip keys). Default: auto at 4000 tokens."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to compress"},
                    "strategy": {
                        "type": "string",
                        "enum": ["auto", "truncate", "deduplicate", "json"],
                        "default": "auto",
                    },
                    "target_tokens": {
                        "type": "integer",
                        "default": 4000,
                        "description": "Target token count for truncate/auto",
                    },
                    "strip_keys": {
                        "type": "string",
                        "default": "",
                        "description": "Comma-separated keys to strip (json strategy)",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="count_tokens",
            description="Count tokens in text using cl100k_base encoding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to count tokens for"},
                },
                "required": ["text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "compress":
        result = compress(
            text=arguments["text"],
            strategy=arguments.get("strategy", "auto"),
            target_tokens=arguments.get("target_tokens", 4000),
            strip_keys=(
                [k.strip() for k in arguments.get("strip_keys", "").split(",") if k.strip()]
                if arguments.get("strip_keys")
                else None
            ),
        )
        return [TextContent(type="text", text=result)]

    if name == "count_tokens":
        result = handle_count_tokens(arguments["text"])
        return [TextContent(type="text", text=str(result))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Async entry point for stdio MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
