# Product concept: LLM Hardware Matcher

## 0. Короткое решение

Делаем не «аналитическую платформу», а простой личный инструмент:

> Выбрал железо → увидел, какие LLM запустятся → выбрал Ollama или LM Studio → получил понятную команду/ссылку.

Цель — чтобы владелец проекта не возился с установкой, базами, парсерами и инженерной настройкой. Проект должен запускаться одной командой или одним кликом через готовый dev/prod-скрипт.

Стиль интерфейса: сдержанный, короткий, как Claude. Много воздуха, минимум шума, спокойные карточки, без «геймерского» UI.

---

## 1. Что важно владельцу проекта

### Нужно

- Простота.
- Личный pet project, но пригодный для других.
- Без регистрации, лайков, соцфункций и комьюнити на старте.
- Только два способа запуска моделей: **Ollama** и **LM Studio**.
- Большая база железа: NVIDIA, AMD, Intel, Apple Silicon, handheld PC, телефоны.
- Учет не только VRAM, но и сценария **GPU + CPU/RAM offload**.
- Поддержка не только Q4, но и всех «жестких» квантов: IQ1, IQ2, IQ3, IQ4, Q2, Q3 и т.д.
- Не полное название видеокарты, а простой выбор: `3060` → выбрать объем памяти → готово.

### Не нужно в MVP

- Автоопределение железа, если это усложняет запуск.
- vLLM, TensorRT-LLM, ExLlamaV2 как основной сценарий.
- Сложный backend.
- Пользовательские аккаунты.
- Краудсорсинг бенчмарков.
- Браузерное расширение.
- Мобильные deep technical фреймворки как основной UX.

---

## 2. Похожие проекты и выводы

Перед проектированием были найдены похожие решения:

- **CanItRun** — показывает, какие open-weight модели влезают в VRAM, учитывает квантизацию и примерную скорость.
- **RunThisModel** — делает проверку железа и совместимости AI-моделей, включая автоопределение GPU/VRAM.
- Разные VRAM/GGUF calculators — обычно требуют вставить ссылку на GGUF и руками выбрать контекст.

Вывод:

- Рынок уже подтверждает потребность.
- Отличаться надо не «самой умной формулой», а простотой.
- Главный фокус: **короткий ответ + инструкция запуска**, а не инженерная таблица.
- Автоопределение железа можно добавить позже. В MVP быстрее и надежнее ручной выбор.

---

## 3. Основной пользовательский сценарий

### Главный экран

```text
Какие локальные нейросети запустятся у тебя?

[Тип устройства]
  Windows PC
  Mac
  Linux PC
  Steam Deck / Handheld
  iPhone / iPad
  Android

[Железо]
  GPU: 3060
  VRAM: 12 GB
  RAM: 32 GB

[Режим]
  Быстро
  Баланс
  Максимум качества
  Лишь бы запустить

[Контекст]
  4k / 8k / 16k / 32k / 64k / 128k

[Показать модели]
```

### Результат

```text
Лучшее для RTX 3060 12GB

🟢 Qwen 7B — Q5_K_M
Пойдет хорошо. Контекст 16k. Ollama / LM Studio.

🟢 Llama 8B — Q4_K_M
Хороший баланс. Контекст 16k.

🟡 Qwen 14B — IQ3_M
Запустится, но лучше 8k и закрыть лишние приложения.

🟠 32B — IQ2_XXS
Только если очень нужно. Часть уйдет в RAM, будет медленно.

🔴 70B — Q4_K_M
Не рекомендуется для этой конфигурации.
```

---

## 4. Выбор видеокарты: не полное название, а модель + память

Пользователь не должен выбирать `MSI GeForce RTX 3060 Ventus 2X OC 12G`.

Правильный UX:

```text
NVIDIA
  1060
    3 GB / 6 GB
  1660
    6 GB
  2060
    6 GB / 12 GB
  3060
    8 GB / 12 GB
  4060
    8 GB
  4060 Ti
    8 GB / 16 GB
```

Внутри можно хранить нормализованный ID:

```json
{
  "vendor": "nvidia",
  "chip": "rtx-3060",
  "displayName": "RTX 3060",
  "memoryOptionsGb": [8, 12],
  "defaultMemoryGb": 12,
  "bandwidthByMemoryGb": {
    "8": 240,
    "12": 360
  }
}
```

Если у карты много OEM-вариантов, показываем только главное:

- модель;
- VRAM;
- примерная bandwidth;
- поколение;
- поддержка CUDA/ROCm/Metal/Vulkan.

---

## 5. Статусы совместимости

### 🟢 Хорошо

Модель помещается в быструю память с запасом.

Текст:

> Запустится нормально. Это хороший выбор для твоего железа.

### 🟡 Нормально

Помещается, но запас небольшой.

Текст:

> Запустится, но лучше не ставить слишком длинный контекст и закрыть лишние приложения.

### 🟠 С болью

Не помещается полностью в VRAM/Unified Memory. Нужен CPU/RAM offload.

Текст:

> Запустить можно, но часть модели уйдет в RAM. Будет заметно медленнее.

### 🔴 Не стоит

Недостаточно памяти или скорость будет бессмысленно низкой.

Текст:

> Не рекомендуем. Возьми модель меньше или более жесткий квант.

---

## 6. Важно: запуск бывает не только в видеокарте

Для локальных LLM надо учитывать три режима.

### 6.1 Полностью в VRAM

Лучший сценарий для NVIDIA/AMD/Intel GPU.

```text
model weights + KV cache + overhead <= usable VRAM
```

Плюсы:

- максимальная скорость;
- меньше лагов;
- проще объяснить пользователю.

Минусы:

- жесткое ограничение по VRAM.

### 6.2 Unified Memory

Для Mac и части мобильных устройств.

```text
model weights + KV cache + overhead <= safe unified memory
```

Особенность:

- память общая для CPU/GPU/системы;
- нельзя отдавать LLM все 100%;
- безопасный лимит надо считать как часть общей памяти.

Пример:

```text
Mac 16 GB → безопасно под LLM примерно 10-12 GB
Mac 32 GB → безопасно под LLM примерно 22-25 GB
Mac 64 GB → безопасно под LLM примерно 45-52 GB
```

### 6.3 GPU + CPU/RAM offload

Ключевая фича для обычных ПК.

Если модель не помещается целиком в VRAM, llama.cpp/Ollama/LM Studio могут держать часть слоев на GPU, часть в системной RAM.

```text
VRAM: быстрые слои
RAM: оставшиеся слои
```

Плюсы:

- можно запустить модель больше, чем VRAM;
- полезно для 8 GB / 12 GB карт.

Минусы:

- скорость резко падает;
- DDR4/DDR5 намного медленнее GDDR/HBM;
- длинный контекст ухудшает ситуацию.

UX-текст:

> Модель не влезает полностью в видеокарту. Можно запустить через CPU/RAM offload, но скорость будет ниже. Для комфортного использования лучше выбрать меньшую модель или квант.

---

## 7. Упрощенная формула MVP

MVP не должен пытаться быть идеальным. Он должен быть осторожным.

```text
required_memory = model_file_size + context_memory + runtime_overhead + safety_margin
```

На старте:

```text
runtime_overhead = max(0.7 GB, model_file_size * 0.08)
safety_margin = 10-15%
```

Контекстный запас для MVP:

| Context | Extra memory estimate |
|---:|---:|
| 4k | +0.5 GB |
| 8k | +1 GB |
| 16k | +2 GB |
| 32k | +4 GB |
| 64k | +8 GB |
| 128k | +16 GB |

Позже заменить на расчет KV-cache по архитектуре:

- layers;
- hidden size;
- attention heads;
- key/value heads;
- MHA/GQA/MQA;
- KV dtype;
- batch size.

---

## 8. Кванты, которые надо поддерживать

Нельзя ограничиваться Q4.

### GGUF / llama.cpp / Ollama / LM Studio

| Quant | UX tier | Комментарий |
|---|---|---|
| F16 / BF16 | Максимум | Очень тяжелый вариант. Только много памяти. |
| Q8_0 | Почти максимум | Хорошее качество, большой размер. |
| Q6_K | Высокое качество | Если памяти достаточно. |
| Q5_K_M | Качество+ | Часто лучше Q4, если влезает. |
| Q5_K_S | Качество | Чуть легче Q5_K_M. |
| Q4_K_M | Баланс | Дефолтная рекомендация. |
| Q4_K_S | Баланс- | Чуть легче, немного хуже. |
| IQ4_NL | Экономный баланс | Хороший вариант для экономии. |
| IQ4_XS | Экономный баланс | Часто полезен для тесной VRAM. |
| Q3_K_L | Низкий средний | Когда Q4 уже тяжеловат. |
| Q3_K_M | Низкий средний | Компромисс. |
| Q3_K_S | Низкий | Еще легче. |
| IQ3_M | Низкий, но полезный | Хорош для слабого железа. |
| IQ3_S | Низкий | Еще легче. |
| IQ3_XS | Очень низкий | Когда памяти мало. |
| IQ3_XXS | Очень низкий | Экстремальный 3-bit. |
| Q2_K | Аварийный | Лишь бы запустить. |
| IQ2_M | Аварийный+ | Очень сильное сжатие. |
| IQ2_S | Аварийный | Слабое качество. |
| IQ2_XS | Аварийный | Для очень слабого железа. |
| IQ2_XXS | Экстремальный | Минимум памяти, заметная деградация. |
| IQ1_M | Последний шанс | «Анальный» квант: запуск важнее качества. |
| IQ1_S | Последний шанс | Еще жестче. |

UX-правило:

- По умолчанию показывать 3-5 лучших вариантов.
- Экстремальные IQ1/IQ2 показывать только в блоке «Лишь бы запустить».
- Всегда предупреждать, что качество может сильно просесть.

---

## 9. Форматы MVP

### Поддержать сразу

- GGUF.
- Ollama library names, если модель есть в Ollama.
- Hugging Face GGUF repos.

### Позже

- EXL2.
- GPTQ.
- AWQ.
- safetensors FP16/BF16.
- MLC mobile packages.

Причина: владелец проекта хочет только Ollama и LM Studio. Оба сценария проще всего закрываются GGUF/Ollama.

---

## 10. База железа: MVP должен быть шире обычного списка

Ниже не финальная база, а обязательный seed-list. В интерфейсе показывать короткие имена.

### 10.1 NVIDIA desktop/laptop

#### GTX / старые карты

- 1050 Ti — 4 GB
- 1060 — 3 / 6 GB
- 1070 — 8 GB
- 1070 Ti — 8 GB
- 1080 — 8 GB
- 1080 Ti — 11 GB
- 1650 — 4 GB
- 1650 Super — 4 GB
- 1660 — 6 GB
- 1660 Super — 6 GB
- 1660 Ti — 6 GB

#### RTX 20

- 2060 — 6 / 12 GB
- 2060 Super — 8 GB
- 2070 — 8 GB
- 2070 Super — 8 GB
- 2080 — 8 GB
- 2080 Super — 8 GB
- 2080 Ti — 11 GB

#### RTX 30

- 3050 — 6 / 8 GB
- 3060 — 8 / 12 GB
- 3060 Ti — 8 GB
- 3070 — 8 GB
- 3070 Ti — 8 GB
- 3080 — 10 / 12 GB
- 3080 Ti — 12 GB
- 3090 — 24 GB
- 3090 Ti — 24 GB

#### RTX 40

- 4050 Laptop — 6 GB
- 4060 Laptop — 8 GB
- 4060 — 8 GB
- 4060 Ti — 8 / 16 GB
- 4070 Laptop — 8 GB
- 4070 — 12 GB
- 4070 Super — 12 GB
- 4070 Ti — 12 GB
- 4070 Ti Super — 16 GB
- 4080 Laptop — 12 GB
- 4080 — 16 GB
- 4080 Super — 16 GB
- 4090 Laptop — 16 GB
- 4090 — 24 GB

#### RTX 50

- 5050 / 5050 Laptop — if present in source DB
- 5060 / 5060 Laptop — common 8 GB class
- 5060 Ti — 8 / 16 GB class
- 5070 / 5070 Laptop — 12 GB class
- 5070 Ti — 16 GB class
- 5080 — 16 GB class
- 5090 — 32 GB class

Примечание: для RTX 50 обязательно сверять VRAM по базе, потому что рынок и ноутбучные варианты быстро меняются.

#### NVIDIA workstation / datacenter

- Titan X / Xp — 12 GB
- Titan RTX — 24 GB
- RTX A2000 — 6 / 12 GB
- RTX A4000 — 16 GB
- RTX A4500 — 20 GB
- RTX A5000 — 24 GB
- RTX A6000 — 48 GB
- RTX 4000 Ada — 20 GB
- RTX 4500 Ada — 24 GB
- RTX 5000 Ada — 32 GB
- RTX 6000 Ada — 48 GB
- Tesla P40 — 24 GB
- Tesla V100 — 16 / 32 GB
- T4 — 16 GB
- A10 — 24 GB
- A16 — 16 GB per GPU class
- A40 — 48 GB
- A100 — 40 / 80 GB
- L4 — 24 GB
- L40 — 48 GB
- L40S — 48 GB
- H100 — 80 GB
- H200 — 141 GB
- B200 — 180 GB class

### 10.2 AMD Radeon desktop/laptop

#### RX 500 / Vega

- RX 570 — 4 / 8 GB
- RX 580 — 4 / 8 GB
- RX 590 — 8 GB
- Vega 56 — 8 GB
- Vega 64 — 8 GB
- Radeon VII — 16 GB

#### RX 5000

- RX 5500 XT — 4 / 8 GB
- RX 5600 XT — 6 GB
- RX 5700 — 8 GB
- RX 5700 XT — 8 GB

#### RX 6000

- RX 6400 — 4 GB
- RX 6500 XT — 4 / 8 GB
- RX 6600 — 8 GB
- RX 6600 XT — 8 GB
- RX 6650 XT — 8 GB
- RX 6700 — 10 GB
- RX 6700 XT — 12 GB
- RX 6750 XT — 12 GB
- RX 6800 — 16 GB
- RX 6800 XT — 16 GB
- RX 6900 XT — 16 GB
- RX 6950 XT — 16 GB

#### RX 7000

- RX 7600 — 8 GB
- RX 7600 XT — 16 GB
- RX 7700 XT — 12 GB
- RX 7800 XT — 16 GB
- RX 7900 GRE — 16 GB
- RX 7900 XT — 20 GB
- RX 7900 XTX — 24 GB

#### RX 9000 / newer RDNA

- RX 9060 class — verify exact VRAM
- RX 9070 class — verify exact VRAM
- RX 9070 XT class — verify exact VRAM

#### AMD workstation / datacenter

- Radeon Pro W6600 — 8 GB
- Radeon Pro W6800 — 32 GB
- Radeon Pro W7600 — 8 GB
- Radeon Pro W7700 — 16 GB
- Radeon Pro W7800 — 32 GB
- Radeon Pro W7900 — 48 GB
- Instinct MI50 — 16 / 32 GB
- Instinct MI100 — 32 GB
- Instinct MI210 — 64 GB
- Instinct MI250 / MI250X — 128 GB class
- Instinct MI300X — 192 GB
- Instinct MI325X — 256 GB class

UX-примечание:

- AMD поддерживать обязательно, но в подсказках писать спокойнее: «лучше LM Studio/llama.cpp с Vulkan/ROCm, совместимость зависит от драйверов».

### 10.3 Intel Arc / integrated

- Arc A310 — 4 GB
- Arc A380 — 6 GB
- Arc A580 — 8 GB
- Arc A750 — 8 GB
- Arc A770 — 8 / 16 GB
- Arc B570 — 10 GB class
- Arc B580 — 12 GB class
- Intel Iris Xe — shared memory
- Intel Core Ultra iGPU — shared memory

UX-примечание:

- Intel Arc можно показывать как «экспериментально/нормально для GGUF», но не обещать чудес.

### 10.4 Apple Silicon

Показывать не «GPU model», а Mac chip + unified memory.

#### M1

- M1 — 8 / 16 GB
- M1 Pro — 16 / 32 GB
- M1 Max — 32 / 64 GB
- M1 Ultra — 64 / 128 GB

#### M2

- M2 — 8 / 16 / 24 GB
- M2 Pro — 16 / 32 GB
- M2 Max — 32 / 64 / 96 GB
- M2 Ultra — 64 / 128 / 192 GB

#### M3

- M3 — 8 / 16 / 24 GB
- M3 Pro — 18 / 36 GB
- M3 Max — 36 / 48 / 64 / 96 / 128 GB
- M3 Ultra — if available in source DB

#### M4

- M4 — 8 / 16 / 24 / 32 GB class
- M4 Pro — 24 / 48 / 64 GB class
- M4 Max — 36 / 48 / 64 / 128 GB class
- M4 Ultra — verify exact configs

UX-примечание:

- Для Mac главный показатель — unified memory.
- Безопасно считать 65-80% от общей памяти под LLM.
- Ollama и LM Studio — основные варианты.

### 10.5 Handheld PC

- Steam Deck LCD — 16 GB unified LPDDR5
- Steam Deck OLED — 16 GB unified LPDDR5/LPDDR5-class
- ASUS ROG Ally Z1 — 16 GB unified
- ASUS ROG Ally Z1 Extreme — 16 GB unified
- ASUS ROG Ally X — 24 GB unified
- Lenovo Legion Go — 16 GB unified
- Lenovo Legion Go S — 16 / 32 GB class
- MSI Claw A1M — 16 GB unified
- MSI Claw 8 AI+ — 32 GB class
- AYANEO 2 / Geek / Kun — 16 / 32 / 64 GB variants
- GPD Win 4 / Win Max / Win Mini — 16 / 32 / 64 GB variants
- OneXPlayer / OneXFly — 16 / 32 / 64 GB variants

UX-примечание:

- Это не «VRAM», а общая память.
- Безопасный лимит для LLM часто 50-70%.
- Лучшие модели: 3B-8B, Q4/IQ4/IQ3.

### 10.6 iPhone / iPad

Показывать модель телефона и RAM class.

#### iPhone

- iPhone 12 / 12 mini — 4 GB class
- iPhone 12 Pro / Pro Max — 6 GB class
- iPhone 13 / mini — 4 GB class
- iPhone 13 Pro / Pro Max — 6 GB class
- iPhone 14 / Plus — 6 GB class
- iPhone 14 Pro / Pro Max — 6 GB class
- iPhone 15 / Plus — 6 GB class
- iPhone 15 Pro / Pro Max — 8 GB class
- iPhone 16 / Plus — 8 GB class
- iPhone 16 Pro / Pro Max — 8 GB class
- iPhone 16e — 8 GB class
- iPhone 17 / Air / Pro / Pro Max — verify exact RAM, likely 8-12 GB class depending model

#### iPad

- iPad mini A17 Pro — 8 GB class
- iPad Air M1/M2/M3 — 8 / 16 GB class
- iPad Pro M1 — 8 / 16 GB
- iPad Pro M2 — 8 / 16 GB
- iPad Pro M4 — 8 / 16 GB

UX-примечание:

- На iOS не обещать полноценный Ollama/LM Studio desktop flow.
- Для MVP телефоны можно показывать как справочный блок: «локально возможно через мобильные приложения, но основной проект оптимизирован под PC/Mac».
- Реалистичные модели: 1B-3B хорошо, 7B/8B только в сильном кванте и с ограниченным контекстом.

### 10.7 Android phones

Показывать не каждый SKU, а SoC + RAM class + популярные примеры.

#### Snapdragon flagship tiers

- Snapdragon 8 Gen 1 — 8 / 12 GB phones
- Snapdragon 8+ Gen 1 — 8 / 12 / 16 GB phones
- Snapdragon 8 Gen 2 — 8 / 12 / 16 GB phones
- Snapdragon 8 Gen 3 — 12 / 16 / 24 GB phones
- Snapdragon 8 Elite — 12 / 16 / 24 GB phones
- Snapdragon 8 Elite Gen 5 — 12 / 16 GB+ phones

#### MediaTek tiers

- Dimensity 9000 / 9000+ — 8 / 12 GB
- Dimensity 9200 / 9200+ — 8 / 12 / 16 GB
- Dimensity 9300 / 9300+ — 12 / 16 GB
- Dimensity 9400 / 9400+ — 12 / 16 GB
- Dimensity 9500 class — verify exact devices

#### Google Tensor

- Tensor G1 — 8 / 12 GB phones
- Tensor G2 — 8 / 12 GB phones
- Tensor G3 — 8 / 12 GB phones
- Tensor G4 — 12 / 16 GB phones
- Tensor G5 — verify exact devices

#### Popular Android examples

- Samsung Galaxy S23 / S23+ / S23 Ultra
- Samsung Galaxy S24 / S24+ / S24 Ultra
- Samsung Galaxy S25 / S25+ / S25 Ultra
- Samsung Galaxy S26 / S26+ / S26 Ultra
- Samsung Galaxy Z Fold 5 / 6 / 7
- Google Pixel 8 / 8 Pro
- Google Pixel 9 / 9 Pro / 9 Pro XL
- Google Pixel 10 class — verify exact RAM
- OnePlus 11 / 12 / 13 / 15
- Xiaomi 13 / 14 / 15 / 17 class
- Xiaomi Ultra models
- ASUS ROG Phone 7 / 8 / 9 / newer
- RedMagic 8 / 9 / 10 / 11 class
- iQOO 12 / 13 / 15 class
- vivo X100 / X200 / X300 class
- OPPO Find X7 / X8 / X9 class
- Honor Magic 5 / 6 / 7 / 8 class

UX-примечание:

- На Android показывать осторожно: тепловой троттлинг, разные драйверы, разные приложения.
- Хороший практичный диапазон: 1B-3B комфортно, 7B/8B только Q4/IQ3/IQ2 и не всегда приятно.

### 10.8 CPU-only profiles

Нужно добавить, потому что не у всех есть дискретная видеокарта.

- Old laptop CPU + 8 GB RAM
- Office PC + 16 GB RAM
- Gaming PC CPU + 32 GB RAM
- Workstation CPU + 64 GB RAM
- Workstation CPU + 128 GB RAM
- Dual Xeon / Threadripper + 128-256 GB RAM

UX-примечание:

- CPU-only — это «можно, но медленно».
- Хорошо для 1B-3B.
- 7B Q4 возможна, но скорость зависит от RAM bandwidth и CPU.
- 13B+ только если пользователь понимает, что будет медленно.

---

## 11. Модели для первого каталога

Не надо парсить весь Hugging Face. Для MVP достаточно curated list.

### Chat/general

- Llama 3.1 8B
- Llama 3.2 1B / 3B
- Llama 3.3 70B
- Qwen2.5 0.5B / 1.5B / 3B / 7B / 14B / 32B / 72B
- Qwen3 0.6B / 1.7B / 4B / 8B / 14B / 32B / 72B class
- Mistral 7B
- Mixtral 8x7B
- Gemma 2 2B / 9B / 27B
- Gemma 3 1B / 4B / 12B / 27B class
- Phi-3 Mini / Small / Medium
- Phi-4 Mini / Phi-4 class
- Yi 1.5 6B / 9B / 34B
- DeepSeek R1 Distill Qwen/Llama variants

### Coding

- Qwen2.5-Coder 1.5B / 3B / 7B / 14B / 32B
- DeepSeek-Coder V2 Lite
- Codestral 22B
- StarCoder2 3B / 7B / 15B
- CodeLlama 7B / 13B / 34B
- Magicoder / WizardCoder class models

### Small/mobile

- SmolLM / SmolLM2
- TinyLlama
- OpenELM
- Phi small models
- Gemma 1B/2B class
- Qwen 0.5B/1.5B/3B class

---

## 12. Карточка результата

```text
Qwen2.5 7B Instruct
Q4_K_M · GGUF

🟢 Хорошо
Память: нужно ~6.2 GB, доступно ~10.5 GB
Контекст: 16k нормально, 32k возможно
Скорость: примерно быстро для этого класса

Запуск:
[Ollama] [LM Studio]
```

### Если Ollama

```text
ollama run qwen2.5:7b
```

Если кастомный GGUF:

```text
1. Скачать GGUF
2. Создать Modelfile
3. ollama create my-model -f Modelfile
4. ollama run my-model
```

### Если LM Studio

```text
1. Открой LM Studio
2. Найди модель или вставь Hugging Face repo
3. Выбери файл GGUF
4. Нажми Download
5. Load model
```

---

## 13. Как ранжировать варианты

Порядок выдачи:

1. Лучший баланс качества и памяти.
2. Самый простой запуск через Ollama.
3. LM Studio GGUF, если Ollama-варианта нет.
4. Более качественный вариант, если память позволяет.
5. Экономный вариант, если памяти мало.
6. Экстремальные IQ-кванты только в отдельном блоке.

Дефолтные рекомендации:

| Ситуация | Рекомендация |
|---|---|
| Памяти много | Q5_K_M / Q6_K / Q8_0 |
| Обычный ПК | Q4_K_M |
| Тесно по VRAM | IQ4_XS / Q3_K_M / IQ3_M |
| Очень тесно | IQ2_XXS / Q2_K |
| Последний шанс | IQ1_M / IQ1_S |

---

## 14. Архитектура MVP

### Стартовая версия

```text
Static app
  data/hardware.json
  data/models.json
  src/calculator.ts
  src/ui
```

Без backend.

Преимущества:

- проще запустить;
- проще деплоить;
- можно положить на Vercel/Netlify/GitHub Pages;
- меньше мест, где все ломается.

### One-click для владельца проекта

Нужны скрипты:

```text
npm install
npm run dev
npm run build
npm run preview
```

Потом можно добавить:

```text
start-windows.bat
start-macos.command
start-linux.sh
```

Идеал:

- `start` сам ставит зависимости;
- запускает локальный сайт;
- открывает браузер.

---

## 15. Минимальная структура файлов

```text
README.md
package.json
src/
  app/
  components/
  data/
    hardware.ts
    models.ts
    quantization.ts
  lib/
    calculator.ts
    matching.ts
    format.ts
  styles/
    globals.css
docs/
  PRODUCT_CONCEPT.md
```

Для первого кода лучше TypeScript + Vite/React.

---

## 16. План реализации

### Phase 0 — Документ

- Зафиксировать концепт.
- Зафиксировать scope MVP.
- Зафиксировать список железа и квантов.

### Phase 1 — Статический прототип

- Vite + React.
- Один экран выбора железа.
- Карточки результатов.
- Статический список моделей.
- Статический список железа.
- Расчет памяти по упрощенной формуле.

### Phase 2 — Реальные инструкции

- Ollama команды.
- LM Studio инструкции.
- Hugging Face links.
- Modelfile для кастомных GGUF.

### Phase 3 — Большой каталог

- Больше GPU.
- Больше Mac.
- Больше телефонов.
- Больше моделей.
- Группировка по семействам.

### Phase 4 — Автоматизация

- Скрипты запуска одним кликом.
- Возможно desktop helper позже.
- Возможно Hugging Face parser позже.

---

## 17. Риски

### Главный риск

Слишком усложнить и не закончить.

Решение:

- Не делать backend до MVP.
- Не делать автоопределение до MVP.
- Не поддерживать все форматы до MVP.
- Не обещать точные tok/s.

### Риск по железу

Спеки меняются, ноутбучные GPU и телефоны имеют разные варианты.

Решение:

- Хранить модель + VRAM options.
- Для новых карт писать `verify exact VRAM`.
- Не показывать лишнюю уверенность.

### Риск по телефонам

Телефоны сильно зависят от ОС, температуры и приложений.

Решение:

- Показывать телефоны как справочный режим.
- Не обещать «летает».
- Рекомендовать маленькие модели.

---

## 18. Источники для дальнейшего наполнения базы

Похожие проекты:

- https://canitrun.dev/
- https://runthismodel.com/

Железо и популярность:

- https://store.steampowered.com/hwsurvey/videocard
- https://www.techpowerup.com/gpu-specs/
- https://www.steamdeck.com/tech/oled
- https://www.apple.com/mac-studio/specs/
- https://www.qualcomm.com/products/mobile/snapdragon/smartphones/snapdragon-8-series-mobile-platforms

Телефоны и рынок:

- https://www.counterpointresearch.com/
- https://www.gsmarena.com/
- https://www.notebookcheck.net/

LLM/runtime:

- https://ollama.com/library
- https://lmstudio.ai/
- https://huggingface.co/models
- https://github.com/ggerganov/llama.cpp

---

## 19. Финальное направление

Проект должен оставаться простым:

> Не «таблица для инженеров», а спокойный помощник: что выбрать, запустится ли, и как открыть в Ollama/LM Studio.

Если фича не помогает быстрее запустить модель — она не входит в MVP.
