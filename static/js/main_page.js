document.addEventListener('DOMContentLoaded', function () {
    // Инициализация элементов
    feather.replace(); // Инициализация Feather Icons

    const openCategoryModal = document.getElementById('open-category-modal');
    const categoryModal = document.getElementById('category-modal');
    const closeCategoryModal = document.getElementById('close-category-modal');
    const categoryOptionsContainer = document.getElementById('category-options-container');
    const habitListContainer = document.getElementById('habit-list-container');
    const editHabitContainer = document.getElementById('edit-habit-container');
    const backToCategoriesButton = document.getElementById('back-to-categories');
    const backToHabitListButton = document.getElementById('back-to-habit-list');
    const habitList = document.querySelector('#habit-list-container .habit-list');
    const categoryButtons = document.querySelectorAll('.category-option');
    const editHabitForm = document.getElementById('edit-habit-form');
    const addHabitInModal = document.getElementById('add-habit-in-modal');

    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }

    let currentCategoryId = null;

    // Показать модальное окно
    openCategoryModal.addEventListener('click', () => {
        categoryModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            categoryModal.classList.add('show');
            showView(categoryOptionsContainer);
        }, 10);
    });

    // Закрыть модальное окно
    function closeModal() {
        categoryModal.classList.remove('show');
        setTimeout(() => {
            categoryModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }

    closeCategoryModal.addEventListener('click', closeModal);

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && categoryModal.style.display === 'flex') {
            closeModal();
        }
    });

    // Универсальная функция для показа view
    function showView(viewElement) {
        document.querySelectorAll('.modal-container').forEach(view => {
            view.classList.remove('show');
        });
        setTimeout(() => {
            viewElement.classList.add('show');
        }, 50);
    }

    // Обработка выбора категории
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            currentCategoryId = button.getAttribute('data-id');
            const selectedCategoryName = button.getAttribute('data-category');

            document.querySelector('#habit-list-container h3').textContent =
                `Привычки в категории "${selectedCategoryName}":`;

            showView(habitListContainer);
            loadHabitsForCategory(currentCategoryId);
        });
    });

    // Загрузка привычек категории
    function loadHabitsForCategory(categoryId) {
        fetch(`/api/habits/category/${categoryId}/`)
            .then(response => response.json())
            .then(data => {
                habitList.innerHTML = '';
                if (data.habits && data.habits.length > 0) {
                    data.habits.forEach(habit => {
                        const habitItem = document.createElement('li');
                        habitItem.classList.add('habit-item');
                        habitItem.setAttribute('data-id', habit.id);
                        habitItem.innerHTML = `
                            <div class="habit-name">${habit.name}</div>
                            ${habit.description ? `<div class="habit-description">${habit.description}</div>` : ''}
                            <div class="habit-actions-modal">
                                <button class="btn btn-edit edit-habit-btn">
                                    <i class="fas fa-edit" style="margin-right: 6px;"></i> Изменить
                                </button>
                                <button class="btn btn-add add-existing-habit-btn" data-id="${habit.id}">
                                    <i class="fas fa-plus" style="margin-right: 6px;"></i> Добавить
                                </button>

                            </div>
                        `;
                        habitList.appendChild(habitItem);
                    });

                    document.querySelectorAll('.edit-habit-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const habitItem = e.target.closest('.habit-item');
                            const habitId = habitItem.getAttribute('data-id');
                            const habitName = habitItem.querySelector('.habit-name').textContent;
                            const habitDescription = habitItem.querySelector('.habit-description')?.textContent || '';

                            document.getElementById('edit-habit-id').value = habitId;
                            document.getElementById('edit-habit-name').value = habitName;
                            document.getElementById('edit-habit-description').value = habitDescription;

                            showView(editHabitContainer);
                        });
                    });


                    document.querySelectorAll('.add-existing-habit-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const habitId = e.target.getAttribute('data-id'); // Получаем ID привычки
                            disableButton(btn); // Блокируем кнопку, чтобы избежать повторного клика
                            addExistingHabit(habitId); // Добавляем привычку
                        });
                    });

                } else {
                    habitList.innerHTML = '<li class="no-habits">Нет привычек в выбранной категории.</li>';
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки привычек:', error);
                habitList.innerHTML = '<li class="error">Произошла ошибка при загрузке привычек.</li>';
            });
    }

    // Добавление существующей привычки пользователю
    // Добавление привычки в список пользователя
function addExistingHabit(habitId) {
    const dateInput = document.getElementById('modal-date');
    const selectedDate = dateInput.value;

    fetch(`/api/habits/add-template/${habitId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            date: selectedDate // Добавляем дату в запрос
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            addHabitToUserList(data);
            closeModal();
        } else {
            alert(data.message || 'Произошла ошибка при добавлении привычки');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при добавлении привычки');
    });
}



    // Добавление привычки в список пользователя

function addHabitToUserList(habit) {
    const userHabitsContainer = document.querySelector('.user-habits');
    let userHabitList = userHabitsContainer.querySelector('.habit-list');


    let firstHabit = false;

    // Если список ещё не создан (первая привычка)
    if (!userHabitList) {
        firstHabit = true;
        userHabitList = document.createElement('ul');
        userHabitList.classList.add('habit-list');
        userHabitsContainer.appendChild(userHabitList);

        // Удалим блок с empty-state
        const emptyState = userHabitsContainer.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
    }

    const habitItem = document.createElement('li');
    habitItem.classList.add('habit-item');
    habitItem.setAttribute('data-id', habit.id);

    habitItem.innerHTML = `
        <div class="habit-name">${habit.name}</div>
        ${habit.description ? `<div class="habit-description">${habit.description}</div>` : ''}
        <div class="habit-actions">
            <a href="/habits/${habit.id}/edit/" class="btn btn-edit">
                <i class="fas fa-edit" style="margin-right: 6px;"></i> Изменить
            </a>
            <form method="post" action="/habits/${habit.id}/delete/" style="display: inline;">
                <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
                <button type="submit" class="btn btn-delete" onclick="return confirm('Вы уверены, что хотите удалить эту привычку?')">
                    <i class="fas fa-trash-alt" style="margin-right: 6px;"></i>Удалить
                </button>
            </form>
        </div>
    `;

    userHabitList.appendChild(habitItem);

    // Плавное появление
    setTimeout(() => {
        habitItem.classList.add('show');
    }, 10);

    // Если это была первая привычка, перезагрузим страницу
    if (firstHabit) {
        window.location.reload();
    }
}

    // Обработка добавления привычки вручную
    addHabitInModal.addEventListener('click', () => {
        closeModal();
        document.getElementById('open-category-modal').textContent =
            document.querySelector('#habit-list-container h3').textContent.replace('Привычки в категории "', '').replace('":', '');
        document.querySelector('#id_name').focus();
    });

    // Назад к категориям
    backToCategoriesButton.addEventListener('click', () => {
        showView(categoryOptionsContainer);
        editHabitForm.reset();
    });

    // Назад к списку привычек
    backToHabitListButton.addEventListener('click', () => {
        showView(habitListContainer);
        editHabitForm.reset();
    });


// Обработка формы редактирования
if (editHabitForm) {
editHabitForm.addEventListener('submit', function(e) {
    e.preventDefault();

    const habitId = document.getElementById('edit-habit-id').value;
    const habitName = document.getElementById('edit-habit-name').value;
    const habitDescription = document.getElementById('edit-habit-description').value;
    const habitCategory = currentCategoryId;

    console.log({
    id: habitId,
    name: habitName,
    description: habitDescription,
    category_id: habitCategory
});
    fetch(`/api/habits/save/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(), // Django CSRF
        },
        body: JSON.stringify({
            id: habitId, // 🧠 вот ключевой момент
            name: habitName,
            description: habitDescription,
            category_id: habitCategory
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload(); // или обнови DOM вручную
        } else {
            alert(data.message || 'Ошибка при добавлении привычки');
        }
    })
    .catch(error => {
        alert('Ошибка при добавлении привычки.');
        console.error(error);
    });
});
}


function disableSaveButton(button) {
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';
    setTimeout(() => {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-save" style="margin-right: 6px;"></i> Сохранить';
    }, 2000); // Время, на которое блокируем кнопку
}


if (addHabitInModal) {
    addHabitInModal.addEventListener('submit', function(e) {
        e.preventDefault();

        const habitName = document.getElementById('id_name').value;
        const habitDescription = document.getElementById('id_description').value;
        const habitDate = document.getElementById('id_date').value;

        fetch(`/api/habits/create/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                name: habitName,
                description: habitDescription,
                category_id: currentCategoryId,
                date: habitDate  // Дата
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Ошибка при добавлении привычки');
            }
        })
        .catch(error => {
            alert('Ошибка при добавлении привычки.');
            console.error(error);
        });
    });
}



    // Защита от повторного клика
    function disableButton(button) {
        button.disabled = true;
        setTimeout(() => button.disabled = false, 1000);
    }

    // Показать категории при загрузке
    showView(categoryOptionsContainer);
});
function updateMoonIcon(isDark) {
    const iconHtml = isDark
        ? feather.icons.sun.toSvg()
        : feather.icons.moon.toSvg();
    themeToggle.innerHTML = iconHtml;

    // Принудительное обновление стилей календаря
    const calendar = document.querySelector('.calendar-container');
    if (calendar) {
        if (isDark) {
            calendar.classList.add('dark-mode');
        } else {
            calendar.classList.remove('dark-mode');
        }

        // Принудительное обновление цветов
        const dayNumbers = document.querySelectorAll('.day-number');
        dayNumbers.forEach(el => {
            el.style.color = isDark ? 'white' : 'inherit';
        });
    }
}