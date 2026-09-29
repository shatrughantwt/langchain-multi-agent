from src.tools.tools import web_search

result = web_search.invoke({
    "query": "latest AI developments"
})

print(result)