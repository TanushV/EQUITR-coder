from typing import Type

from ddgs import DDGS
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class SearchArgs(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(
        default=5, description="Maximum number of results to return"
    )


class WebSearch(Tool):
    def get_name(self) -> str:
        return "web_search"

    def get_description(self) -> str:
        return "Search the web using DuckDuckGo"

    def get_args_schema(self) -> Type[BaseModel]:
        return SearchArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            with DDGS() as ddgs:
                results = list(
                    ddgs.text(
                        args.query,
                        max_results=min(args.max_results, 10),  # Limit to 10 max
                    )
                )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "query": args.query,
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))
