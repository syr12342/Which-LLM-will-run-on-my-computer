import { useMemo, useState } from 'react';
import { ArrowRight, Cpu, Download, Monitor, Sparkles, Terminal } from 'lucide-react';
import { deviceTypeLabels, hardwareProfiles, type DeviceType } from './data/hardware';
import { calculateMatches, type Preference } from './lib/calculator';
import { formatGb, statusMeta } from './lib/format';

const deviceTypes: DeviceType[] = ['windows', 'mac', 'linux', 'handheld', 'iphone-ipad', 'android', 'cpu-only'];
const preferences: Array<{ id: Preference; label: string; description: string }> = [
  { id: 'fast', label: 'Быстро', description: 'легче, отзывчивее' },
  { id: 'balanced', label: 'Баланс', description: 'лучший default' },
  { id: 'quality', label: 'Максимум качества', description: 'умнее, тяжелее' },
  { id: 'just-run', label: 'Лишь бы запустить', description: 'IQ/Q2 допускаются' },
];
const contexts = [4, 8, 16, 32, 64, 128];
const ramOptions = [8, 16, 24, 32, 48, 64, 96, 128];

function App() {
  const [deviceType, setDeviceType] = useState<DeviceType>('windows');
  const availableHardware = useMemo(
    () => hardwareProfiles.filter((profile) => profile.deviceTypes.includes(deviceType)),
    [deviceType],
  );
  const [hardwareId, setHardwareId] = useState('rtx-3060');
  const selectedHardware = availableHardware.find((profile) => profile.id === hardwareId) ?? availableHardware[0];
  const [selectedMemoryGb, setSelectedMemoryGb] = useState(selectedHardware.defaultMemoryGb);
  const [ramGb, setRamGb] = useState(32);
  const [preference, setPreference] = useState<Preference>('balanced');
  const [contextK, setContextK] = useState(16);

  const chooseDeviceType = (nextType: DeviceType) => {
    const nextHardware = hardwareProfiles.find((profile) => profile.deviceTypes.includes(nextType));
    setDeviceType(nextType);
    if (nextHardware) {
      setHardwareId(nextHardware.id);
      setSelectedMemoryGb(nextHardware.defaultMemoryGb);
      setRamGb(nextHardware.memoryKind === 'ram' ? nextHardware.defaultMemoryGb : 32);
    }
  };

  const chooseHardware = (nextId: string) => {
    const nextHardware = hardwareProfiles.find((profile) => profile.id === nextId);
    if (!nextHardware) return;
    setHardwareId(nextId);
    setSelectedMemoryGb(nextHardware.defaultMemoryGb);
    if (nextHardware.memoryKind === 'ram') setRamGb(nextHardware.defaultMemoryGb);
  };

  const matches = useMemo(
    () =>
      calculateMatches({
        hardware: selectedHardware,
        selectedMemoryGb,
        ramGb,
        preference,
        requestedContextK: contextK,
      }),
    [contextK, preference, ramGb, selectedHardware, selectedMemoryGb],
  );

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="eyebrow">
          <Sparkles size={16} />
          LLM Hardware Matcher
        </div>
        <div className="hero-grid">
          <div>
            <h1>Какие локальные нейросети запустятся у тебя?</h1>
            <p>
              Выбери устройство, память и режим. Сервис даст короткий список моделей, объяснит запас памяти и покажет
              простой запуск через Ollama или LM Studio.
            </p>
          </div>
          <div className="hero-note">
            <Monitor size={22} />
            <span>Без регистрации, backend и инженерной таблицы. Только понятный ответ: что выбрать и как открыть.</span>
          </div>
        </div>
      </section>

      <section className="workspace">
        <aside className="panel controls" aria-label="Настройки железа">
          <div className="panel-heading">
            <Cpu size={20} />
            <h2>Железо</h2>
          </div>

          <label className="field-label">Тип устройства</label>
          <div className="segmented device-grid">
            {deviceTypes.map((type) => (
              <button
                className={type === deviceType ? 'selected' : ''}
                key={type}
                onClick={() => chooseDeviceType(type)}
                type="button"
              >
                {deviceTypeLabels[type]}
              </button>
            ))}
          </div>

          <label className="field-label" htmlFor="hardware-select">
            Модель
          </label>
          <select id="hardware-select" value={selectedHardware.id} onChange={(event) => chooseHardware(event.target.value)}>
            {availableHardware.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.displayName}
              </option>
            ))}
          </select>

          <label className="field-label">{selectedHardware.memoryKind === 'vram' ? 'VRAM' : 'Память'}</label>
          <div className="segmented">
            {selectedHardware.memoryOptionsGb.map((memory) => (
              <button
                className={memory === selectedMemoryGb ? 'selected' : ''}
                key={memory}
                onClick={() => setSelectedMemoryGb(memory)}
                type="button"
              >
                {memory} GB
              </button>
            ))}
          </div>

          {selectedHardware.memoryKind === 'vram' && (
            <>
              <label className="field-label">RAM для offload</label>
              <div className="segmented compact">
                {ramOptions.map((ram) => (
                  <button className={ram === ramGb ? 'selected' : ''} key={ram} onClick={() => setRamGb(ram)} type="button">
                    {ram}
                  </button>
                ))}
              </div>
            </>
          )}

          <label className="field-label">Режим</label>
          <div className="mode-list">
            {preferences.map((item) => (
              <button
                className={item.id === preference ? 'mode-card selected' : 'mode-card'}
                key={item.id}
                onClick={() => setPreference(item.id)}
                type="button"
              >
                <strong>{item.label}</strong>
                <span>{item.description}</span>
              </button>
            ))}
          </div>

          <label className="field-label">Контекст</label>
          <div className="segmented compact">
            {contexts.map((context) => (
              <button
                className={context === contextK ? 'selected' : ''}
                key={context}
                onClick={() => setContextK(context)}
                type="button"
              >
                {context}k
              </button>
            ))}
          </div>

          {selectedHardware.notes && <p className="soft-warning">{selectedHardware.notes}</p>}
        </aside>

        <section className="results">
          <div className="results-header">
            <div>
              <span className="eyebrow muted">Лучшее для</span>
              <h2>
                {selectedHardware.displayName} · {selectedMemoryGb} GB
              </h2>
            </div>
            <a className="ghost-link" href="https://lmstudio.ai/" rel="noreferrer" target="_blank">
              LM Studio <ArrowRight size={16} />
            </a>
          </div>

          <div className="cards">
            {matches.map((match) => {
              const meta = statusMeta[match.status];
              return (
                <article className={`result-card ${meta.className}`} key={match.id}>
                  <div className="status-row">
                    <span className="status-pill">
                      {meta.icon} {meta.label}
                    </span>
                    <span>{match.speedLabel}</span>
                  </div>

                  <div className="model-title">
                    <h3>{match.model.name}</h3>
                    <span>{match.quant.label}</span>
                  </div>

                  <p>{match.summary}</p>

                  <dl className="metric-grid">
                    <div>
                      <dt>Контекст</dt>
                      <dd>{match.contextK}k</dd>
                    </div>
                    <div>
                      <dt>Память</dt>
                      <dd>{formatGb(match.estimatedMemoryGb)}</dd>
                    </div>
                    <div>
                      <dt>Запас</dt>
                      <dd>{formatGb(match.usableMemoryGb)}</dd>
                    </div>
                    <div>
                      <dt>Offload</dt>
                      <dd>{match.offloadGb > 0 ? formatGb(match.offloadGb) : 'не нужен'}</dd>
                    </div>
                  </dl>

                  <p className="model-note">{match.model.notes} {match.quant.description}</p>

                  <div className="launch-box">
                    <div>
                      <Terminal size={16} />
                      <code>{match.command ?? `Найди “${match.model.lmStudioQuery}” в LM Studio`}</code>
                    </div>
                    <a href="https://ollama.com/library" rel="noreferrer" target="_blank">
                      <Download size={16} /> Ollama library
                    </a>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      </section>
    </main>
  );
}

export default App;
