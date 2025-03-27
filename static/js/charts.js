document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("habitModal");
    const habitNameInput = document.getElementById("habitName");
    const habitList = document.querySelector(".habit-container");
    const ctx = document.getElementById("habitChart").getContext("2d");

    // Пример списка привычек
    const habits = [
        { name: "Утренняя зарядка", completed: false },
        { name: "Чтение 30 минут", completed: false },
        { name: "Пить 2 литра воды", completed: false }
    ];

    // Функция рендеринга списка привычек
    function renderHabits() {
        habitList.innerHTML = "";
        habits.forEach((habit, index) => {
            const habitItem = document.createElement("div");
            habitItem.classList.add("habit-item");
            habitItem.innerHTML = `
                <input type="checkbox" id="habit-${index}" ${habit.completed ? "checked" : ""}>
                <label for="habit-${index}">${habit.name}</label>
                <button class="toggle-fail" data-index="${index}" ${habit.completed ? "style='display: none;'" : ""}>❌</button>
            `;

            const checkbox = habitItem.querySelector("input");
            const failButton = habitItem.querySelector(".toggle-fail");

            checkbox.addEventListener("change", function () {
                habits[index].completed = this.checked;
                failButton.style.display = this.checked ? "none" : "inline-block";
                updateChart();
            });

            failButton.addEventListener("click", function () {
                habits[index].completed = false;
                updateChart();
                renderHabits();
            });

            habitList.appendChild(habitItem);
        });
    }

    // Добавление новой привычки
    window.addHabit = function () {
        const habitName = habitNameInput.value.trim();
        if (habitName) {
            habits.push({ name: habitName, completed: false });
            habitNameInput.value = "";
            closeModal();
            renderHabits();
        }
    };

    // Открытие/закрытие модального окна
    window.openModal = function () {
        modal.style.display = "block";
    };

    window.closeModal = function () {
        modal.style.display = "none";
    };

    window.onclick = function (event) {
        if (event.target === modal) {
            closeModal();
        }
    };

    // Данные для графика с выполненными и невыполненными привычками
    const habitData = {
        labels: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        datasets: [
            {
                label: "Выполненные привычки",
                data: [3, 5, 2, 6, 4, 5, 0],
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 1
            },
            {
                label: "Невыполненные привычки",
                data: [2, 3, 4, 2, 5, 3, 0],
                backgroundColor: "rgba(255, 99, 132, 0.2)",
                borderColor: "rgba(255, 99, 132, 1)",
                borderWidth: 1
            }
        ]
    };

    const habitChart = new Chart(ctx, {
        type: "bar",
        data: habitData,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    function updateChart() {
        const completedCount = habits.filter(h => h.completed).length;
        const failedCount = habits.length - completedCount;
        habitChart.data.datasets[0].data[6] = completedCount;
        habitChart.data.datasets[1].data[6] = failedCount;
        habitChart.update();
    }

    // Инициализация
    renderHabits();
});
