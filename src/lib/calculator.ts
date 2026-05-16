import type { HardwareProfile } from '../data/hardware';
import type { LlmModel, UseCase } from '../data/models';
import { llmModels } from '../data/models';
import { quantizationProfiles, type QuantizationProfile } from '../data/quantization';

export type Preference = 'fast' | 'balanced' | 'quality' | 'just-run';

export type MatchStatus = 'good' | 'ok' | 'slow' | 'bad';

export type MatchResult = {
  id: string;
  model: LlmModel;
  quant: QuantizationProfile;
  status: MatchStatus;
  contextK: number;
  estimatedMemoryGb: number;
  usableMemoryGb: number;
  offloadGb: number;
  score: number;
  speedLabel: string;
  summary: string;
  command?: string;
};

const preferenceToUseCase: Record<Preference, UseCase> = {
  fast: 'fast',
  balanced: 'chat',
  quality: 'smartest',
  'just-run': 'chat',
};

const contextMemoryGb = (contextK: number, parametersB: number) =>
  0.45 + (contextK / 8) * Math.max(0.35, Math.sqrt(parametersB) * 0.18);

export const estimateModelMemoryGb = (parametersB: number, bitsPerWeight: number, contextK: number) => {
  const weightGb = (parametersB * bitsPerWeight) / 8;
  const runtimeOverheadGb = Math.max(0.45, weightGb * 0.09);
  return weightGb + contextMemoryGb(contextK, parametersB) + runtimeOverheadGb;
};

export const getUsableMemoryGb = (hardware: HardwareProfile, selectedMemoryGb: number, ramGb: number) => {
  if (hardware.memoryKind === 'vram') {
    return {
      primary: selectedMemoryGb * 0.88,
      totalWithOffload: selectedMemoryGb * 0.88 + Math.max(0, ramGb - 8) * 0.65,
    };
  }

  if (hardware.memoryKind === 'unified') {
    return {
      primary: selectedMemoryGb * 0.7,
      totalWithOffload: selectedMemoryGb * 0.78,
    };
  }

  if (hardware.memoryKind === 'shared') {
    return {
      primary: selectedMemoryGb * 0.55,
      totalWithOffload: selectedMemoryGb * 0.65,
    };
  }

  return {
    primary: Math.max(0, selectedMemoryGb - 5) * 0.75,
    totalWithOffload: Math.max(0, selectedMemoryGb - 5) * 0.75,
  };
};

const getStatus = (estimatedMemoryGb: number, primaryMemoryGb: number, totalMemoryGb: number): MatchStatus => {
  if (estimatedMemoryGb <= primaryMemoryGb * 0.82) return 'good';
  if (estimatedMemoryGb <= primaryMemoryGb) return 'ok';
  if (estimatedMemoryGb <= totalMemoryGb) return 'slow';
  return 'bad';
};

const getSpeedLabel = (status: MatchStatus, hardware: HardwareProfile, parametersB: number) => {
  if (status === 'bad') return 'не рекомендуется';
  if (hardware.accelerator === 'cpu') return parametersB <= 8 ? 'медленно, но терпимо' : 'очень медленно';
  if (status === 'slow') return 'медленно из-за offload';
  if (parametersB <= 8 && status === 'good') return 'быстро для этого класса';
  if (parametersB <= 14) return 'нормально';
  return 'спокойно, не мгновенно';
};

const statusSummary: Record<MatchStatus, string> = {
  good: 'Запустится нормально. Это хороший выбор для твоего железа.',
  ok: 'Запустится, но запас небольшой. Лучше закрыть лишние приложения.',
  slow: 'Запустится через GPU + RAM/CPU offload, но будет заметно медленнее.',
  bad: 'Не рекомендуется для этой конфигурации.',
};

const quantAllowedForPreference = (preference: Preference, quant: QuantizationProfile) => {
  if (preference === 'quality') return !['emergency', 'last-chance'].includes(quant.tier);
  if (preference === 'fast') return ['balanced', 'tight', 'high'].includes(quant.tier);
  if (preference === 'just-run') return true;
  return !['last-chance'].includes(quant.tier);
};

const preferenceWeight = (preference: Preference, quant: QuantizationProfile) => {
  if (preference === 'quality') return quant.qualityRank * 1.25;
  if (preference === 'fast') return quant.tier === 'balanced' || quant.tier === 'tight' ? quant.qualityRank + 12 : quant.qualityRank;
  if (preference === 'just-run') return quant.tier === 'emergency' || quant.tier === 'last-chance' ? quant.qualityRank + 18 : quant.qualityRank;
  return quant.qualityRank;
};

export const calculateMatches = ({
  hardware,
  selectedMemoryGb,
  ramGb,
  preference,
  requestedContextK,
}: {
  hardware: HardwareProfile;
  selectedMemoryGb: number;
  ramGb: number;
  preference: Preference;
  requestedContextK: number;
}): MatchResult[] => {
  const memory = getUsableMemoryGb(hardware, selectedMemoryGb, ramGb);
  const useCase = preferenceToUseCase[preference];

  return llmModels
    .flatMap((model) => {
      const contextK = Math.min(requestedContextK, model.maxContextK);
      return quantizationProfiles
        .filter((quant) => quantAllowedForPreference(preference, quant))
        .map((quant) => {
          const estimatedMemoryGb = estimateModelMemoryGb(model.parametersB, quant.bitsPerWeight, contextK);
          const status = getStatus(estimatedMemoryGb, memory.primary, memory.totalWithOffload);
          const useCaseBonus = model.strengths.includes(useCase) ? 18 : 0;
          const statusBonus = status === 'good' ? 45 : status === 'ok' ? 28 : status === 'slow' ? 8 : -90;
          const offloadGb = Math.max(0, estimatedMemoryGb - memory.primary);
          const score =
            statusBonus +
            useCaseBonus +
            preferenceWeight(preference, quant) +
            Math.min(model.parametersB, 34) -
            Math.max(0, estimatedMemoryGb - memory.primary) * 5;

          return {
            id: `${model.id}-${quant.id}`,
            model,
            quant,
            status,
            contextK,
            estimatedMemoryGb,
            usableMemoryGb: memory.primary,
            offloadGb,
            score,
            speedLabel: getSpeedLabel(status, hardware, model.parametersB),
            summary: statusSummary[status],
            command: model.ollamaName ? `ollama run ${model.ollamaName}` : undefined,
          } satisfies MatchResult;
        });
    })
    .sort((a, b) => b.score - a.score)
    .filter((result, index, all) => all.findIndex((item) => item.model.id === result.model.id) === index)
    .slice(0, 6);
};
