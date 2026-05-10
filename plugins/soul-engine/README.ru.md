🇬🇧 [English](README.md) | 🇷🇺 [Русский](README.ru.md)

# Human Design MCP-сервер

Первый полнофункциональный калькулятор Human Design для AI-ассистентов.

Рассчитывай рейв-карты, транзиты и совместимость - прямо из Claude, Cursor, Windsurf или любого MCP-совместимого клиента.

## Возможности

| Возможность | Статус |
|---|---|
| Тип, Профиль, Авторитет, Стратегия | ✅ |
| Все 36 каналов с привязкой к контурам | ✅ |
| Все 64 ворот с линиями | ✅ |
| 9 центров (определенные/открытые) | ✅ |
| Инкарнационный Крест (угол + название) | ✅ |
| Переменные (4 стрелки: Цвет/Тон/База) | ✅ |
| Тип определенности (Единое/Расщепленное/Тройное/Четверное) | ✅ |
| Наложение транзитов на натальную карту | ✅ |
| Композитная карта (совместимость) | ✅ |
| Электромагнитные/Доминантные/Компромиссные каналы | ✅ |
| Автоопределение часового пояса по городу (историческая точность) | ✅ |
| Двуязычный вывод (английский + русский) | ✅ |

## Быстрый старт

### Установка

```bash
git clone https://github.com/artvitu/human-design-mcp.git
cd human-design-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Настройка Claude Desktop

Добавь в `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "human-design": {
      "command": "/абсолютный/путь/к/human-design-mcp/.venv/bin/python",
      "args": ["-m", "server"]
    }
  }
}
```

### Настройка Cursor / VS Code

Добавь в `.cursor/mcp.json` или аналогичный файл:

```json
{
  "mcpServers": {
    "human-design": {
      "command": "/абсолютный/путь/к/human-design-mcp/.venv/bin/python",
      "args": ["-m", "server"]
    }
  }
}
```

### Настройка Antigravity (Gemini Code Assist)

Добавь в конфигурацию MCP:

```json
{
  "mcpServers": {
    "human-design": {
      "command": "/абсолютный/путь/к/human-design-mcp/.venv/bin/python",
      "args": ["server.py"]
    }
  }
}
```

## Инструменты

### `calculate_chart`

Полный расчет рейв-карты Human Design (бодиграф).

```python
calculate_chart(
    birth_year=1990,
    birth_month=3,
    birth_day=15,
    birth_hour=14,
    birth_minute=30,
    birth_place="Москва"  # Автоопределение часового пояса!
)
```

**Возвращает:** тип, профиль, авторитет, стратегия, сигнатура, тема "ложного я", определенные/открытые центры, активные каналы, ворота с линиями/цветом/тоном/базой, инкарнационный крест, переменные (4 стрелки), тип определенности.

### `get_transits`

Расчет текущих (или на заданную дату) транзитных позиций. Опциональное наложение на натальную карту показывает временно активированные каналы.

```python
get_transits(
    birth_year=1990, birth_month=3, birth_day=15,
    birth_hour=14, birth_minute=30, birth_place="Москва"
)
```

### `compare_charts`

Композитная карта и анализ совместимости двух людей.

```python
compare_charts(
    person1_year=1990, person1_month=3, person1_day=15,
    person1_hour=14, person1_minute=30, person1_place="Москва",
    person2_year=1992, person2_month=7, person2_day=22,
    person2_hour=9, person2_minute=0, person2_place="Нью-Йорк",
    person1_name="Алиса", person2_name="Борис"
)
```

**Возвращает:** тип/профиль/авторитет каждого человека, электромагнитные каналы (притяжение), доминантные каналы, компромиссные каналы, композитный тип, оценку химии.

## Часовые пояса

Сервер автоматически определяет **исторически корректные** часовые пояса по базе IANA.

Это важно! Например:
- **Киров** - UTC+4 до октября 2014, затем UTC+3
- **Самара** - UTC+4, стала UTC+3 в 2010, вернулась к UTC+4 в 2014

При указании `birth_place="Киров"` с датой рождения 1979 года сервер корректно определит UTC+4.

Можно также передать `utc_offset=4.0` явно, если знаешь точное смещение.

## Архитектура

Python-порт логики [SharpAstrology.HumanDesign](https://github.com/CReizner/SharpAstrology.HumanDesign) (MIT), использует:

- **[pyswisseph](https://github.com/astrorigin/pyswisseph)** - привязки Swiss Ephemeris для точных астрономических вычислений
- **[fastmcp](https://github.com/jlowin/fastmcp)** - реализация протокола MCP
- **[timezonefinder](https://github.com/jannikmi/timezonefinder)** - офлайн-определение часового пояса по координатам

## Верификация

Расчеты проверены по [humdes.com](https://humdes.com) - ведущему русскоязычному калькулятору Human Design.

## Запуск тестов

```bash
source .venv/bin/activate
python tests/test_chart.py
```

## Лицензия

MIT - свободное использование в любых целях, коммерческих и личных.

## Автор

Разработал Артём Устюжанин ([@artvitu](https://github.com/artvitu)).
