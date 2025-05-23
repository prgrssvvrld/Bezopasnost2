document.addEventListener('DOMContentLoaded', function() {
    addCompletionHandlers();
    // Инициализация текущей даты
    const today = new Date();
    let currentDate = new Date();
    let selectedDate = new Date();
    let currentSelectedDay = (today.getDay() + 6) % 7;


    // Цвета для привычек
    const habitColors = [
        { name: 'Красный', value: 'bg-red-100 text-red-800' },
        { name: 'Синий', value: 'bg-blue-100 text-blue-800' },
        { name: 'Зелёный', value: 'bg-green-100 text-green-800' },
        { name: 'Жёлтый', value: 'bg-yellow-100 text-yellow-800' },
        { name: 'Фиолетовый', value: 'bg-purple-100 text-purple-800' },
        { name: 'Розовый', value: 'bg-pink-100 text-pink-800' },
    ];

    // Функция для получения CSRF-токена из cookies
function getCSRFToken() {
    const csrfToken = document.cookie.match(/csrftoken=([\w-]+)/);
    return csrfToken ? csrfToken[1] : null;
}

 // Функция для отображения уведомления
    function showNotification(message) {
    const notification = document.createElement('div');
    notification.classList.add(
        'fixed', 'top-24', 'right-4',  // Смещение вниз под аватаркой
        'text-white', 'p-4', 'rounded-lg', 'shadow-lg',
        'transition', 'opacity-0', 'z-50'
    );
    notification.style.backgroundColor = '#b84300'; // Чуть темнее цвет

    notification.innerHTML = `<p>${message}</p>`;
    document.body.appendChild(notification);

    // Плавное появление уведомления
    setTimeout(() => notification.classList.remove('opacity-0'), 100);

    // Автоматическое скрытие через 3 секунды
    setTimeout(() => {
        notification.classList.add('opacity-0');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}


    // Функция для отображения календаря
    function renderCalendar() {
        const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
        const calendar = document.getElementById('week-calendar');
        calendar.innerHTML = '';

        // Получаем понедельник текущей недели
        const monday = new Date(currentDate);
        const adjustedDay = (currentDate.getDay() + 6) % 7;
        monday.setDate(currentDate.getDate() - adjustedDay);

        // Создаем дни недели
        for (let i = 0; i < 7; i++) {
            const day = new Date(monday);
            day.setDate(monday.getDate() + i);

            const dayElement = document.createElement('div');
            dayElement.className = `flex flex-col items-center p-2 rounded-lg cursor-pointer transition ${isSameDay(day, selectedDate) ? 'bg-[rgba(255,107,0,0.1)] text-[rgba(255,107,0,1)]' : 'hover:bg-gray-100'}`;
            dayElement.onclick = () => {
                selectedDate = new Date(day);  // ✅ сохраняем выбранную дату
                currentSelectedDay = (day.getDay() + 6) % 7;  // ✅ используем выбранный день недели
                renderCalendar(); // перерисовываем календарь, чтобы выделить выбранный день
            };

            dayElement.innerHTML = `
                <div class="relative w-full">
                    <span class="day-label text-sm font-medium">${weekDays[i]}</span>
                    <span class="indicator absolute top-1 right-1 w-3 h-3 rounded-full bg-[#FF6B00] opacity-0 transition-opacity"></span>
                </div>
                <div class="text-lg ${isSameDay(day, today) ? 'font-bold text-[#FF6B00]' : ''}">${day.getDate()}</div>
            `;

            calendar.appendChild(dayElement);
        }

        // Обновляем список привычек для выбранного дня
        updateHabitsList();
    }
    //показ точки рядом с днем недели при добавлении или обновлении привычки
    function showIndicatorForDay(weekdayIndex) {
    const calendar = document.getElementById('week-calendar');
    // Получаем все дни недели (div-элементы внутри календаря)
    const days = calendar.children;

    if (weekdayIndex < 0 || weekdayIndex > 6) return;

    // В каждом дне ищем элемент .indicator и меняем opacity
    const indicator = days[weekdayIndex].querySelector('.indicator');
    if (!indicator) return;

    // Показываем точку
    indicator.style.opacity = '1';

    // Через 3 секунды скрываем
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 3000);
}

    // Функция выбора даты
    function selectDate(date) {
        selectedDate = date;
        renderCalendar();
    }

    // Функция проверки совпадения дат
    function isSameDay(d1, d2) {
        return d1.getDate() === d2.getDate() &&
               d1.getMonth() === d2.getMonth() &&
               d1.getFullYear() === d2.getFullYear();
    }

    // Функция обновления списка привычек
 function updateHabitsList() {
    const habitsList = document.getElementById('habits-list');
     const dayOfWeek = (selectedDate.getDay() + 6) % 7;
     const selectedDateStr = selectedDate.toISOString().slice(0, 10);  // YYYY-MM-DD

        fetch(`/habits/get_by_day/?day=${dayOfWeek}&date=${selectedDateStr}`)

        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.habits.length === 0) {
                    habitsList.innerHTML = `
                        <div class="text-center py-8 text-gray-500">
                            <p>На этот день нет запланированных привычек</p>
                        </div>
                    `;
                } else {
                    habitsList.innerHTML = '';
                    data.habits.forEach(habit => {
    habitsList.appendChild(createHabitElement(habit, false, true, selectedDateStr));
});


                    // Добавляем обработчики событий для новых элементов
                    addCompletionHandlers();

                }
            }

        })
        .catch(error => {
            console.error('Error:', error);
        });

}

// Добавьте эту новую функцию для обработки кнопок выполнения:
function addCompletionHandlers() {
    document.querySelectorAll('.habit-completion-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const habitId = this.dataset.habitId;
            const button = this.querySelector('button');

            const dateInput = this.querySelector('input[name="date"]');
            const date = dateInput ? dateInput.value : new Date().toISOString().slice(0, 10); // fallback to today

            fetch(`/api/toggle-completion/${habitId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `date=${encodeURIComponent(date)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.completed !== undefined) {
                    button.textContent = data.completed ? '✓ Выполнено' : 'Отметить';
                    button.className = data.completed ?
                        'bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full transition' :
                        'bg-gray-100 text-gray-800 text-xs px-3 py-1 rounded-full transition';
                    const progressBar = form.closest('.flex-col').querySelector('.progress-bar-fill');
                    const progressText = form.closest('.flex-col').querySelector('.progress-text');

                    if (progressText && progressBar) {
                        progressText.textContent = `Прогресс: ${data.completion_rate}%`;
                        progressBar.style.width = `${data.completion_rate}%`;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Ошибка отметки выполнения', 'error');
            });
        });
    });
}



    // Функция загрузки всех привычек пользователя
    function loadAllHabits() {
    fetch('/habits/get_all/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const allHabitsList = document.getElementById('all-habits-list');
                allHabitsList.innerHTML = '';
                data.habits.forEach(habit => {
                    allHabitsList.appendChild(createHabitElement(habit, true));
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}


    // Создание элемента привычки (только категория окрашивается)
    function createHabitElement(habit, showDays = false, showCompletion = false, dateStr = null) {
    const element = document.createElement('div');
    element.className = 'p-4 hover:bg-gray-50 transition bg-white border-b';
    element.dataset.habitId = habit.id;

    const daysMap = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'};
    const activeDays = habit.schedule_days ? habit.schedule_days.map(day => daysMap[day]) : [];

    // Кнопки действий (удалить и изменить)
    const actionButtons = `
        <div class="flex items-center space-x-2">
            <button class="edit-habit text-gray-400 hover:text-indigo-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                </svg>
            </button>
            <button class="delete-habit text-gray-400 hover:text-red-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
            </button>
        </div>
    `;

    // Кнопка выполнения (только если showCompletion=true)
    const today = new Date();
const selectedDateObj = new Date(selectedDate); // selectedDate должен быть в области видимости!

const isFutureDate = selectedDateObj > today;

const completionSection = showCompletion ? `
    <div class="flex flex-col items-end">
        <form class="habit-completion-form" data-habit-id="${habit.id}">
            <input type="hidden" name="date" value="${dateStr}">
            <button type="submit" class="${
                habit.is_completed_today ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            } text-xs px-3 py-1 rounded-full transition"
            ${isFutureDate ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                ${habit.is_completed_today ? '✓ Выполнено' : 'Отметить'}
        </button>
    </form>
    <div class="mt-2 text-xs text-gray-500 progress-text">
        Прогресс: ${habit.completion_rate || 0}%
    </div>
    <div class="w-20 h-1 bg-gray-200 rounded-full mt-1 progress-bar">
        <div class="h-1 bg-indigo-600 rounded-full progress-bar-fill" style="width: ${habit.completion_rate || 0}%"></div>
    </div>
</div>
` : '';



    const rightSection = `
    <div class="flex flex-col items-end space-y-2">
        ${completionSection}
        ${actionButtons}
    </div>
`;

    const daysInfo = showDays && activeDays.length > 0 ? `
        <div class="mt-1 text-xs text-gray-500">Дни: ${activeDays.join(', ')}</div>
    ` : '';

    element.innerHTML = `
    <div class="flex justify-between items-start">
        <div>
            <div class="flex items-center space-x-2">
                <span class="${habit.color_class} text-xs font-medium px-2.5 py-0.5 rounded-full">
                    ${habit.category_display || habit.category}
                </span>
                ${habit.reminder && habit.reminder_time ? `
                <span class="text-xs text-gray-500">
                    ⏰ ${habit.reminder_time}
                </span>
                ` : ''}
            </div>
            <h3 class="font-medium mt-1">${habit.name}</h3>
            ${habit.description ? `<p class="text-sm text-gray-600 mt-1">${habit.description}</p>` : ''}
            ${daysInfo}
        </div>
        ${rightSection}
    </div>
    <div class="flex justify-between items-center mt-3 text-xs text-gray-500">

    </div>
`;


    // Добавляем обработчики событий для кнопок
    element.querySelector('.edit-habit').addEventListener('click', () => editHabit(habit.id));
    element.querySelector('.delete-habit').addEventListener('click', () => deleteHabit(habit.id));

//    if (showCompletion) {
//    const form = element.querySelector('.habit-completion-form');
//    if (form) {
//        form.addEventListener('submit', function(e) {
//            e.preventDefault();
//            toggleHabitCompletion(habit.id, form);
//        });
//    }
//}

    return element;
}


    // Функции для модального окна
    function openModal() {
        document.getElementById('modal').classList.remove('hidden');
        renderColorOptions();
    }

    function closeModal() {
        document.getElementById('modal').classList.add('hidden');
        document.getElementById('habit-form').reset();
        document.getElementById('habit-id').value = '';
    }

    // Функция отображения вариантов цвета
    function renderColorOptions() {
        const container = document.getElementById('color-options');
        container.innerHTML = '';

        habitColors.forEach(color => {
            const colorElement = document.createElement('div');
            colorElement.className = `flex items-center space-x-2 p-2 rounded-lg cursor-pointer hover:bg-gray-100`;
            colorElement.onclick = () => selectColor(color.value);

            colorElement.innerHTML = `
                <div class="w-6 h-6 rounded-full ${color.value.split(' ')[0]}"></div>
                <span>${color.name}</span>
            `;

            container.appendChild(colorElement);
        });
    }

    // Функция выбора цвета
function selectColor(colorClass) {
    const colorInput = document.getElementById('color');
    const selectedColor = document.getElementById('selected-color');
    const container = document.getElementById('color-options'); // Контейнер с цветами

    if (!colorInput || !selectedColor || !container) {
        console.warn('Цветовой input, индикатор или контейнер с цветами не найден!');
        return;
    }

    // Устанавливаем выбранный цвет
    colorInput.value = colorClass;
    selectedColor.className = `w-6 h-6 rounded-full ${colorClass}`;

    // Закрываем список с цветами
    container.classList.add('hidden');
}



    // Генерация случайной привычки
    function generateHabit() {
        const categories = ['health', 'productivity', 'learning', 'relationships', 'finance'];
        const healthHabits = ['Пить воду', 'Утренняя зарядка', '10 000 шагов', 'Медитация'];
        const productivityHabits = ['Планирование дня', 'Уборка рабочего стола', 'Ведение дневника'];
        const developmentHabits = ['Чтение книги', 'Изучение языка', 'Просмотр курса'];
        const relationsHabits = ['Звонок родителям', 'Свидание', 'Встреча с друзьями'];
        const financeHabits = ['Учет расходов', 'Инвестирование', 'Анализ бюджета'];

        const category = categories[Math.floor(Math.random() * categories.length)];
        let habitName = '';

        switch(category) {
            case 'health': habitName = healthHabits[Math.floor(Math.random() * healthHabits.length)]; break;
            case 'productivity': habitName = productivityHabits[Math.floor(Math.random() * productivityHabits.length)]; break;
            case 'learning': habitName = developmentHabits[Math.floor(Math.random() * developmentHabits.length)]; break;
            case 'relationships': habitName = relationsHabits[Math.floor(Math.random() * relationsHabits.length)]; break;
            case 'finance': habitName = financeHabits[Math.floor(Math.random() * financeHabits.length)]; break;
        }

        document.getElementById('name').value = habitName;
        document.getElementById('category').value = category;
        document.getElementById('description').value = 'Описание моей новой привычки';
        document.getElementById('days_goal').value = Math.floor(Math.random() * 90) + 10;

        // Выбираем случайный цвет
        const randomColor = habitColors[Math.floor(Math.random() * habitColors.length)];
        selectColor(randomColor.value);
    }

    // Обработчик отправки формы
    document.getElementById('habit-form').addEventListener('submit', function(e) {
        e.preventDefault();
        saveHabit();
    });


    // Функция сохранения привычки
   // Функция сохранения привычки
function saveHabit() {
    const form = document.getElementById('habit-form');
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfTokenElement ? csrfTokenElement.value : null;

    if (!csrfToken) {
        console.warn('CSRF токен не найден!');
        return;
    }

    const habitId = document.getElementById('habit-id').value;
    const isEdit = !!habitId;

    const habitData = {
        habit_id: habitId,
        name: document.getElementById('name').value,
        category: document.getElementById('category').value,
        description: document.getElementById('description').value,
        days_goal: document.getElementById('days_goal').value,
        color_class: document.getElementById('color').value,
        schedule_days: Array.from(document.querySelectorAll('input[name="days"]:checked')).map(cb => parseInt(cb.value))
    };

    fetch('/habits/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(habitData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Привычка сохранена!', data.habit);


            // Уведомление в зависимости от типа (добавление или редактирование)
            if (isEdit) {
                showNotification('Привычка успешно отредактирована!', 'edit');
                /////нужно обновление страницв=ы
            } else {
                showNotification('Привычка успешно добавлена!', 'add');
            }

            // Обновляем UI
            if (isEdit) {
                // Удаляем старую версию привычки
                const oldHabitElements = document.querySelectorAll(`[data-habit-id="${habitId}"]`);
                oldHabitElements.forEach(el => el.remove());
            }

            // Добавляем обновленную привычку
            addHabitToAllHabitsList(data.habit);
            addHabitToSelectedDayList(data.habit);
            addCompletionHandlers();

            if (data.habit.schedule_days && data.habit.schedule_days.length > 0) {
                data.habit.schedule_days.forEach(dayIndex => {
                    showIndicatorForDay(dayIndex);
                });
            }

            closeModal();
        } else {
            console.error('Ошибка сохранения:', data.error);
        }
    })
    .catch(error => {
        console.error('Ошибка запроса:', error);
    });
}
    // Добавление привычки в список "Все ваши привычки"
    function addHabitToAllHabitsList(habit) {
        const allHabitsList = document.getElementById('all-habits-list');
        if (allHabitsList) {
            const habitElement = createHabitElement(habit, false, false);
            allHabitsList.appendChild(habitElement);
        }
    }

    // Добавление привычки в список "Привычки на выбранный день"
    function addHabitToSelectedDayList(habit) {
        const habitsList = document.getElementById('habits-list');
        const selectedDay = (selectedDate.getDay() + 6) % 7;


        // Проверяем, есть ли выбранный день в расписании привычки
        const hasDay = habit.schedule_days ? habit.schedule_days.includes(selectedDay) : false;

        if (habitsList && hasDay) {
            const habitElement = createHabitElement(habit, false, true);

            // Если список пустой (с сообщением "нет привычек"), очищаем его
            if (habitsList.querySelector('.text-center')) {
                habitsList.innerHTML = '';
            }

            habitsList.appendChild(habitElement);

        }

    }

    // Инициализация
    renderCalendar();
    loadAllHabits();

    // Функция для отправки состояния выполнения привычки
function toggleHabitCompletion(habitId, formElement, date = null) {
    const button = formElement.querySelector('button');
    const progressText = formElement.closest('.flex.flex-col').querySelector('.progress-text');
    const progressBar = formElement.closest('.flex.flex-col').querySelector('.progress-bar-fill');
    const selectedDate = document.getElementById('selected-date')?.value || new Date().toISOString().slice(0, 10); // YYYY-MM-DD

    button.disabled = true;
    button.textContent = '...';

    fetch(`/api/toggle-completion/${habitId}/`, {
        method: 'POST',
    headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `date=${encodeURIComponent(selectedDate)}`  // 👈 передаём дату<-- дата может быть null (сегодня) или задана вручную
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.disabled = false;
            button.textContent = data.completed ? '✓ Выполнено' : 'Отметить';
            button.className = data.completed
                ? 'bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full transition'
                : 'bg-gray-100 text-gray-800 text-xs px-3 py-1 rounded-full transition';

            if (data.completion_rate !== undefined) {
                progressText.textContent = `Прогресс: ${data.completion_rate}%`;
                progressBar.style.width = `${data.completion_rate}%`;
            }

            showNotification(data.completed ? "Привычка выполнена!" : "Привычка отменена!");
        } else {
            showNotification(data.error || 'Ошибка при отметке привычки');
            button.disabled = false;
            button.textContent = data.completed ? '✓ Выполнено' : 'Отметить';
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при отметке привычки.');
        button.disabled = false;
        button.textContent = 'Отметить';
    });
}


    // Назначение обработчиков событий
    document.getElementById('open-modal').addEventListener('click', openModal);
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('generate-habit').addEventListener('click', generateHabit);

    // Глобальные функции для кнопок
 window.editHabit = function(id) {
    console.log('Попытка редактировать привычку с ID:', id);

    fetch(`/habits/get/${id}/`)
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                const habit = data;
                console.log('Полученные данные привычки:', habit);

                // Сохраняем ID редактируемой привычки
                document.getElementById('habit-id').value = habit.id;

                // Заполнение формы данными привычки
                document.getElementById('name').value = habit.name;
                document.getElementById('category').value = habit.category;
                document.getElementById('days_goal').value = habit.days_goal;
                document.getElementById('description').value = habit.description || '';

                // Установка цвета
                if (habit.color_class) {
                    selectColor(habit.color_class);
                }

                // Установка выбранных дней
                const scheduleDays = habit.schedule_days || [];
                document.querySelectorAll('input[name="days"]').forEach(input => {
                    const span = input.nextElementSibling;
                    if (scheduleDays.includes(parseInt(input.value))) {
                        input.checked = true;
                        span.classList.add('bg-indigo-600', 'text-white');
                    } else {
                        input.checked = false;
                        span.classList.remove('bg-indigo-600', 'text-white');
                    }
                });

                // Открытие модального окна
                openModal();
            } else {
                console.error('Ошибка получения данных о привычке:', data.message || 'Неизвестная ошибка');
            }
        })
        .catch(error => {
            console.error('Ошибка при запросе данных о привычке:', error);
        });
};



    window.deleteHabit = function(id) {
    if (confirm('Вы уверены, что хотите удалить эту привычку?')) {
        fetch(`/habits/delete/${id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error('Ошибка на сервере: ' + text);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log('Привычка удалена успешно');

                const habitElement = document.querySelector(`[data-habit-id="${id}"]`);
                if (habitElement) habitElement.remove();

                // После удаления — проверяем остались ли привычки на этот день
                const habitsList = document.getElementById('habits-list');
                if (habitsList && habitsList.children.length === 0) {
                    habitsList.innerHTML = `
                        <div class="text-center py-8 text-gray-500">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p>На этот день нет запланированных привычек</p>
                        </div>
                    `;
                }

                // Также можно убрать привычку из списка "все привычки"
                const allHabitsList = document.getElementById('all-habits-list');
                const habitInAllList = allHabitsList?.querySelector(`[data-habit-id="${id}"]`);
                if (habitInAllList) habitInAllList.remove();

            } else {
                throw new Error('Ошибка при удалении привычки: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Ошибка при удалении привычки:', error);
        });
    }
    showNotification('Привычка успешно удалена!', 'success');
};

});