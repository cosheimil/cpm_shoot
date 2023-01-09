# Олимпиада ЦПМ - тир 2022 (старшая категория)

<object data="https://mosrobotics.ru/wp-content/uploads/2022/10/старшая-2_Тир_зрение.pdf" type="application/pdf" width="700px" height="700px">
    <embed src="https://mosrobotics.ru/wp-content/uploads/2022/10/старшая-2_Тир_зрение.pdf">
        <p>This browser does not support PDFs. Please download the PDF to view it: <a href="https://mosrobotics.ru/wp-content/uploads/2022/10/старшая-2_Тир_зрение.pdf">Download PDF</a>.</p>
    </embed>
</object>

## TODOs
- [ ] убрать рыбий глаз
- [ ] определять синий
- [ ] определять центры кругов
- [ ] map для сервы по y, степпер по x
- [ ] улучшить движение(двигаться не прямоугольно, а сглаживать углы)
- [x] сделать робота)
- [ ] уменьшить кадр
- [ ] выполнить олимпиаду на сотку

## Робот

### Алгоритм

- определяем расстояние до крестика
- определяем синие кружочки
- определяем маршрут, переводим его в две угловые скорости
- двигаемся и стреляем

### Конструкция

- робот 250x250x250
- две сервы

#### Поподробнее про алгоритм движения и движения

- Двигаться необходимо по <img src="https://latex.codecogs.com/gif.latex?\text { arctg(h / x) } " />
- Также надо стрелять по кружочкам ближним к крестику
