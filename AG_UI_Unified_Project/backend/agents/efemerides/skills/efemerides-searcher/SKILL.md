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
1. Usa `google_search` para cada categoría y mes individualmente.
2. **Determinación del Mes / Temporalidad**:
   - Si el usuario dice "este mes", "del mes", "mes actual", "fechas importantes" o no menciona un mes específico, SIEMPRE debes buscar y resolver para el **mes actual en curso** según la fecha del sistema.
   - Si el usuario menciona un mes específico (ej: "marzo", "octubre"), enfoca la búsqueda en dicho mes.
3. **Consultas de Búsqueda**:
   - Si el usuario especifica un tema, enfoca la búsqueda en él (`"efemérides [MES] [TEMA]"` o `"fechas conmemorativas [MES] [TEMA] Colombia / Internacional"`).
   - Si no, usa búsquedas dirigidas como `"efemérides [MES] Colombia"`, `"efemérides internacionales [MES]"`, `"hitos históricos tecnología [MES]"`.
4. Verifica que cada resultado tenga fecha concreta (día y mes) y relevancia genuina.
5. Busca variedad entre categorías (Nacional Colombia, Internacional, Industria) y ámbitos; evita repetir el mismo tipo de evento.