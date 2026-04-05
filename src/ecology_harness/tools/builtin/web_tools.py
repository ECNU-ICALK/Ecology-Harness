from __future__ import annotations

from html import unescape
from urllib.parse import quote_plus
from urllib import error, request
import re

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_web_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="WebFetch",
            description="Fetch a web page over HTTP GET and return the response body.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
            },
            handler=_web_fetch,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="WebSearch",
            description="Search the web and return a small set of result titles and URLs.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
            handler=_web_search,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _web_fetch(params: dict, context: ToolContext) -> ToolResult:
    if not context.settings.sandbox_allow_network:
        raise ToolError("WebFetch is unavailable because sandbox network access is disabled.")
    url = params["url"]
    req = request.Request(
        url,
        headers={
            "User-Agent": "EcologyHarness/0.1",
        },
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=context.settings.command_timeout_sec) as response:
            body = response.read(context.settings.max_web_bytes + 1)
            text = body.decode("utf-8", errors="replace")
            truncated = len(body) > context.settings.max_web_bytes
    except error.HTTPError as exc:
        raise ToolError("WebFetch HTTP error %s for %s" % (exc.code, url)) from exc
    except error.URLError as exc:
        raise ToolError("WebFetch connection error for %s: %s" % (url, exc)) from exc

    if truncated:
        text = text[: context.settings.max_web_bytes]
    return ToolResult(
        content=text,
        data={"url": url, "truncated": truncated},
    )


def _web_search(params: dict, context: ToolContext) -> ToolResult:
    if not context.settings.sandbox_allow_network:
        raise ToolError("WebSearch is unavailable because sandbox network access is disabled.")
    query = params["query"]
    url = "https://html.duckduckgo.com/html/?q=%s" % quote_plus(query)
    req = request.Request(
        url,
        headers={"User-Agent": "EcologyHarness/0.1"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=context.settings.command_timeout_sec) as response:
            html = response.read(context.settings.max_web_bytes).decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raise ToolError("WebSearch HTTP error %s for query %s" % (exc.code, query)) from exc
    except error.URLError as exc:
        raise ToolError("WebSearch connection error for query %s: %s" % (query, exc)) from exc

    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    results = []
    for match in pattern.finditer(html):
        title = re.sub(r"<.*?>", "", match.group("title"))
        href = unescape(match.group("href"))
        title = unescape(title).strip()
        if not title:
            continue
        results.append({"title": title, "url": href})
        if len(results) >= 5:
            break

    if not results:
        return ToolResult(content="No search results found.", data={"results": []})
    lines = ["%s\n%s" % (item["title"], item["url"]) for item in results]
    return ToolResult(content="\n\n".join(lines), data={"query": query, "results": results})
