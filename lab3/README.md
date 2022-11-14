## Лабораторная №3

Метод устранения левой рекурсии и метода Блюма-Коха

### Установка
Необходимо установить [graphviz](https://graphviz.org/download/). Он используется для отрисовки автоматов в графы.
```bash
git clone https://github.com/boomb0om/FormalLanguageTheory
cd FormalLanguageTheory/lab3
pip install -r requirements
```
### Запуск
Запустить лабу на тесте (по-умолчанию используется алгоритм устранения левой рекурсии):
```python
python main.py < tests/gnf.txt
```
Возможные параметры:
1. `--debug` - вывод промежуточных действий
2. `--blum-coh` - использовать алгоритм Блюма-Коха
3. `--graphs` - сохранять графы автоматов (работает только с алгоритмом Блюма-Коха)