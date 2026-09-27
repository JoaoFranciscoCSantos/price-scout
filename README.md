# price-scout

Ferramenta em Python para seguir o preço de um item em vários sites e identificar onde está mais barato. Guarda o histórico completo de preços para permitir ver tendências ao longo do tempo. Projeto pensado para, no futuro, ser integrado na [wishlist-app](../wishlist-app).

## Objetivo

Dado um item que existe em vários sites (ex: uma peça de hardware, um produto de retalho), o `price-scout`:

1. Vai a cada site onde o item está listado
2. Obtém o preço atual (via scraping ou API oficial, conforme o site)
3. Guarda esse preço na base de dados, com timestamp
4. No final, mostra um resumo com o site mais barato para cada item

## Arquitetura (planeada)

```
price-scout/
├── main.py              # ponto de entrada — corre o tracker manualmente
├── scraper.py           # lógica de scraping genérica
├── api_clients.py       # clientes para APIs oficiais de sites que as tenham
├── sites/               # um parser por site (get_price(url) -> float)
│   └── __init__.py
├── models.py            # classes Item, PriceEntry
├── database.py          # SQLite — tabelas items e price_history
├── items.json           # configuração: items a seguir e os sites/URLs de cada um
├── requirements.txt
└── README.md
```

## Decisões de design

- **Stack:** Python, SQLite (sem ORM) — mesmo stack da wishlist-app
- **Obtenção de preços:** mistura de web scraping e APIs oficiais, escolhido por site
- **Execução:** manual, via `python main.py` (sem agendamento automático, por agora)
- **Histórico:** guarda todas as leituras de preço ao longo do tempo (tabela `price_history`), não só o valor mais recente
- **Configuração de items:** ficheiro `items.json`, editável à mão; um comando `--add` no terminal poderá ser adicionado mais tarde sem mudar este formato

## Estado atual

Projeto em fase de scaffolding — ainda sem código funcional. Próximo passo: modelo de dados (`models.py` + `database.py`).

## Roadmap futuro

- Integração com a wishlist-app como módulo de acompanhamento de preços