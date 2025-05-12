// main_page.js
document.addEventListener('DOMContentLoaded', function() {
    // Состояние приложения
    const state = {
        selectedWeekdays: [],
        currentCategoryId: null,
        isSubmitting: false,
        lastSubmittedHabit: null
    };

    // Инициализация модального окна
    const modal = document.getElementById('category-modal');
    const openBtn = document.getElementById('open-category-modal');
    const closeBtn = document.getElementById('close-category-modal');

    // Показать/скрыть модальное окно
    openBtn.addEventListener('click', showModal);
    closeBtn.addEventListener('click', closeModal);

    function showModal() {
        modal.style.display = 'flex';
        setTimeout(() => {
            modal.classList.add('show');
            document.getElementById('category-options-container').classList.add('show');
            resetSelectedDays();
        }, 10);
    }

    function closeModal() {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
            resetSelectedDays();
        }, 300);
    }

    // Работа с категориями
    document.querySelectorAll('.category-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.category-option').forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            state.currentCategoryId = this.getAttribute('data-id');

            document.getElementById('habit-list-container').classList.add('show');
            document.getElementById('category-options-container').classList.remove('show');

            loadHabitsForCategory(state.currentCategoryId);
            resetSelectedDays();
        });
    });

    document.getElementById('back-to-categories').addEventListener('click', function() {
        document.getElementById('habit-list-container').classList.remove('show');
        document.getElementById('category-options-container').classList.add('show');
        resetSelectedDays();
    });

    // Календарь недели
    function setupWeekCalendar() {
        document.querySelectorAll('.week-days .day').forEach(day => {
            day.addEventListener('click', function() {
                this.classList.toggle('selected');
                const weekday = this.dataset.weekday;

                if (this.classList.contains('selected')) {
                    if (!state.selectedWeekdays.includes(weekday)) {
                        state.selectedWeekdays.push(weekday);
                    }
                } else {
                    state.selectedWeekdays = state.selectedWeekdays.filter(d => d !== weekday);
                }

                updateSelectedDaysText();
            });
        });
    }

    function resetSelectedDays() {
        state.selectedWeekdays = [];
        document.querySelectorAll('.week-days .day').forEach(day => {
            day.classList.remove('selected');
        });
        updateSelectedDaysText();
    }

    function updateSelectedDaysText() {
        const daysMap = {
            '0': 'Пн', '1': 'Вт', '2': 'Ср',
            '3': 'Чт', '4': 'Пт', '5': 'Сб', '6': 'Вс',
        };

        const selectedText = state.selectedWeekdays.length > 0
            ? state.selectedWeekdays.map(d => daysMap[d]).join(', ')
            : 'не выбраны';

        document.getElementById('selected-days-text').textContent = selectedText;
    }

    document.getElementById('add-habit-in-modal').addEventListener('click', function() {
    // Проверяем, что категория выбрана
    if (!state.currentCategoryId) {
        alert('Пожалуйста, сначала выберите категорию');
        return;
    }

    // Получаем данные о выбранной категории
    const selectedOption = document.querySelector('.category-option.active');
    if (selectedOption) {
        const categoryId = selectedOption.getAttribute('data-id');
        const categoryName = selectedOption.getAttribute('data-category');

        // Заполняем основную форму
        document.getElementById('id_category').value = categoryId;
        document.getElementById('category-text').textContent = categoryName;

        // Закрываем модальное окно
        closeModal();

        // Прокручиваем к форме (опционально)
        document.getElementById('habit-form').scrollIntoView({ behavior: 'smooth' });
    }
});

    // Загрузка привычек
    function loadHabitsForCategory(categoryId) {
        fetch(`/api/habits/category/${categoryId}/`)
            .then(response => response.json())
            .then(data => {
                const habitList = document.querySelector('#habit-list-container .habit-list');
                habitList.innerHTML = '';

                if (data.habits?.length > 0) {
                    data.habits.forEach(habit => {
                        const li = document.createElement('li');
                        li.className = 'habit-item';
                        li.innerHTML = `
                            <div class="habit-name">${habit.name}</div>
                            ${habit.description ? `<div class="habit-description">${habit.description}</div>` : ''}
                            <button class="btn btn-add add-existing-habit-btn" data-id="${habit.id}">
                                <i class="fas fa-plus"></i> Добавить
                            </button>
                        `;
                        habitList.appendChild(li);
                    });
                } else {
                    habitList.innerHTML = '<li class="no-habits">Нет привычек в этой категории</li>';
                }
            })
            .catch(console.error);
    }

    // Обработка добавления привычки
    document.getElementById('habit-list-container').addEventListener('click', function(e) {
        const btn = e.target.closest('.add-existing-habit-btn');
        if (btn && !state.isSubmitting) {
            const habitId = btn.getAttribute('data-id');

            // Проверка на повторное нажатие для той же привычки
            if (state.lastSubmittedHabit === habitId) {
                alert('Эта привычка уже добавлена. Пожалуйста, выберите другую или измените дни.');
                return;
            }

            addExistingHabit(habitId);
        }
    });

    async function addExistingHabit(habitId) {
    if (state.selectedWeekdays.length === 0) {
        alert('Выберите хотя бы один день недели!');
        return;
    }

    if (state.isSubmitting) return;
    state.isSubmitting = true;

    const btn = document.querySelector(`.add-existing-habit-btn[data-id="${habitId}"]`);
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Добавление...';

    try {
        const response = await fetch(`/api/habits/add-template/${habitId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                weekdays: state.selectedWeekdays, // Отправляем только дни недели
                category_id: state.currentCategoryId
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            closeModal();
            window.location.reload(); // Обновляем страницу
        } else {
            throw new Error(data.error || 'Ошибка при добавлении привычки');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка: ' + error.message);
    } finally {
        state.isSubmitting = false;
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-plus"></i> Добавить';
    }
}

    function getDatesForSelectedWeekdays() {
        const today = new Date();
        const dates = [];

        for (let i = 0; i < 28; i++) {
            const date = new Date(today);
            date.setDate(today.getDate() + i);

            if (state.selectedWeekdays.includes(date.getDay().toString())) {
                dates.push(date.toISOString().split('T')[0]);
            }
        }

        return dates;
    }

    function getCSRFToken() {
        return document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
    }

    // Инициализация
    setupWeekCalendar();
});