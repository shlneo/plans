// toggle password
const togglePassword = {
  init: function() {
    document.querySelectorAll('.toggle-password').forEach(button => {
      button.addEventListener('click', function() {
        const passwordInput = this.closest('.password-input-wrapper').querySelector('input');
        const eyeVisible = this.querySelector('.eye-visible');
        const eyeHidden = this.querySelector('.eye-hidden');
        
        if (passwordInput.type === 'password') {
          passwordInput.type = 'text';
          eyeVisible.style.display = 'none';
          eyeHidden.style.display = 'block';
          this.setAttribute('aria-label', 'Скрыть пароль');
        } else {
          passwordInput.type = 'password';
          eyeVisible.style.display = 'block';
          eyeHidden.style.display = 'none';
          this.setAttribute('aria-label', 'Показать пароль');
        }
      });
    });
  }
};

const messageFlash = (function() {
    const containerId = 'flash-container';
    let container;
    let messages = []; // массив всех сообщений

    function init() {
        container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = containerId;
            document.body.appendChild(container);
        }

        // Загружаем из localStorage
        messages = JSON.parse(localStorage.getItem('flashMessages') || '[]');
        renderMessages();
    }

    function _showMessage(msgObj) {
        const alertBox = document.createElement('div');
        alertBox.className = `custom-alert ${msgObj.type === 'error' ? 'alert-danger' : 'alert-success'} collapsed`;

        const imgSrc = msgObj.type === 'error'
            ? '/static/img/Error.svg'
            : '/static/img/No_error.svg';

        alertBox.innerHTML = `
            <img src="${imgSrc}" class="alert-icon" alt="">
            <div class="p_message_cont">
                <p>${msgObj.msg}</p>
            </div>
            <button class="alert-close">&times;</button>
        `;

        

        alertBox.querySelector('.alert-close').addEventListener('click', e => {
            e.stopPropagation();

            // Добавляем класс для анимации исчезновения
            alertBox.classList.add('removing');

            // Удаляем из DOM после окончания анимации (300ms)
            setTimeout(() => {
                container.removeChild(alertBox);
                messages = messages.filter(m => m.msg !== msgObj.msg);
                localStorage.setItem('flashMessages', JSON.stringify(messages));
                renderMessages();
            }, 300); // совпадает с transition в CSS
        });
        // разворачивание при клике на последний
        alertBox.addEventListener('click', () => {
            container.querySelectorAll('.custom-alert').forEach((el, index) => {
                if (index === container.children.length - 1) {
                    el.classList.toggle('expanded');
                    el.classList.toggle('collapsed');
                } else {
                    el.classList.remove('expanded');
                    el.classList.add('collapsed');
                }
            });
        });

        container.appendChild(alertBox);
    }

    function addMessage(msg, type='success') {
        const msgObj = { msg, type };
        messages.push(msgObj);
        localStorage.setItem('flashMessages', JSON.stringify(messages));
        renderMessages();
    }

    function renderMessages() {
        container.innerHTML = '';
        messages.forEach(_showMessage);
        // оставляем только последний видимым развёрнутым по клику
        container.querySelectorAll('.custom-alert').forEach((el, index) => {
            if (index !== container.children.length - 1) {
                el.classList.add('collapsed');
            }
        });
    }

    return { init, addMessage };
})();


// notif modal show
const NotificationPopup = {
    init: function (options) {
        this.button = document.querySelector(options.button);
        this.popup = document.querySelector(options.popup);

        if (!this.button || !this.popup) {
            console.error("NotificationPopup: элемент(ы) не найдены");
            return;
        }

        this.bindEvents();
    },

    bindEvents: function () {
        this.button.addEventListener("click", (e) => {
            e.stopPropagation();
            this.toggle();
        });

        document.addEventListener("click", (e) => {
            if (!this.popup.contains(e.target) && !this.button.contains(e.target)) {
                this.hide();
            }
        });
    },

    toggle: function () {
        this.popup.classList.toggle("show");
    },

    hide: function () {
        this.popup.classList.remove("show");
    },

    show: function () {
        this.popup.classList.add("show");
    }
};

// notif in header modal load
const Notifications = {
    notifListEl: null,
    notifCountEl: null,
    markAllBtn: null,

    async load() {
        try {
            const response = await fetch("/api/notifications");
            const data = await response.json();
            this.render(data);
        } catch (err) {
            console.error("Ошибка загрузки уведомлений:", err);
        }
    },

    render(data) {
        this.notifListEl.innerHTML = ""; 

        if (!data || data.length === 0) {
            this.notifListEl.innerHTML = "<div class='notif empty'>Нет уведомлений</div>";
            this.hideCounter();
            return;
        }

        let unreadCount = 0;

        data.forEach(n => {
            const notif = document.createElement("div");
            notif.classList.add("notif");
            if (!n.is_read) {
                notif.classList.add("unread");
                unreadCount++;
            }

            notif.innerHTML = `
                <div class="notif-message">${n.message}</div>
                <div class="notif-time">${n.created_at}</div>
            `;
            this.notifListEl.appendChild(notif);
        });

        this.updateCounter(unreadCount);
    },

    updateCounter(count) {
        if (count > 0) {
            this.notifCountEl.innerText = count;
            this.notifCountEl.classList.add("active"); // показываем
        } else {
            this.notifCountEl.classList.remove("active"); // скрываем
            this.notifCountEl.innerText = "";
        }
    },

    hideCounter() {
        this.notifCountEl.style.display = "none";
        this.notifCountEl.innerText = "";
    },

    async markAllRead() {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

            const response = await fetch("/api/notifications/mark-all-read", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken 
                },
                body: "{}"
            });

            if (!response.ok) throw new Error("Ошибка запроса");

            const result = await response.json();
            console.log(result.message);

            this.load();
        } catch (err) {
            console.error("Ошибка при отметке уведомлений:", err);
        }
    },

    init() {
        this.notifListEl = document.getElementById("notifList");
        this.notifCountEl = document.getElementById("notifCount");
        this.markAllBtn  = document.getElementById("markAllRead");

        if (this.markAllBtn) {
            this.markAllBtn.addEventListener("click", () => this.markAllRead());
        }

        this.load();
    }
};

// activation code
const activationCode = {
  init: function() {
    const inputs = document.querySelectorAll('.activation_code_input');
        inputs.forEach((input, index) => {
            input.addEventListener('input', () => {
                if (input.value && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
                else if (!input.value && index > 0) {
                    inputs[index - 1].focus();
                }
            });
    
            input.addEventListener('keydown', (e) => {
                if (e.key === "Backspace" && index > 0 && !input.value) {
                    inputs[index - 1].focus();
                }
            });
        });
    
        inputs[0].addEventListener('paste', (e) => {
            e.preventDefault();
            const pasteData = e.clipboardData.getData('text');
        
            pasteData.split('').forEach((char, i) => {
                if (i < inputs.length) {
                    inputs[i].value = char;
                }
            });

            inputs[Math.min(pasteData.length - 1, inputs.length - 1)].focus();
        });
  }
};

// steps in forms
const formSteps = {
  init: function () {
    const step1 = document.querySelector('.auth-step-1');
    const step2 = document.querySelector('.auth-step-2');
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const requiredFields = ['#name', '#secondname', '#phone'];

    if (!step1 || !step2 || !nextBtn) return;

    function checkFields() {
      return requiredFields.every(field => {
        const input = document.querySelector(field);
        return input && input.value.trim() !== '';
      });
    }

    function updateNextButtonState() {
      nextBtn.disabled = !checkFields();
    
      if (nextBtn.disabled) {
        nextBtn.classList.add('disabled');
      } else {
        nextBtn.classList.remove('disabled');
      }
    }

    requiredFields.forEach(field => {
      const input = document.querySelector(field);
      if (input) {
        input.addEventListener('input', updateNextButtonState);
        input.addEventListener('change', updateNextButtonState);
        input.addEventListener('paste', updateNextButtonState);
        input.addEventListener('cut', updateNextButtonState);
      }
    });

    updateNextButtonState();

    nextBtn.addEventListener('click', (e) => {
      if (!checkFields()) {
        e.preventDefault();
        return;
      }
      step1.classList.remove('active');
      step2.classList.add('active');
    });

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        step2.classList.remove('active');
        step1.classList.add('active');
      });
    }
  }
};

// language modal
function initLanguageDropdown() {
  const button = document.querySelector('.language-button');
  const dropdown = document.querySelector('.language-dropdown-content');

  if (!button || !dropdown) return;

  button.addEventListener('click', function(e) {
    e.stopPropagation();
    dropdown.classList.toggle('show');
  });

  window.addEventListener('click', function() {
    if (dropdown.classList.contains('show')) {
      dropdown.classList.remove('show');
    }
  });
}

// dropdown Module
const customDropdown = {
    init: function() {
        this.dropdowns = document.querySelectorAll('.custom-dropdown');
        
        if (this.dropdowns.length === 0) return;
        
        this.setupDropdowns();
        this.setupDocumentClick();
        this.setupFilterListeners();
    },
    
    setupDropdowns: function() {
        this.dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            const menu = dropdown.querySelector('.dropdown-menu');
            const items = dropdown.querySelectorAll('.dropdown-item');
            const selectedOption = dropdown.querySelector('.selected-option');
            
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown(dropdown);
            });
            
            items.forEach(item => {
                item.addEventListener('click', () => {
                    this.selectItem(item, selectedOption);
                    this.closeDropdown(dropdown);
                });
            });
        });
    },
    
    setupFilterListeners: function() {
        this.dropdowns.forEach(dropdown => {
            const items = dropdown.querySelectorAll('.dropdown-item');
            const filterType = dropdown.getAttribute('data-filter-type');
            
            items.forEach(item => {
                item.addEventListener('click', () => {
                    const value = item.getAttribute('data-value');
                    this.submitFilterForm(filterType, value);
                });
            });
        });
    },
    
    submitFilterForm: function(filterType, value) {
        const form = document.getElementById(filterType + 'Filter');
        const input = document.getElementById(filterType + 'Input');
        
        if (form && input) {
            input.value = value;
            
            const urlParams = new URLSearchParams(window.location.search);
            ['status', 'year'].forEach(param => {
                if (param !== filterType && urlParams.has(param)) {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = param;
                    hiddenInput.value = urlParams.get(param);
                    form.appendChild(hiddenInput);
                }
            });
            
            form.submit();
        }
    },
    
    setupDocumentClick: function() {
        document.addEventListener('click', () => {
            this.closeAllDropdowns();
        });
    },
    
    toggleDropdown: function(dropdown) {
        this.closeAllDropdowns();
        dropdown.classList.toggle('active');
    },
    
    closeDropdown: function(dropdown) {
        dropdown.classList.remove('active');
    },
    
    closeAllDropdowns: function() {
        this.dropdowns.forEach(dropdown => {
            this.closeDropdown(dropdown);
        });
    },
    
    selectItem: function(item, selectedOption) {
        selectedOption.textContent = item.textContent;
    }
};

// status row
const STATUS_CONFIG = {
  'plan-cont-redac': {
    width: '20%',
    color: 'var(--color-redaced)'
  },
  'plan-cont-control': {
    width: '40%', 
    color: 'var(--color-controled)'
  },
  'plan-cont-sent': {
    width: '60%',
    color: 'var(--color-sented)'
  },
  'plan-cont-eror': {
    width: '80%',
    color: 'var(--color-erorsed)'
  },
  'plan-cont-sub': {
    width: '100%',
    color: 'var(--color-submited)'
  }
};

const elements = {
  planConts: document.querySelectorAll('.plan-cont'),
  progressLine: document.querySelector('.progress-line-active'),
  dots: document.querySelectorAll('.status-dot')
};

const checkElements = () => {
  if (!elements.planConts.length || !elements.progressLine || !elements.dots.length) {
    console.warn('Не найдены необходимые элементы для прогресс-бара');
    return false;
  }
  return true;
};

const setupEventHandlers = () => {
  elements.planConts.forEach(planCont => {
    planCont.addEventListener('mouseenter', handleMouseEnter);
    planCont.addEventListener('mouseleave', handleMouseLeave);
  });
};

const handleMouseEnter = (event) => {
  const planCont = event.currentTarget;
  
  for (const [className, config] of Object.entries(STATUS_CONFIG)) {
    if (planCont.classList.contains(className)) {
      updateProgressBar(config);
      updateDots(className);
      break;
    }
  }
};

const updateProgressBar = (config) => {
  elements.progressLine.style.width = config.width;
  elements.progressLine.style.background = config.color;
};

const updateDots = (activeClass) => {
  const activeIndex = Object.keys(STATUS_CONFIG).indexOf(activeClass);
  const activeColor = STATUS_CONFIG[activeClass].color;
  
  elements.dots.forEach((dot, index) => {
    dot.style.background = index <= activeIndex ? activeColor : 'var(--border-color)';
  });
};

const handleMouseLeave = () => {
  elements.progressLine.style.width = '0';
  elements.dots.forEach(dot => {
    dot.style.background = 'var(--border-color)';
  });
};

const initStatusProgress = () => {
  if (!checkElements()) return;
  
  setupEventHandlers();

  return () => {
    elements.planConts.forEach(planCont => {
      planCont.removeEventListener('mouseenter', handleMouseEnter);
      planCont.removeEventListener('mouseleave', handleMouseLeave);
    });
  };
};

// func to show modals
function handleModal(modalElement, openLink, closeLink) {
    openLink.addEventListener('click', function(event) {
        if (openLink.style.opacity === '0.5') {
            event.preventDefault();
        } else {
            modalElement.classList.add('active');
        }
    });

    closeLink.addEventListener('click', function() {
        modalElement.classList.remove('active');
    });

    window.addEventListener('click', function(event) {
        if (event.target === modalElement) {
            modalElement.classList.remove('active');
        }
    });
}

// event modal
class EventModal {
  constructor(modalId) {
    this.modal = document.getElementById(modalId);
    if (!this.modal) return;

    this.progressBar = this.modal.querySelector('#modal-progress-bar');

    this.stepEls = Array.from(this.modal.querySelectorAll('[id^="step"]'))
      .filter(el => /^step\d+$/.test(el.id))
      .sort((a, b) => parseInt(a.id.slice(4), 10) - parseInt(b.id.slice(4), 10));

    this.totalSteps = this.stepEls.length || 1;
    this.currentStep = 1;

    this.buttons = {
      step1Next: this.modal.querySelector('#step1-next-btn'),
      step2Back: this.modal.querySelector('#step2-back-btn'),
      step2Next: this.modal.querySelector('#step2-next-btn'),
      step3Back: this.modal.querySelector('#step3-back-btn'),
      step3Next: this.modal.querySelector('#step3-next-btn')
    };

    this.init();
  }

  init() {
    this.buttons.step1Next?.addEventListener('click', () => this.nextStep());
    this.buttons.step2Back?.addEventListener('click', () => this.prevStep());
    this.buttons.step2Next?.addEventListener('click', () => this.nextStep());
    this.buttons.step3Back?.addEventListener('click', () => this.prevStep());
    this.buttons.step3Next?.addEventListener('click', () => this.submitForm());


  }

  activeStepEl() {
    return this.stepEls[this.currentStep - 1];
  }

  updateProgressBar() {
    if (!this.progressBar) return;
    const progress = (this.currentStep / this.totalSteps) * 100;
    this.progressBar.style.width = progress + '%';
  }

  nextStep() {
    if (this.currentStep >= this.totalSteps) return;
    this.activeStepEl().style.display = 'none';
    this.currentStep++;
    this.activeStepEl().style.display = 'block';
    this.updateProgressBar();
  }

  prevStep() {
    if (this.currentStep <= 1) return;
    this.activeStepEl().style.display = 'none';
    this.currentStep--;
    this.activeStepEl().style.display = 'block';
    this.updateProgressBar();
  }

  validateStep1() { return true; }
  validateStep2() { return true; }

  submitForm() {
  }

  close() {
    this.modal.style.display = 'none';
  }

  resetForm() {
    this.stepEls.forEach((el, i) => el.style.display = i === 0 ? 'block' : 'none');
    this.currentStep = 1;
    this.updateProgressBar();
  }
}

/* numbers + dot only */
var numeric_input = document.querySelectorAll('.app-numeric-input');
numeric_input.forEach(function(input) {
    input.addEventListener('input', function(event) {
        var oldValue = this.value;
        var selectionStart = this.selectionStart;
        var selectionEnd = this.selectionEnd;
        
        var value = oldValue.replace(/[^\d.]/g, '');
        var parts = value.split('.');
        if (parts.length > 1) {
            value = parts[0] + '.' + parts[1].slice(0, 3);
        }
        
        if (value.startsWith('0') && value.length > 1 && value[1] !== '.') {
            value = value.substring(1);
        }

        if (!value.includes('.')) {
            value += '.000';
        }

        var oldDotIndex = oldValue.indexOf('.');
        var newDotIndex = value.indexOf('.');

        this.value = value;

        if (selectionEnd - selectionStart > 1) {
            this.setSelectionRange(selectionEnd, selectionEnd);
        } else if (selectionStart <= oldDotIndex) {
            var cursorPos = selectionStart + (newDotIndex - oldDotIndex);
            this.setSelectionRange(cursorPos, cursorPos);
        } else {
            this.setSelectionRange(selectionStart, selectionStart);
        }
    });

    input.addEventListener('focus', function(event) {
        if (this.value === '') {
            this.value = '0.000';
        }

        var dotIndex = this.value.indexOf('.');
        if (dotIndex !== -1) {
            this.setSelectionRange(dotIndex, dotIndex);
        }
    });

    input.addEventListener('click', function(event) {
        this.select();
    });
});
/* end numbers + dot only */

/* numbers + dot + minys only */
var numeric_input_negative = document.querySelectorAll('.app-numeric-input-negative');
numeric_input_negative.forEach(function(input) {
    input.addEventListener('input', function(event) {
        var oldValue = this.value;
        var selectionStart = this.selectionStart;
        var selectionEnd = this.selectionEnd;
        
        var value = oldValue.replace(/[^\d.-]/g, '');
        
        var minusCount = (value.match(/-/g) || []).length;
        if (minusCount > 1) {
            value = value.replace(/-/g, '');
            value = '-' + value;
        } else if (minusCount === 1 && !value.startsWith('-')) {
            value = value.replace(/-/g, '');
            value = '-' + value;
        }
        
        var parts = value.split('.');
        if (parts.length > 1) {
            value = parts[0] + '.' + parts[1].slice(0, 3);
        }
        
        if (!value.startsWith('-')) {
            if (value.startsWith('0') && value.length > 1 && value[1] !== '.') {
                value = value.substring(1);
            }
        } 
        else {
            if (value.startsWith('-0') && value.length > 2 && value[2] !== '.') {
                value = '-' + value.substring(2);
            }
        }

        if (!value.includes('.')) {
            if (value === '' || value === '-') {
                value += '0.000';
            } else {
                value += '.000';
            }
        }

        var oldDotIndex = oldValue.indexOf('.');
        var newDotIndex = value.indexOf('.');

        this.value = value;

        if (selectionEnd - selectionStart > 1) {
            this.setSelectionRange(selectionEnd, selectionEnd);
        } else if (selectionStart <= oldDotIndex) {
            var cursorPos = selectionStart + (newDotIndex - oldDotIndex);
            this.setSelectionRange(cursorPos, cursorPos);
        } else {
            this.setSelectionRange(selectionStart, selectionStart);
        }
    });

    input.addEventListener('focus', function(event) {
        if (this.value === '') {
            this.value = '0.000';
        }

        var dotIndex = this.value.indexOf('.');
        if (dotIndex !== -1) {
            this.setSelectionRange(dotIndex, dotIndex);
        }
    });

    input.addEventListener('click', function(event) {
        this.select();
    });
});
/* end numbers + dot + minys only */

class DirectionsTable {
    constructor({ searchSelector, tableSelector, hiddenInputSelector, nextButtonSelector }) {
        this.searchInput = document.querySelector(`[data-action="${searchSelector}"]`);
        this.table = document.querySelector(`[data-action="${tableSelector}"] tbody`);
        this.hiddenInput = document.querySelector(`[data-action="${hiddenInputSelector}"]`);
        this.nextButton = document.querySelector(`[data-action="${nextButtonSelector}"]`);
        this.selectedId = null;

        if (!this.searchInput || !this.table) return;

        this.initSearch();
        this.initSelection();

        if (this.nextButton) {
            this.nextButton.disabled = true;
        }
    }

    initSearch() {
        this.searchInput.addEventListener("input", () => {
            const filter = this.searchInput.value.toLowerCase();
            const rows = this.table.querySelectorAll("tr");

            rows.forEach(row => {
                const code = row.cells[1].textContent.toLowerCase();
                const name = row.cells[2].textContent.toLowerCase();
                row.style.display = (code.includes(filter) || name.includes(filter)) ? "" : "none";
            });
        });
    }

    initSelection() {
        this.table.addEventListener("click", (e) => {
            const row = e.target.closest("tr");
            if (!row) return;

            this.table.querySelectorAll("tr").forEach(r => r.classList.remove("selected"));
            row.classList.add("selected");

            this.selectedId = row.cells[0].textContent.trim();

            if (this.hiddenInput) {
                this.hiddenInput.value = this.selectedId;
            }
            if (this.nextButton) {
                this.nextButton.disabled = false;
            }
        });
    }
}

class TableContextMenu {
    constructor(tableId, menuId, options = {}) {
        this.table = document.getElementById(tableId);
        this.menu = document.getElementById(menuId);
        this.selectedRow = null;
        
        // Кнопки в контекстном меню
        this.contextDeleteButton = options.contextDeleteButtonId ? document.getElementById(options.contextDeleteButtonId) : null;
        this.contextEditButton = options.contextEditButtonId ? document.getElementById(options.contextEditButtonId) : null;
        
        // Кнопки над таблицей
        this.tableDeleteButton = options.tableDeleteButtonId ? document.getElementById(options.tableDeleteButtonId) : null;
        this.tableEditButton = options.tableEditButtonId ? document.getElementById(options.tableEditButtonId) : null;
        
        // Callback функции
        this.editCallback = options.editCallback || null;
        this.removeCallback = options.removeCallback || null;
        this.removeUrlTemplate = options.removeUrlTemplate || null;
        
        // Параметры для неизменяемых строк
        this.immutableCodes = options.immutableCodes || []; // Коды, которые нельзя изменять/удалять
        this.immutableEditCodes = options.immutableEditCodes || []; // Коды, которые нельзя редактировать
        this.immutableDeleteCodes = options.immutableDeleteCodes || []; // Коды, которые нельзя удалять
        this.codeColumnIndex = options.codeColumnIndex || 0; // Индекс столбца с кодом
        this.hideCodeColumn = options.hideCodeColumn !== false; // Скрывать ли столбец с кодом

        if (!this.table || !this.menu) return;
        this.init();
    }

    init() {
        if (this.hideCodeColumn) {
            this.hideCodeColumnInTable();
        }

        this.table.querySelectorAll('tbody.rows tr.menu-row').forEach(row => {
            row.addEventListener('contextmenu', (event) => this.onRowRightClick(event, row));
            row.addEventListener('click', (event) => this.onRowLeftClick(event, row));
        });
        
        document.addEventListener('click', (event) => {
            if (!this.menu.contains(event.target)) {
                this.hideMenu();
            }
        });

        // Обработчики для кнопок в контекстном меню
        if (this.contextEditButton) {
            this.contextEditButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (this.isRowActive() && this.editCallback && !this.isEditDisabled(this.selectedRow)) {
                    this.editCallback(this.selectedRow.dataset.id);
                }
            });
        }

        if (this.contextDeleteButton) {
            this.contextDeleteButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (this.isRowActive() && !this.isDeleteDisabled(this.selectedRow)) {
                    this.showConfirmModal(this.selectedRow.dataset.id);
                }
            });
        }

        // Обработчики для кнопок над таблицей
        if (this.tableEditButton) {
            this.tableEditButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (this.isRowActive() && this.editCallback && !this.isEditDisabled(this.selectedRow)) {
                    this.editCallback(this.selectedRow.dataset.id);
                }
            });
        }

        if (this.tableDeleteButton) {
            this.tableDeleteButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (this.isRowActive() && !this.isDeleteDisabled(this.selectedRow)) {
                    this.showConfirmModal(this.selectedRow.dataset.id);
                }
            });
        }

        this.updateButtonsState();
    }

    hideCodeColumnInTable() {
        const headerCells = this.table.querySelectorAll('thead th');
        if (headerCells.length > this.codeColumnIndex) {
            headerCells[this.codeColumnIndex].classList.add('hidden-column');
        }
        
        const rows = this.table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length > this.codeColumnIndex) {
                cells[this.codeColumnIndex].classList.add('hidden-column');
            }
        });
    }

    getRowCode(row) {
        const cells = row.querySelectorAll('td');
        if (cells.length > this.codeColumnIndex) {
            return cells[this.codeColumnIndex].textContent.trim();
        }
        return null;
    }

    isEditDisabled(row) {
        if (!row) return true;
        const rowCode = this.getRowCode(row);
        return this.immutableCodes.includes(rowCode) || this.immutableEditCodes.includes(rowCode);
    }

    isDeleteDisabled(row) {
        if (!row) return true;
        const rowCode = this.getRowCode(row);
        return this.immutableCodes.includes(rowCode) || this.immutableDeleteCodes.includes(rowCode);
    }

    isRowActive() {
        return this.selectedRow && this.selectedRow.classList.contains('active-row');
    }

    updateButtonsState() {
        const isActive = this.isRowActive();
        const isEditDisabled = this.isEditDisabled(this.selectedRow);
        const isDeleteDisabled = this.isDeleteDisabled(this.selectedRow);
        
        const allButtons = [
            this.contextEditButton,
            this.contextDeleteButton,
            this.tableEditButton,
            this.tableDeleteButton
        ];
        
        allButtons.forEach(button => {
            if (button) {
                if (!isActive) {
                    button.classList.add('btn-disabled');
                } else {
                    const isEditButton = button === this.contextEditButton || button === this.tableEditButton;
                    const isDeleteButton = button === this.contextDeleteButton || button === this.tableDeleteButton;
                    
                    if (isEditButton && isEditDisabled) {
                        button.classList.add('btn-disabled');
                    } else if (isEditButton && !isEditDisabled) {
                        button.classList.remove('btn-disabled');
                    } else if (isDeleteButton && isDeleteDisabled) {
                        button.classList.add('btn-disabled');
                    } else if (isDeleteButton && !isDeleteDisabled) {
                        button.classList.remove('btn-disabled');
                    }
                }
            }
        });
    }

    onRowLeftClick(event, row) {
        event.stopPropagation();
        
        if (row.classList.contains('active-row')) {
            row.classList.remove('active-row');
            this.selectedRow = null;
        } else {
            if (this.selectedRow && this.selectedRow !== row) {
                this.selectedRow.classList.remove('active-row');
            }
            row.classList.add('active-row');
            this.selectedRow = row;
        }

        const editDirectionModal = document.getElementById('EditDirectionModal');
        if (editDirectionModal) {
            Edit_econmeasure_modal();
        }
        
        const editEventModal = document.getElementById('EditEventModal');
        if (editEventModal) {
            Edit_econexece_modal();
        }

        const editIndicatorModal = document.getElementById('EditIndicatorModal');
        if (editIndicatorModal) {
            Edit_indicator_modal();
        }

        this.updateButtonsState();
        this.hideContextMenu();
    }

    onRowRightClick(event, row) {
        event.preventDefault();
        event.stopPropagation();

        if (this.selectedRow && this.selectedRow !== row) {
            this.selectedRow.classList.remove('active-row');
        }

        row.classList.add('active-row');
        this.selectedRow = row;

        if (!this.isDeleteDisabled(row) && this.removeUrlTemplate) {
            const removeForm = this.menu.querySelector('form#removeForm');
            if (removeForm) {
                removeForm.action = this.removeUrlTemplate.replace('{id}', row.dataset.id);
            }
        }

        const editDirectionModal = document.getElementById('EditDirectionModal');
        if (editDirectionModal) {
            Edit_econmeasure_modal();
        }
        
        const editEventModal = document.getElementById('EditEventModal');
        if (editEventModal) {
            Edit_econexece_modal();
        }

        const editIndicatorModal = document.getElementById('EditIndicatorModal');
        if (editIndicatorModal) {
            Edit_indicator_modal();
        }
        
        this.updateButtonsState();
        this.showMenu(event.pageX, event.pageY);
    }

    showMenu(x, y) {
        this.menu.style.top = `${y}px`;
        this.menu.style.left = `${x}px`;
        this.menu.style.display = 'block';
    }

    hideMenu() {
        this.hideContextMenu();
    }
    
    hideContextMenu() {
        this.menu.style.display = 'none';
    }

    showConfirmModal(rowId) {
        // Проверяем, не отключено ли удаление для строки
        if (this.isDeleteDisabled(this.selectedRow)) {
            return;
        }

        const modal = document.getElementById('confirmModal');
        if (!modal) return;

        const yesBtn = modal.querySelector('#confirmYesdelete');
        const noBtn = modal.querySelector('#confirmNodelete');

        modal.classList.add('active');

        yesBtn.onclick = null;
        noBtn.onclick = null;

        yesBtn.onclick = () => {
            modal.classList.remove('active');
            
            if (this.removeCallback) {
                this.removeCallback(rowId);
            } else if (this.removeUrlTemplate) {
                this.submitForm(this.removeUrlTemplate.replace('{id}', rowId));
            }
        };

        noBtn.onclick = () => {
            modal.classList.remove('active');
        };

        window.onclick = (event) => {
            if (event.target === modal) {
                modal.classList.remove('active');
            }
        };
    }

    submitForm(url) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        form.style.display = 'none';
        
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token'; 
            csrfInput.value = csrfToken.content;
            form.appendChild(csrfInput);
        }

        document.body.appendChild(form);
        form.submit();
    }
}

function initExportPage() {
    const form = document.getElementById("exportForm");
    const formatInput = document.getElementById("selectedFormat");
    const checkboxes = document.querySelectorAll('input[name="ids"]');
    const exportBtn = document.getElementById("exportBtn");
    const selectAllBtn = document.getElementById("selectAllBtn");

    function updateButtonState() {
        const formatSelected = !!formatInput.value;
        const planSelected = Array.from(checkboxes).some(cb => cb.checked);
        exportBtn.disabled = !(formatSelected && planSelected);

        form.action = formatSelected ? `/export-to/${formatInput.value}` : "";
    }

    document.querySelectorAll(".choose-conteiner").forEach(item => {
        item.addEventListener("click", () => {
            document.querySelectorAll(".choose-conteiner").forEach(el => el.classList.remove("active"));
            item.classList.add("active");
            formatInput.value = item.dataset.format;
            updateButtonState();
        });
    });

    if (selectAllBtn) {
        selectAllBtn.addEventListener("change", () => {
            checkboxes.forEach(cb => cb.checked = selectAllBtn.checked);
            updateButtonState();
        });
    }

    checkboxes.forEach(cb => cb.addEventListener("change", updateButtonState));

    updateButtonState();
}

function Edit_econmeasure_modal() {
    const EditDirectionsModal = document.getElementById('EditDirectionModal');
    if (!EditDirectionsModal) {
        console.error('Модальное окно не найдено');
        return;
    }

    var activeRow = document.querySelector('.rows .active-row');
    if (!activeRow) {
        // console.error('Активная строка не найдена');
        return;
    }

    var idEvent = activeRow.getAttribute('data-id');
    if (!idEvent) {
        console.error('ID мероприятия не найден');
        return;
    }

    showLoadingIndicator(true);

    fetch(`/get-econmeasure/${idEvent}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сети: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            setValueIfExists('change-year-econ', data.year_econ || '');
            setValueIfExists('change-estim-econ', data.estim_econ || '');
            
            var form = document.getElementById('editEconForm');
            if (form) {
                form.action = `/edit-econmeasure/${idEvent}`;
            } else {
                console.error('Форма editEconForm не найдена');
            }
        })
        .catch(error => {
            console.error('Error fetching econexece data:', error);
            alert('Ошибка при загрузке данных мероприятия: ' + error.message);
        })
        .finally(() => {
            showLoadingIndicator(false);
        });
}

function Edit_econexece_modal(){
    const EditEventModal = document.getElementById('EditEventModal');
    if (!EditEventModal) {
        console.error('Модальное окно не найдено');
        return;
    }

    var activeRow = document.querySelector('.rows .active-row');
    if (!activeRow) {
        // console.error('Активная строка не найдена');
        return;
    }

    var idEvent = activeRow.getAttribute('data-id');
    if (!idEvent) {
        console.error('ID мероприятия не найден');
        return;
    }

    showLoadingIndicator(true);

    fetch(`/get-econexece/${idEvent}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сети: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            setValueIfExists('change-name-edit-model', data.name || '');
            setValueIfExists('change-Volume-edit-model', data.Volume || '');
            setValueIfExists('change-EffTut-edit-model', data.EffTut || '');
            setValueIfExists('change-EffRub-edit-model', data.EffRub || '');
            setValueIfExists('change-ExpectedQuarter-edit-model', data.ExpectedQuarter || '');
            setValueIfExists('change-EffCurrYear-edit-model', data.EffCurrYear || '');
            setValueIfExists('change-Payback-edit-model', data.Payback || '');
            setValueIfExists('change-VolumeFin-edit-model', data.VolumeFin || '');
            setValueIfExists('change-BudgetState-edit-model', data.BudgetState || '');
            setValueIfExists('change-BudgetRep-edit-model', data.BudgetRep || '');
            setValueIfExists('change-BudgetLoc-edit-model', data.BudgetLoc || '');
            setValueIfExists('change-BudgetOther-edit-model', data.BudgetOther || '');
            setValueIfExists('change-MoneyOwn-edit-model', data.MoneyOwn || '');
            setValueIfExists('change-MoneyLoan-edit-model', data.MoneyLoan || '');
            setValueIfExists('change-MoneyOther-edit-model', data.MoneyOther || '');
            
            var form = document.getElementById('editEconexeceForm');
            if (form) {
                form.action = `/edit-econexeces/${idEvent}`;
            } else {
                console.error('Форма editEconexeceForm не найдена');
            }
        })
        .catch(error => {
            console.error('Error fetching econexece data:', error);
            alert('Ошибка при загрузке данных мероприятия: ' + error.message);
        })
        .finally(() => {
            showLoadingIndicator(false);
        });
}

function Edit_indicator_modal(){
    const EditIndicatorModal = document.getElementById('EditIndicatorModal');
    if (!EditIndicatorModal) {
        console.error('Модальное окно EditIndicatorModal не найдено');
        return;
    }

    var activeRow = document.querySelector('.rows .active-row');
    if (!activeRow) {
        return;
    }

    var idIndicator = activeRow.getAttribute('data-id');
    if (!idIndicator) {
        console.error('ID не найден');
        return;
    }

    // Получаем значение Group - несколько вариантов поиска для надежности
    let groupValue = '';
    
    // Вариант 1: Ищем по data-атрибуту (если добавили data-group)
    const groupDataCell = activeRow.querySelector('td[data-group]');
    if (groupDataCell) {
        groupValue = groupDataCell.getAttribute('data-group');
    } 
    // Вариант 2: Ищем по классу (если добавили class="group-cell")
    else {
        const groupClassCell = activeRow.querySelector('td.group-cell');
        if (groupClassCell) {
            groupValue = groupClassCell.textContent.trim();
        }
        // Вариант 3: Ищем по стилю display: none (оригинальный способ)
        else {
            const groupStyleCell = activeRow.querySelector('td[style*="display: none"]');
            if (groupStyleCell) {
                groupValue = groupStyleCell.textContent.trim();
            }
        }
    }

    const isGroup6 = groupValue === '6';

    // Управляем видимостью элементов
    const qYearCurrNoDisplay = document.getElementById('QYearCurr-edit-nodisplay');
    const qYearPrevNoDisplay = document.getElementById('QYearPrev-edit-nodisplay');
    
    // Находим input поля внутри этих контейнеров
    const qYearCurrInput = qYearCurrNoDisplay ? qYearCurrNoDisplay.querySelector('input') : null;
    const qYearPrevInput = qYearPrevNoDisplay ? qYearPrevNoDisplay.querySelector('input') : null;
    
    if (qYearCurrNoDisplay) {
        qYearCurrNoDisplay.style.display = isGroup6 ? 'none' : '';
    }
    
    if (qYearPrevNoDisplay) {
        qYearPrevNoDisplay.style.display = isGroup6 ? 'none' : '';
    }

    // Управляем обязательностью полей
    if (qYearCurrInput) {
        if (isGroup6) {
            qYearCurrInput.removeAttribute('required');
        } else {
            qYearCurrInput.setAttribute('required', 'required');
        }
    }
    
    if (qYearPrevInput) {
        if (isGroup6) {
            qYearPrevInput.removeAttribute('required');
        } else {
            qYearPrevInput.setAttribute('required', 'required');
        }
    }

    showLoadingIndicator(true);

    fetch(`/get-indicator/${idIndicator}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сети: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Для группы 6 не заполняем QYearPrev и QYearCurr
            if (!isGroup6) {
                setValueIfExists('QYearPrev-edit', data.QYearPrev ? (data.QYearPrev / data.CoeffToTut).toFixed(3) : '');
                setValueIfExists('QYearCurr-edit', data.QYearCurr ? (data.QYearCurr / data.CoeffToTut).toFixed(3) : '');
            } else {
                // Очищаем значения для группы 6
                setValueIfExists('QYearPrev-edit', '');
                setValueIfExists('QYearCurr-edit', '');
            }
            
            // QYearNext заполняем всегда
            setValueIfExists('QYearNext-edit', data.QYearNext ? (data.QYearNext / data.CoeffToTut).toFixed(3) : '');
            
            const predictionElements = document.querySelectorAll('.prediction-value');
            predictionElements.forEach(element => {
                if (data.CoeffToTut) {
                    element.dataset.multiplier = data.CoeffToTut;
                }
            });

            var form = document.getElementById('editIndicatorForm');
            if (form) {
                form.action = `/edit-indicator/${idIndicator}`;
            } else {
                console.error('Форма не найдена');
            }
        })
        .catch(error => {
            console.error('Error fetching econexece data:', error);
            alert('Ошибка при загрузке данных: ' + error.message);
        })
        .finally(() => {
            showLoadingIndicator(false);
        });
}

function setValueIfExists(elementId, value) {
    var element = document.getElementById(elementId);
    if (element) {
        element.value = value;
        // console.log(`Установлено значение для ${elementId}:`, value);
    } else {
        console.error(`Элемент с ID '${elementId}' не найден`);
    }
}

function showLoadingIndicator(show) {
    var loader = document.getElementById('loading-indicator');
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }
}

function initColumnResize() {
    const table = document.querySelector('.main-table');
    const thElements = table.querySelectorAll('th.resizable');
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    let currentTh = null;

    thElements.forEach(th => {
        const resizer = th.querySelector('.resizer');
        if (resizer) {
            resizer.addEventListener('mousedown', function(e) {
                isResizing = true;
                startX = e.clientX;
                startWidth = th.offsetWidth;
                currentTh = th;
                document.body.style.cursor = 'col-resize';
                e.preventDefault();
            });
        }
    });

    document.addEventListener('mousemove', function(e) {
        if (isResizing) {
            const newWidth = startWidth + (e.clientX - startX);
            currentTh.style.width = newWidth + 'px';
            currentTh.style.minWidth = newWidth + 'px';
        }
    });

    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
        }
    });
}

// OrganizationSearchManager
class OrganizationSearchManager {
    constructor(config = {}) {
        this.config = {
            searchInputSelector: 'input[data-action="search-organization"]',
            tableBodySelector: '#orgUserModal table[data-action="organization-table"] tbody',
            selectedOrgInputSelector: 'input[data-action="selected-org"]',
            submitButtonSelector: '#orgUserModal button[type="submit"]',
            apiUrl: '/api/organizations',
            ...config
        };

        this.init();
    }

    init() {
        this.searchInput = document.querySelector(this.config.searchInputSelector);
        this.tableBody = document.querySelector(this.config.tableBodySelector);
        this.selectedOrgInput = document.querySelector(this.config.selectedOrgInputSelector);
        this.submitButton = document.querySelector(this.config.submitButtonSelector);

        if (!this.searchInput || !this.tableBody || !this.selectedOrgInput) {
            console.error('OrganizationSearchManager: Не найдены необходимые элементы');
            return;
        }

        this.bindEvents();
        this.updateSubmitButtonState();
    }

    bindEvents() {
        let debounceTimer;
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            debounceTimer = setTimeout(() => this.loadOrganizations(query), 300);
        });

        this.tableBody.addEventListener('click', (e) => {
            const row = e.target.closest('tr');
            if (row && row.dataset.id) {
                this.selectOrganization(row);
            }
        });

        if (this.submitButton) {
            this.submitButton.addEventListener('click', (e) => {
                if (!this.selectedOrgInput.value) {
                    e.preventDefault();
                    this.showNotification('Пожалуйста, выберите организацию из списка');
                }
            });
        }

        const form = this.selectedOrgInput.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (!this.selectedOrgInput.value) {
                    e.preventDefault();
                    this.showNotification('Пожалуйста, выберите организацию из списка');
                }
            });
        }
    }

    async loadOrganizations(query = '') {
        try {
            const url = `${this.config.apiUrl}?q=${encodeURIComponent(query)}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }

            const data = await response.json();
            this.renderOrganizations(data.organizations);
        } catch (error) {
            console.error('OrganizationSearchManager: Ошибка загрузки организаций:', error);
            this.showError('Ошибка загрузки данных');
        }
    }

    renderOrganizations(organizations) {
        this.tableBody.innerHTML = '';

        if (!organizations || organizations.length === 0) {
            this.tableBody.innerHTML = `
                <tr>
                    <td colspan="3">Нет данных</td>
                </tr>
            `;
            return;
        }

        organizations.forEach(org => {
            const row = document.createElement('tr');
            row.dataset.id = org.id;
            row.innerHTML = `
                <td style="display: none;">${this.escapeHtml(org.id)}</td>
                <td>${this.escapeHtml(org.name)}</td>
                <td>${this.escapeHtml(org.okpo)}</td>
            `;
            this.tableBody.appendChild(row);
        });
    }

    selectOrganization(row) {
        const orgId = row.dataset.id;
        this.selectedOrgInput.value = orgId;
        
        this.highlightSelectedRow(row);
        this.updateSubmitButtonState(true);
        this.dispatchSelectionEvent(orgId, row);
    }

    highlightSelectedRow(selectedRow) {
        const allRows = this.tableBody.querySelectorAll('tr');
        allRows.forEach(row => {
            row.classList.remove('selected');
        });
        
        selectedRow.classList.add('selected');
    }

    updateSubmitButtonState(isActive = false) {
        if (!this.submitButton) return;

        if (isActive && this.selectedOrgInput.value) {
            this.submitButton.disabled = false;
            this.submitButton.classList.remove('disabled');
        } else {
            this.submitButton.disabled = true;
            this.submitButton.classList.add('disabled');
        }
    }

    dispatchSelectionEvent(orgId, row) {
        const event = new CustomEvent('organizationSelected', {
            detail: {
                id: orgId,
                name: row.cells[1].textContent,
                okpo: row.cells[2].textContent,
                element: row
            }
        });
        document.dispatchEvent(event);
    }

    showError(message) {
        this.tableBody.innerHTML = `
            <tr>
                <td colspan="3">${message}</td>
            </tr>
        `;
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff4757;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 1000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    clearSearch() {
        this.searchInput.value = '';
        this.loadOrganizations();
    }

    clearSelection() {
        this.selectedOrgInput.value = '';
        this.updateSubmitButtonState(false);
        
        const allRows = this.tableBody.querySelectorAll('tr');
        allRows.forEach(row => {
            row.classList.remove('selected');
        });
    }

    getSelectedOrganizationId() {
        return this.selectedOrgInput.value;
    }

    destroy() {
        this.searchInput.replaceWith(this.searchInput.cloneNode(true));
        this.tableBody.replaceWith(this.tableBody.cloneNode(true));
    }
}

const TableCollapseManager = (function() {
    let isInitialized = false;
    let groupHeaders = [];

    function toggleContent(header) {
        const targetId = header.getAttribute('data-target');
        const target = document.getElementById(targetId);
        
        if (target) {
            if (target.style.display === 'none') {
                target.style.display = 'table-row-group';
                const arrow = header.querySelector('.dropdown-arrow');
                if (arrow) {
                    arrow.style.transform = 'rotate(0deg)';
                    arrow.style.transition = 'transform 0.3s ease';
                }
            } else {
                target.style.display = 'none';
                const arrow = header.querySelector('.dropdown-arrow');
                if (arrow) {
                    arrow.style.transform = 'rotate(-90deg)';
                    arrow.style.transition = 'transform 0.3s ease';
                }
            }
        }
    }
    
    function initHeaders() {
        groupHeaders = document.querySelectorAll('.group-header');
        
        groupHeaders.forEach(header => {
            header.style.cursor = 'pointer';
            
            header.addEventListener('click', function() {
                toggleContent(this);
            });
            
            header.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f5f5f5';
            });
            
            header.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    }
    
    // Публичный API
    return {
        init: function(options = {}) {
            if (isInitialized) {
                console.warn('TableCollapseManager уже инициализирован');
                return;
            }
            
            const config = {
                autoInit: options.autoInit !== false,
                initiallyCollapsed: options.initiallyCollapsed || [''], //other-content
                ...options
            };
            
            if (config.autoInit) {
                this.initializeAll();
            }
            
            if (config.initiallyCollapsed && config.initiallyCollapsed.length > 0) {
                config.initiallyCollapsed.forEach(sectionId => {
                    this.collapseSection(sectionId);
                });
            }
            
            isInitialized = true;
            // console.log('TableCollapseManager инициализирован');
        },
        
        initializeAll: function() {
            initHeaders();
        },
        
        collapseSection: function(sectionId) {
            const header = document.querySelector(`[data-target="${sectionId}"]`);
            if (header) {
                toggleContent(header);
            }
        },
        
        expandSection: function(sectionId) {
            const header = document.querySelector(`[data-target="${sectionId}"]`);
            const target = document.getElementById(sectionId);
            
            if (header && target) {
                target.style.display = 'table-row-group';
                const arrow = header.querySelector('.dropdown-arrow');
                if (arrow) arrow.style.transform = 'rotate(0deg)';
            }
        },
        
        toggleSection: function(sectionId) {
            const header = document.querySelector(`[data-target="${sectionId}"]`);
            if (header) {
                toggleContent(header);
            }
        },
        
        getSectionState: function(sectionId) {
            const target = document.getElementById(sectionId);
            return target ? target.style.display !== 'none' : null;
        },
        
        addSection: function(headerElement, contentElement) {
            if (!headerElement || !contentElement) {
                console.error('Необходимо передать и header и content элементы');
                return;
            }
            
            headerElement.style.cursor = 'pointer';
            headerElement.addEventListener('click', function() {
                toggleContent(this);
            });
            
            headerElement.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f5f5f5';
            });
            
            headerElement.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
            
            groupHeaders = document.querySelectorAll('.group-header');
        },
        

        destroy: function() {
            groupHeaders.forEach(header => {
                const newHeader = header.cloneNode(true);
                header.parentNode.replaceChild(newHeader, header);
            });
            
            groupHeaders = [];
            isInitialized = false;
            console.log('TableCollapseManager уничтожен');
        },
        
        isInitialized: function() {
            return isInitialized;
        },
        
        getSections: function() {
            const sections = [];
            groupHeaders.forEach(header => {
                const targetId = header.getAttribute('data-target');
                sections.push({
                    id: targetId,
                    header: header,
                    content: document.getElementById(targetId),
                    isExpanded: this.getSectionState(targetId)
                });
            });
            return sections;
        }
    };
})();

function initConfirmModal(config) {
    const triggerButtons = config.triggerButton ? 
                         document.querySelectorAll(config.triggerButton) : 
                         (config.triggerId ? [document.getElementById(config.triggerId)] : []);
    
    const formElement = config.formElement ||
                       (config.formId ? document.getElementById(config.formId) : null);
    
    const modalElement = config.modalId ? document.getElementById(config.modalId) : null;
    const yesButton = config.yesId ? document.getElementById(config.yesId) : null;
    const noButton = config.noId ? document.getElementById(config.noId) : null;
    const textElement = config.textId ? document.getElementById(config.textId) : null;
    const textElementSecond = config.textSecondId ? document.getElementById(config.textSecondId) : null;

    if (triggerButtons.length === 0 || !modalElement || !yesButton || !noButton) {
        console.error('Modal initialization error: required elements not found', config);
        return;
    }

    triggerButtons.forEach(triggerButton => {
        triggerButton.addEventListener('click', function (e) {
            e.preventDefault();
            const planId = this.getAttribute('data-plan-id');
            
            if (textElement && config.modalText) {
                let text = config.modalText;
                if (planId && text.includes('{id}')) {
                    text = text.replace('{id}', planId);
                }
                textElement.textContent = text;
            }
            
            if (textElementSecond && config.modalTextSecond) {
                textElementSecond.textContent = config.modalTextSecond;
            }   
            
            modalElement.classList.add('active');
            let currentForm = null;
            
            if (formElement) {
                currentForm = formElement;
            } else if (config.formSelector) {
                currentForm = document.querySelector(config.formSelector);
            } else {
                currentForm = this.closest('form');
            }
            modalElement._currentForm = currentForm;
        });
    });

    // подтвердить действие
    yesButton.addEventListener('click', function () {
        modalElement.classList.remove('active');
        if (modalElement._currentForm) {
            modalElement._currentForm.submit();
        }
    });

    // отмена
    noButton.addEventListener('click', function () {
        modalElement.classList.remove('active');
    });

    // клик мимо окна
    modalElement.addEventListener('click', function (event) {
        if (event.target === modalElement) {
            modalElement.classList.remove('active');
        }
    });

    // закрытие по ESC
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && modalElement.classList.contains('active')) {
            modalElement.classList.remove('active');
        }
    });
}

(function() {
    function filterPlans(nameInput, okpoInput, plans) {
        const nameFilter = nameInput ? nameInput.value.toLowerCase() : "";
        const okpoFilter = okpoInput ? okpoInput.value.toLowerCase() : "";

        plans.forEach(plan => {
            const planName = plan.dataset.name || "";
            const planOkpo = plan.dataset.okpo || "";

            const matchName = planName.includes(nameFilter);
            const matchOkpo = planOkpo.includes(okpoFilter);

            plan.style.display = (matchName && matchOkpo) ? "" : "none";
        });
    }

    function initPlansFilter(config = {}) {
        const {
            nameInputSelector = "#search-name",
            okpoInputSelector = "#search-okpo",
            plansSelector = '[data-plan="choose"]' // <- теперь селектор по атрибуту
        } = config;

        const nameInput = document.querySelector(nameInputSelector);
        const okpoInput = document.querySelector(okpoInputSelector);
        const plans = document.querySelectorAll(plansSelector);

        if (!plans.length) return;

        const handler = () => filterPlans(nameInput, okpoInput, plans);

        if (nameInput) nameInput.addEventListener("input", handler);
        if (okpoInput) okpoInput.addEventListener("input", handler);
    }

    window.initPlansFilter = initPlansFilter;
})();

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.toggle-password')) {
    togglePassword.init();
  }

  if (document.querySelector('.activation_code_input')) {
    activationCode.init();
  }

  if (document.querySelector('.auth-step-1') && document.querySelector('.auth-step-2')) {
    formSteps.init();
  }

  initLanguageDropdown();

  customDropdown.init();
  
  if (document.querySelector('.plan-cont')) {
    const cleanup = initStatusProgress();
  }

  new DirectionsTable({
      searchSelector: "search-directions",
      tableSelector: "directions-table",
      hiddenInputSelector: "selected-direction",
      nextButtonSelector: "directions-next"
  });

  if (document.querySelector('.main-table')) {
    setTimeout(initColumnResize, 100);    
    TableCollapseManager.init();  
  }

  const directionTable = document.getElementById('directionTable');
  const directionMenu = document.getElementById('MenuMainTable');
  if (directionTable && directionMenu) {
      const tableMenu = new TableContextMenu('directionTable', 'MenuMainTable', {
          contextEditButtonId: 'contextEditButton',
          contextDeleteButtonId: 'contextDeleteButton',
          
          tableEditButtonId: 'tableEditButton',
          tableDeleteButtonId: 'tableDeleteButton',
          removeUrlTemplate: '/delete-econmeasure/{id}',
          
          immutableCodes: [], // Коды, которые нельзя изменять/удалять
          immutableEditCodes: [], // Коды, которые нельзя редактировать (но можно удалять)
          immutableDeleteCodes: [], // Коды, которые нельзя удалять (но можно редактировать)

          codeColumnIndex: 11, 
          hideCodeColumn: true
      });
  }

  const eventsTable = document.getElementById('eventsTable');
  const eventsMenu = document.getElementById('MenuMainTable');
  if (eventsTable && eventsMenu) {
      const tableMenu = new TableContextMenu('eventsTable', 'MenuMainTable', {
          contextEditButtonId: 'contextEditButton',
          contextDeleteButtonId: 'contextDeleteButton',
          
          tableEditButtonId: 'tableEditButton',
          tableDeleteButtonId: 'tableDeleteButton',
          removeUrlTemplate: '/delete-econexeces/{id}',
          
          immutableCodes: [], // Коды, которые нельзя изменять/удалять
          immutableEditCodes: [], // Коды, которые нельзя редактировать (но можно удалять)
          immutableDeleteCodes: [], // Коды, которые нельзя удалять (но можно редактировать)

          codeColumnIndex: 11, 
          hideCodeColumn: true
      });
  }

  const indicatorsTable = document.getElementById('indicatorsTable');
  const indicatorsMenu = document.getElementById('MenuMainTable');
  if (indicatorsTable && indicatorsMenu) {
      const tableMenu = new TableContextMenu('indicatorsTable', 'MenuMainTable', {
          contextEditButtonId: 'contextEditButton',
          contextDeleteButtonId: 'contextDeleteButton',
          
          tableEditButtonId: 'tableEditButton',
          tableDeleteButtonId: 'tableDeleteButton',
          removeUrlTemplate: '/delete-indicator/{id}',
          
          immutableCodes: ['260', '9900', '9999', '1000'], // Коды, которые нельзя изменять/удалять
          immutableEditCodes: [],
          immutableDeleteCodes: ['9911', '9910', '9912', '9913', '9914', '1404', '1104', '1424', '1105', '1405', '1425', '1445'], // Коды, которые нельзя удалять (но можно редактировать)

          codeColumnIndex: 11, 
          hideCodeColumn: true
      });
  }

  // Добавление Direction
  const addDirectionModal = document.getElementById('AddDirectionModal');
  const DirectionModal = new EventModal('AddDirectionModal');
  if (addDirectionModal && DirectionModal) {
    handleModal(
      addDirectionModal, 
      document.getElementById('AddDirectionModalButton'), 
      addDirectionModal.querySelector('.close')
    );
  }

  // Добавление Event
  const addEventModal = document.getElementById('AddEventModal');
  const addEventModal1 = new EventModal('AddEventModal');
  if (addEventModal && addEventModal1) {
    handleModal(
      addEventModal, 
      document.getElementById('AddEventModalButton'), 
      addEventModal.querySelector('.close')
    );
  }

  // Добавление Indicator
  const addIndicatorModal = document.getElementById('AddIndicatorModal');
  const IndicatorModal = new EventModal('AddIndicatorModal');
  if (addIndicatorModal && IndicatorModal) {
    handleModal(
      addIndicatorModal,
      document.getElementById('AddIndicatorModalButton'), 
      addIndicatorModal.querySelector('.close')
    );
  }

  // Редактирование Direction
  const editDirectionModal = document.getElementById('EditDirectionModal');
  if (editDirectionModal) {
    handleModal(
      editDirectionModal, 
      document.getElementById('tableEditButton'), 
      editDirectionModal.querySelector('.close')
    );
    handleModal(
      editDirectionModal, 
      document.getElementById('contextEditButton'), 
      editDirectionModal.querySelector('.close')
    );
  }

  // Редактирование Event
  const editEventModal = document.getElementById('EditEventModal');
  const eventModal = new EventModal('EditEventModal');
  if (editEventModal && eventModal) {
    handleModal(
      editEventModal, 
      document.getElementById('tableEditButton'), 
      editEventModal.querySelector('.close')
    );
    handleModal(
      editEventModal, 
      document.getElementById('contextEditButton'), 
      editEventModal.querySelector('.close')
    );
  }
  
    // Редактирование Organizattion
  const orgUserModal = document.getElementById('orgUserModal');
  if (orgUserModal) {
    handleModal(
      orgUserModal, 
      document.getElementById('orgUserbutton'), 
      orgUserModal.querySelector('.close')
    );
  }

  // Редактирование Indicator
  const editIndicatorModal = document.getElementById('EditIndicatorModal');
  if (editIndicatorModal) {
    handleModal(
      editIndicatorModal, 
      document.getElementById('tableEditButton'), 
      editIndicatorModal.querySelector('.close')
    );
    handleModal(
      editIndicatorModal, 
      document.getElementById('contextEditButton'), 
      editIndicatorModal.querySelector('.close')
    );
  }

    const questions = document.querySelectorAll('.faq-question');
    questions.forEach(question => {
        question.addEventListener('click', function() {
            const allAnswers = document.querySelectorAll('.faq-answer');
            const allQuestions = document.querySelectorAll('.faq-question');
            if (this.classList.contains('active')) {
                const answer = this.nextElementSibling;
                answer.classList.remove('active');
                this.classList.remove('active');
                return;
            }

            allAnswers.forEach(answer => {
                answer.classList.remove('active');
            });
            
            allQuestions.forEach(q => {
                q.classList.remove('active');
            });
            
            const answer = this.nextElementSibling;
            answer.classList.add('active');
            this.classList.add('active');
        });
    });

    //edit profile
    if (document.getElementById('editprofileButton')) {
        initConfirmModal({
            triggerId: 'editprofileButton',
            formId: 'editprofileForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите отредактировать данные профиля?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'Все несохраненные изменения будут потеряны.'
        });
    }

    //logout
    if (document.getElementById('logoutButton')) {
        initConfirmModal({
            triggerId: 'logoutButton',
            formId: 'logout_form',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите выйти из системы РеспондентаS?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'Все несохраненные изменения будут потеряны. Убедитесь, что вы сохранили свою работу.'
        });
    }

    //deletePlan
    if (document.querySelector('[data-modal-trigger="deletePlan"]')) {
        initConfirmModal({
            triggerButton: '[data-modal-trigger="deletePlan"]',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите удалить план #{id}?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'Все несохраненные изменения будут потеряны.'
        });
    }

    //edit plan
    if (document.getElementById('editPlanButton')) {
        initConfirmModal({
            triggerId: 'editPlanButton',
            formId: 'editPlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите отредактировать данные плана?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'Все несохраненные изменения будут потеряны.'
        });
    }

    //control plan
    if (document.getElementById('controlPlanButton')) {
        initConfirmModal({
            triggerId: 'controlPlanButton',
            formId: 'controlPlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите пройти контроль?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'Все несохраненные изменения будут потеряны. План сменит статус.'
        });
    }

    //sent plan
    if (document.getElementById('sentPlanButton')) {
        initConfirmModal({
            triggerId: 'sentPlanButton',
            formId: 'sentPlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите отправить план на проверку?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'План сменит статус и на время проверки его нельзя будет редактировать.'
        });
    }

    //sent audit message plan
    if (document.getElementById('sent_mesPlanButton')) {
        initConfirmModal({
            triggerId: 'sent_mesPlanButton',
            formId: 'sent_mesPlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите отправить сообщение об ошибках пользователю?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'Описывайте ошибки максимально подробно, для наилучшего восприятия со стороны пользователя.'
        });
    }

    //to_delete plan
    if (document.getElementById('to_deletePlanButton')) {
        initConfirmModal({
            triggerId: 'to_deletePlanButton',
            formId: 'to_deletePlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите сменить статус плана на "Есть ошибки"?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'План сменит статус для последующего исправления ошибок.'
        });
    }

    //confirm plan
    if (document.getElementById('confirmPlanButton')) {
        initConfirmModal({
            triggerId: 'confirmPlanButton',
            formId: 'confirmPlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите одобрить план?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'План сменит статус и не будет подлежать последующей редакции или удалению со всех сторон.'
        });
    }

    //cancel_audit plan
    if (document.getElementById('cancel_auditPlanButton')) {
        initConfirmModal({
            triggerId: 'cancel_auditPlanButton',
            formId: 'cancel_auditPlanForm',
            modalId: 'confirmModal2',
            yesId: 'confirmYes',
            noId: 'confirmNo',
            textId: 'modal-text',
            modalText: 'Вы действительно хотите отменить изменения в статусе плана?',
            textSecondId: 'modal-text-second',
            modalTextSecond: 'План сменит статус обратно на "Не просмотренный". Отменить изменния можно только в течении 1-го часа.'
        });
    }

    if (tickets_conteiner = document.querySelector('.tickets-conteiner')) {
        function customSmoothScroll(element, targetPosition, duration = 800) {
            if (!element) return;
            
            const startPosition = element.scrollTop;
            const distance = targetPosition - startPosition;
            let startTime = null;

            function animation(currentTime) {
                if (startTime === null) startTime = currentTime;
                const timeElapsed = currentTime - startTime;
                const progress = Math.min(timeElapsed / duration, 1);
                
                const ease = progress < 0.5 
                    ? 4 * progress * progress * progress 
                    : 1 - Math.pow(-2 * progress + 2, 3) / 2;
                
                element.scrollTop = startPosition + distance * ease;
                
                if (timeElapsed < duration) {
                    requestAnimationFrame(animation);
                }
            }

            requestAnimationFrame(animation);
        }
        
        customSmoothScroll(tickets_conteiner, tickets_conteiner.scrollHeight);
        
    }

    if(document.getElementById('orgUserbutton')){
        const orgSearchManager = new OrganizationSearchManager();
    }

   
    const triggerSideBar = document.getElementById("user-info-trigger");
    const sidebarUser = document.getElementById("user-sidebar");

    triggerSideBar.addEventListener("click", (e) => {
        e.stopPropagation();
        sidebarUser.classList.add("show");
    });

    document.addEventListener("click", (e) => {
        if (!sidebarUser.contains(e.target) && !triggerSideBar.contains(e.target)) {
        sidebarUser.classList.remove("show");
        }
    });
    
    if (document.getElementById('exportForm')) {
        initExportPage();
    }


    if (document.querySelectorAll('.plan-cont')) {
        initPlansFilter();
    }
 


    NotificationPopup.init({
        button: "#notifBtn",
        popup: "#notifPopup"
    });

    Notifications.init();
    setInterval(() => {
        Notifications.init();
    }, 60000);
});