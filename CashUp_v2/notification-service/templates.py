from jinja2 import Template

TEMPLATES = {
    "order.created": Template("订单创建: {{symbol}} {{side}} 数量 {{quantity}}"),
    "order.filled": Template("订单成交: {{symbol}} {{side}} 数量 {{quantity}}"),
    "news.published": Template("新闻: {{title}} 相关: {{symbols|join(', ')}}"),
    "risk.alert": Template("风险预警: {{details}}"),
}

def render(routing_key: str, data: dict) -> tuple[str, str]:
    t = TEMPLATES.get(routing_key)
    if not t:
        return routing_key, str(data)
    title = routing_key
    content = t.render(**data)
    return title, content