<div align="center">

# SurveEngine — Source Code Documentation

### Архитектура и техническое описание исходного кода движка

<br>

<a href="#">
  <img src="https://img.shields.io/badge/Language-Python%203.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
</a>
<a href="#">
  <img src="https://img.shields.io/badge/Architecture-Software%20Renderer-blue?style=for-the-badge" alt="Software Renderer">
</a>
<a href="#">
  <img src="https://img.shields.io/badge/API-Standard%20Library-lightgrey?style=for-the-badge" alt="Stdlib Only">
</a>

</div>

---

## Обзор архитектуры

Исходный код SurveEngine разделён на четыре изолированных модуля, каждый из которых отвечает за свою часть пайплайна. Связь между модулями осуществляется через передачу объектов (например, `GameMap` передаётся в `Renderer` и `Player`).

```text
       [ game.py ]
      /     |     \
     /      |      \
[ map.py ] [player.py] [ render.py ]
