export type QuantTier = 'maximum' | 'high' | 'balanced' | 'tight' | 'emergency' | 'last-chance';

export type QuantizationProfile = {
  id: string;
  label: string;
  bitsPerWeight: number;
  tier: QuantTier;
  qualityRank: number;
  description: string;
};

export const quantizationProfiles: QuantizationProfile[] = [
  { id: 'q8_0', label: 'Q8_0', bitsPerWeight: 8.5, tier: 'maximum', qualityRank: 98, description: 'Почти максимум качества, большой размер.' },
  { id: 'q6_k', label: 'Q6_K', bitsPerWeight: 6.8, tier: 'high', qualityRank: 92, description: 'Высокое качество, если памяти достаточно.' },
  { id: 'q5_k_m', label: 'Q5_K_M', bitsPerWeight: 5.8, tier: 'high', qualityRank: 86, description: 'Качество выше Q4 при умеренном размере.' },
  { id: 'q4_k_m', label: 'Q4_K_M', bitsPerWeight: 4.8, tier: 'balanced', qualityRank: 78, description: 'Дефолтный баланс качества и памяти.' },
  { id: 'iq4_xs', label: 'IQ4_XS', bitsPerWeight: 4.3, tier: 'tight', qualityRank: 70, description: 'Экономный вариант, когда VRAM тесная.' },
  { id: 'q3_k_m', label: 'Q3_K_M', bitsPerWeight: 3.9, tier: 'tight', qualityRank: 62, description: 'Компромисс для слабого железа.' },
  { id: 'iq3_m', label: 'IQ3_M', bitsPerWeight: 3.5, tier: 'tight', qualityRank: 58, description: 'Низкий, но полезный квант.' },
  { id: 'q2_k', label: 'Q2_K', bitsPerWeight: 3.0, tier: 'emergency', qualityRank: 42, description: 'Аварийный режим: запустить важнее качества.' },
  { id: 'iq2_xxs', label: 'IQ2_XXS', bitsPerWeight: 2.3, tier: 'emergency', qualityRank: 34, description: 'Экстремально мало памяти, заметная деградация.' },
  { id: 'iq1_m', label: 'IQ1_M', bitsPerWeight: 1.8, tier: 'last-chance', qualityRank: 18, description: 'Последний шанс, если важен сам факт запуска.' },
];
