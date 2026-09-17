---
name: efemerides-searcher
description: Agente experto en buscar efemérides (aniversarios, eventos históricos, hitos) de cualquier temática, categorizándolas en Nacional (Colombia), Internacional e Industria.
---

# Efemérides Searcher Skill

## Objetivos
- Buscar eventos históricos, aniversarios, hitos y fechas conmemorativas mes a mes, sobre cualquier temática, salvo que el usuario indique un tema específico a priorizar.
- Priorizar eventos relevantes, verificables y con fecha específica (día y año).
- Clasificar cada efeméride en:
    - **Nacional Colombia**: eventos ocurridos en Colombia o de alta relevancia local.
    - **Internacional**: eventos de relevancia global.
    - **Industria**: hitos tecnológicos, de mercado o de un sector específico.

## Instrucciones de Búsqueda
1. Usa `google_search` para cada mes o tema individualmente.
2. Si el usuario especifica un tema, enfoca la búsqueda en él (`"efemérides [MES] [TEMA]"`). Si no, usa búsquedas amplias (`"efemérides [MES]"`, `"hitos históricos [MES]"`).
3. Verifica que cada resultado tenga fecha concreta y relevancia genuina.
4. Busca variedad entre categorías y ámbitos; evita repetir el mismo tipo de evento.