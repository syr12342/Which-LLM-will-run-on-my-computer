export type UseCase = 'chat' | 'coding' | 'long-context' | 'smartest' | 'fast';

export type LlmModel = {
  id: string;
  name: string;
  family: string;
  parametersB: number;
  defaultContextK: number;
  maxContextK: number;
  ollamaName?: string;
  lmStudioQuery: string;
  strengths: UseCase[];
  notes: string;
};

export const llmModels: LlmModel[] = [
  {
    id: 'qwen2.5-3b',
    name: 'Qwen2.5 3B',
    family: 'Qwen',
    parametersB: 3,
    defaultContextK: 16,
    maxContextK: 32,
    ollamaName: 'qwen2.5:3b',
    lmStudioQuery: 'Qwen2.5 3B GGUF',
    strengths: ['chat', 'fast'],
    notes: 'Быстрая компактная модель для слабого железа.',
  },
  {
    id: 'llama3.1-8b',
    name: 'Llama 3.1 8B',
    family: 'Llama',
    parametersB: 8,
    defaultContextK: 16,
    maxContextK: 128,
    ollamaName: 'llama3.1:8b',
    lmStudioQuery: 'Llama 3.1 8B Instruct GGUF',
    strengths: ['chat', 'long-context'],
    notes: 'Хороший универсальный баланс.',
  },
  {
    id: 'qwen2.5-7b',
    name: 'Qwen2.5 7B',
    family: 'Qwen',
    parametersB: 7,
    defaultContextK: 16,
    maxContextK: 32,
    ollamaName: 'qwen2.5:7b',
    lmStudioQuery: 'Qwen2.5 7B Instruct GGUF',
    strengths: ['chat', 'coding'],
    notes: 'Сильный маленький универсал.',
  },
  {
    id: 'deepseek-coder-6.7b',
    name: 'DeepSeek Coder 6.7B',
    family: 'DeepSeek',
    parametersB: 6.7,
    defaultContextK: 16,
    maxContextK: 16,
    ollamaName: 'deepseek-coder:6.7b',
    lmStudioQuery: 'DeepSeek Coder 6.7B GGUF',
    strengths: ['coding'],
    notes: 'Практичный вариант для кода на обычном ПК.',
  },
  {
    id: 'qwen2.5-14b',
    name: 'Qwen2.5 14B',
    family: 'Qwen',
    parametersB: 14,
    defaultContextK: 8,
    maxContextK: 32,
    ollamaName: 'qwen2.5:14b',
    lmStudioQuery: 'Qwen2.5 14B Instruct GGUF',
    strengths: ['chat', 'coding', 'smartest'],
    notes: 'Заметно умнее 7B/8B, но требует больше памяти.',
  },
  {
    id: 'mistral-small-24b',
    name: 'Mistral Small 24B',
    family: 'Mistral',
    parametersB: 24,
    defaultContextK: 8,
    maxContextK: 32,
    ollamaName: 'mistral-small:24b',
    lmStudioQuery: 'Mistral Small 24B GGUF',
    strengths: ['chat', 'smartest'],
    notes: 'Хороший кандидат для 16-24 GB памяти.',
  },
  {
    id: 'qwen2.5-32b',
    name: 'Qwen2.5 32B',
    family: 'Qwen',
    parametersB: 32,
    defaultContextK: 8,
    maxContextK: 32,
    ollamaName: 'qwen2.5:32b',
    lmStudioQuery: 'Qwen2.5 32B Instruct GGUF',
    strengths: ['coding', 'smartest'],
    notes: 'Качественный вариант, часто требует offload в RAM.',
  },
  {
    id: 'llama3.3-70b',
    name: 'Llama 3.3 70B',
    family: 'Llama',
    parametersB: 70,
    defaultContextK: 8,
    maxContextK: 128,
    ollamaName: 'llama3.3:70b',
    lmStudioQuery: 'Llama 3.3 70B Instruct GGUF',
    strengths: ['smartest', 'long-context'],
    notes: 'Большая модель: домашнему ПК обычно нужна сильная компрессия или много RAM.',
  },
];
