// main_page.js
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация переменных
    let selectedWeekdays = [];
    let currentCategoryId = null;

    // Элементы модального окна
    const modal = document.getElementById('category-modal');
    const openBtn = document.getElementById('open-category-modal');
    const closeBtn = document.getElementById('close-category-modal');

    // Показать модальное окно
    openBtn.addEventListener('click', function() {
        modal.style.display = 'flex';
        setTimeout(() => {
            modal.classList.add('show');
            document.getElementById('category-options-container').classList.add('show');
        }, 10);
    });

    // Закрыть модальное окно
    function closeModal() {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }

    closeBtn.addEventListener('click', closeModal);

    // Обработка выбора категории
    const categoryOptions = document.querySelectorAll('.category-option');
    categoryOptions.forEach(option => {
        option.addEventListener('click', function() {
            categoryOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            currentCategoryId = this.getAttribute('data-id');

            // Показываем контейнер с привычками
            document.getElementById('habit-list-container').classList.add('show');
            document.getElementById('category-options-container').classList.remove('show');

            // Загружаем привычки для выбранной категории
            loadHabitsForCategory(currentCategoryId);
        });
    });

    // Назад к категориям
    document.getElementById('back-to-categories').addEventListener('click', function() {
        document.getElementById('habit-list-container').classList.remove('show');
        document.getElementById('category-options-container').classList.add('show');
    });

    // Инициализация календаря недели
    setupWeekCalendar();

    // Функция загрузки привычек
    function loadHabitsForCategory(categoryId) {
        fetch(`/api/habits/category/${categoryId}/`)
            .then(response => response.json())
            .then(data => {
                const habitList = document.querySelector('#habit-list-container .habit-list');
                habitList.innerHTML = '';

                if (data.habits && data.habits.length > 0) {
                    data.habits.forEach(habit => {
                        const li = document.createElement('li');
                        li.className = 'habit-item';
                        li.innerHTML = `
                            <div class="habit-name">${habit.name}</div>
                            ${habit.description ? `<div class="habit-description">${habit.description}</div>` : ''}
                            <div class="habit-actions-modal">
                                <button class="btn btn-add add-existing-habit-btn" data-id="${habit.id}">
                                    <i class="fas fa-plus"></i> Добавить
                                </button>
                            </div>
                        `;
                        habitList.appendChild(li);
                    });
                } else {
                    habitList.innerHTML = '<li class="no-habits">Нет привычек в этой категории</li>';
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки привычек:', error);
            });
    }

    // Обработчик для кнопок "Добавить"
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-existing-habit-btn') ||
            e.target.closest('.add-existing-habit-btn')) {
            const btn = e.target.classList.contains('add-existing-habit-btn')
                ? e.target
                : e.target.closest('.add-existing-habit-btn');
            const habitId = btn.getAttribute('data-id');
            addExistingHabit(habitId);
        }
    });

    // Функция добавления привычки
    function addExistingHabit(habitId) {
        if (selectedWeekdays.length === 0) {
            alert('Выберите хотя бы один день недели!');
            return;
        }

        const dates = getDatesForSelectedWeekdays();

        fetch(`/api/habits/add-template/${habitId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                dates: dates,
                category_id: currentCategoryId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Привычка успешно добавлена!');
                closeModal();
                window.location.reload();
            } else {
                throw new Error(data.message || 'Ошибка при добавлении привычки');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка: ' + error.message);
        });
    }

    // Календарь недели
    function setupWeekCalendar() {
        const days = document.querySelectorAll('.week-days .day');

        days.forEach(day => {
            day.addEventListener('click', function() {
                this.classList.toggle('selected');
                const weekday = this.dataset.weekday;

                if (this.classList.contains('selected')) {
                    if (!selectedWeekdays.includes(weekday)) {
                        selectedWeekdays.push(weekday);
                    }
                } else {
                    selectedWeekdays = selectedWeekdays.filter(d => d !== weekday);
                }

                updateSelectedDaysText();
            });
        });
    }

    function updateSelectedDaysText() {
        const daysMap = {
            '0': 'Вс', '1': 'Пн', '2': 'Вт', '3': 'Ср',
            '4': 'Чт', '5': 'Пт', '6': 'Сб'
        };

        const selectedText = selectedWeekdays.length > 0
            ? selectedWeekdays.map(d => daysMap[d]).join(', ')
            : 'не выбраны';

        document.getElementById('selected-days-text').textContent = selectedText;
    }

    function getDatesForSelectedWeekdays() {
        const today = new Date();
        const dates = [];

        // Добавляем даты на 4 недели вперед
        for (let i = 0; i < 28; i++) {
            const date = new Date();
            date.setDate(today.getDate() + i);

            if (selectedWeekdays.includes(date.getDay().toString())) {
                dates.push(date.toISOString().split('T')[0]);
            }
        }

        return dates;
    }

    // Функция для получения CSRF токена
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }
});
function addExistingHabit(habitId) {
    if (selectedWeekdays.length === 0) {
        alert('Выберите хотя бы один день недели!');
        return;
    }

    const dates = getDatesForSelectedWeekdays();

    fetch(`/api/habits/add-template/${habitId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            dates: dates,
            category_id: currentCategoryId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Привычка успешно добавлена!');
            closeModal();
            // Обновляем календарь на другой странице
            if (window.opener) {
                window.opener.refreshCalendar();
            }
            window.location.reload();
        } else {
            throw new Error(data.message || 'Ошибка при добавлении привычки');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка: ' + error.message);
    });
}