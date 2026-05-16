export const formatGb = (value: number) => `${value.toFixed(value >= 10 ? 1 : 2)} GB`;

export const statusMeta = {
  good: { icon: '🟢', label: 'Хорошо', className: 'status-good' },
  ok: { icon: '🟡', label: 'Нормально', className: 'status-ok' },
  slow: { icon: '🟠', label: 'Через offload', className: 'status-slow' },
  bad: { icon: '🔴', label: 'Не надо', className: 'status-bad' },
} as const;
