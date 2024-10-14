# Translation

2024-10-14

## Translation by string key

gettext, Qt translation

The english strings in the source code become keys for the translation system
to look up the string in a different language.

```python
german = {
    "English message": "Deutsche Nachricht"
}

def _(key: str):
    return german[key]

print(_("English message"))
raise Exception(_("English message"))
```

This approach requires tools to collect all english strings from source code
and files to provide the translation dictionaries. The tools must update the translation catalogs
incrementally and detect key changes.

Python does not collect the strings in a global dictionary, because the function call
happens at runtime only. Testing with full coverage could collect all strings.

- No autocompletion or static validation of string keys

For large language dictionaries, many languages, and many translators, the tools help with management.
For a small project and only one or two languages, the tools overcomplicate things.

## Translation by message catalog

The program uses message objects in place of normal strings. These message objects
have the strings in every language.

```python
class Message(Exception):
    english = "English message"
    german = "Deutsche Nachricht"
    
    def __str__(self):
        return self.german

print(Message())
raise Message()
```

- Autocompletion and static validation will inform about missing or surplus message objects
- No build step or external tools
- Suitable for small projects with few translations
- Ability to add long help texts without affecting the readability of the source code
- Python checks for completeness at import time

## Re-translation

```python
from PySide6.QtWidgets import QPushButton

german = {
    "Cancel": "Abbrechen"
}

window = [QPushButton("Cancel")]

for widget in window:
    widget.setText(german[widget.text()])
```

For dynamic re-translation, it should keep the string keys in a cache.

It searches all strings keys once during initialization.
Therefore, Python can create and check the catalog without extra tool.

- No autocompletion or static validation of string keys
- Suitable for the short labels in the GUI
- Message objects for long error messages or help text
- Works with objects organized in a static tree and initialized once at the beginning
- Does not work for exceptions (initialized dynamically)
