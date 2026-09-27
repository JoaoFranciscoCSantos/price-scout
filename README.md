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

## Como correr

```bash
pip install -r requirements.txt
python main.py
```

Isto lê o `items.json`, verifica o preço de cada item em cada site configurado,
grava o resultado no histórico (`price_scout.db`, criado automaticamente) e
mostra no terminal o site mais barato para cada item.

## Configurar os teus próprios items

Edita o `items.json` e substitui os exemplos pelos teus items reais. Para cada
site com `"type": "scraper"`, precisas de indicar o `price_selector`: o
seletor CSS do elemento onde o preço aparece na página. Para o encontrar:

1. Abre a página do produto no browser
2. Inspeciona o elemento com o preço (botão direito → Inspecionar)
3. Usa a classe ou id desse elemento como seletor (ex: `.price-current`, `#product-price`)

## Estado atual

Funcional de ponta a ponta com parsers de scraping genérico. Ainda por fazer:
suporte a sites com API oficial, e testar seletores CSS contra sites reais.

## Roadmap futuro

- Integração com a wishlist-app como módulo de acompanhamento de preços