import { useState, useEffect } from 'react';
import { loadAISettings, saveAISettings, checkOllaBridgeHealth, pairWithOllaBridge } from '../../services/ollabridgeService';

const AISettingsModal = ({ isOpen, onClose, onSettingsChange }) => {
  const [settings, setSettings] = useState(loadAISettings());
  const [bridgeStatus, setBridgeStatus] = useState(null); // null | 'checking' | { available, models, error }
  const [pairingCode, setPairingCode] = useState('');
  const [pairingStatus, setPairingStatus] = useState(null); // null | 'pairing' | 'success' | 'error'
  const [pairingError, setPairingError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setSettings(loadAISettings());
      setSaved(false);
    }
  }, [isOpen]);

  const updateSettings = (path, value) => {
    setSettings(prev => {
      const next = { ...prev };
      if (path.startsWith('ollabridge.')) {
        const key = path.replace('ollabridge.', '');
        next.ollabridge = { ...prev.ollabridge, [key]: value };
      } else {
        next[path] = value;
      }
      return next;
    });
    setSaved(false);
  };

  const handleSave = () => {
    saveAISettings(settings);
    setSaved(true);
    onSettingsChange?.(settings);
    setTimeout(() => onClose(), 600);
  };

  const handleTestConnection = async () => {
    setBridgeStatus('checking');
    const result = await checkOllaBridgeHealth(settings);
    setBridgeStatus(result);
  };

  const handlePair = async () => {
    if (!pairingCode.trim()) return;
    setPairingStatus('pairing');
    setPairingError('');
    try {
      const result = await pairWithOllaBridge(pairingCode, settings);
      updateSettings('ollabridge.pair_token', result.token);
      updateSettings('ollabridge.auth_mode', 'pairing');
      setPairingStatus('success');
      setPairingCode('');
    } catch (err) {
      setPairingStatus('error');
      setPairingError(err.message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                <i className="fas fa-cog text-white text-xl"></i>
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">AI Settings</h2>
                <p className="text-purple-200 text-xs">Configure your AI backend</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white hover:text-purple-200 text-xl">
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">AI Provider</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'auto', label: 'Auto', icon: 'fa-magic', desc: 'Ollama first, then Cloud' },
                { value: 'ollama', label: 'Ollama', icon: 'fa-server', desc: 'Local only' },
                { value: 'ollabridge', label: 'OllaBridge', icon: 'fa-cloud', desc: 'Cloud only' },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => updateSettings('provider', opt.value)}
                  className={`p-3 rounded-xl border-2 text-center transition-all ${
                    settings.provider === opt.value
                      ? 'border-purple-500 bg-purple-50 shadow-sm'
                      : 'border-gray-200 hover:border-purple-300'
                  }`}
                >
                  <i className={`fas ${opt.icon} text-lg ${
                    settings.provider === opt.value ? 'text-purple-600' : 'text-gray-400'
                  }`}></i>
                  <div className="text-xs font-semibold mt-1">{opt.label}</div>
                  <div className="text-[10px] text-gray-500">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* OllaBridge Cloud Settings */}
          {(settings.provider === 'ollabridge' || settings.provider === 'auto') && (
            <div className="bg-gray-50 rounded-xl p-4 space-y-4">
              <div className="flex items-center space-x-2">
                <i className="fas fa-cloud text-purple-600"></i>
                <h3 className="text-sm font-bold text-gray-800">OllaBridge Cloud</h3>
              </div>

              {/* Base URL */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Base URL</label>
                <input
                  type="text"
                  value={settings.ollabridge.base_url}
                  onChange={(e) => updateSettings('ollabridge.base_url', e.target.value)}
                  placeholder="https://ruslanmv-ollabridge.hf.space"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
                />
              </div>

              {/* Model */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Model</label>
                <input
                  type="text"
                  value={settings.ollabridge.model}
                  onChange={(e) => updateSettings('ollabridge.model', e.target.value)}
                  placeholder="qwen2.5:1.5b"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
                />
                {bridgeStatus?.available && bridgeStatus.models?.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {bridgeStatus.models.slice(0, 8).map(m => (
                      <button
                        key={m}
                        onClick={() => updateSettings('ollabridge.model', m)}
                        className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                          settings.ollabridge.model === m
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-200 text-gray-600 hover:bg-purple-100'
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Authentication */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">Authentication</label>
                <div className="flex gap-2 mb-2">
                  {['none', 'apikey', 'pairing'].map(mode => (
                    <button
                      key={mode}
                      onClick={() => updateSettings('ollabridge.auth_mode', mode)}
                      className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                        settings.ollabridge.auth_mode === mode
                          ? 'border-purple-500 bg-purple-50 text-purple-700'
                          : 'border-gray-300 text-gray-600 hover:border-purple-300'
                      }`}
                    >
                      {mode === 'none' ? 'No Auth' : mode === 'apikey' ? 'API Key' : 'Device Pairing'}
                    </button>
                  ))}
                </div>

                {settings.ollabridge.auth_mode === 'apikey' && (
                  <input
                    type="password"
                    value={settings.ollabridge.api_key}
                    onChange={(e) => updateSettings('ollabridge.api_key', e.target.value)}
                    placeholder="Enter API Key"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
                  />
                )}

                {settings.ollabridge.auth_mode === 'pairing' && (
                  <div className="space-y-2">
                    {settings.ollabridge.pair_token ? (
                      <div className="flex items-center space-x-2 bg-green-50 border border-green-200 rounded-lg p-2">
                        <i className="fas fa-check-circle text-green-600"></i>
                        <span className="text-xs text-green-700 font-medium">Device paired</span>
                        <button
                          onClick={() => updateSettings('ollabridge.pair_token', '')}
                          className="ml-auto text-xs text-red-600 hover:text-red-800"
                        >
                          Unpair
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={pairingCode}
                          onChange={(e) => setPairingCode(e.target.value)}
                          placeholder="Enter pairing code"
                          maxLength={10}
                          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none uppercase tracking-wider"
                        />
                        <button
                          onClick={handlePair}
                          disabled={pairingStatus === 'pairing'}
                          className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                          {pairingStatus === 'pairing' ? (
                            <i className="fas fa-spinner fa-spin"></i>
                          ) : 'Pair'}
                        </button>
                      </div>
                    )}
                    {pairingStatus === 'success' && (
                      <p className="text-xs text-green-600">Paired successfully!</p>
                    )}
                    {pairingStatus === 'error' && (
                      <p className="text-xs text-red-600">{pairingError}</p>
                    )}
                  </div>
                )}
              </div>

              {/* Test Connection */}
              <div className="pt-2">
                <button
                  onClick={handleTestConnection}
                  disabled={bridgeStatus === 'checking'}
                  className="w-full px-4 py-2 border-2 border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 text-sm font-medium disabled:opacity-50 transition-colors"
                >
                  {bridgeStatus === 'checking' ? (
                    <><i className="fas fa-spinner fa-spin mr-2"></i>Testing...</>
                  ) : (
                    <><i className="fas fa-plug mr-2"></i>Test Connection</>
                  )}
                </button>
                {bridgeStatus && bridgeStatus !== 'checking' && (
                  <div className={`mt-2 p-2 rounded-lg text-xs ${
                    bridgeStatus.available
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-red-50 text-red-700 border border-red-200'
                  }`}>
                    {bridgeStatus.available ? (
                      <><i className="fas fa-check-circle mr-1"></i>Connected! {bridgeStatus.models?.length || 0} models available</>
                    ) : (
                      <><i className="fas fa-times-circle mr-1"></i>Connection failed: {bridgeStatus.error}</>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Info box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <i className="fas fa-info-circle text-blue-500 mt-0.5"></i>
              <div className="text-xs text-blue-700">
                <p className="font-semibold mb-1">How it works:</p>
                <ul className="space-y-0.5 list-disc list-inside">
                  <li><b>Auto:</b> Tries local Ollama tutor first, falls back to OllaBridge Cloud</li>
                  <li><b>Ollama:</b> Uses only the local Ollama backend (requires <code className="bg-blue-100 px-1 rounded">make tutor-server</code>)</li>
                  <li><b>OllaBridge:</b> Uses OllaBridge Cloud on HuggingFace Spaces (works on Vercel)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium flex items-center"
          >
            {saved ? (
              <><i className="fas fa-check mr-2"></i>Saved!</>
            ) : (
              <><i className="fas fa-save mr-2"></i>Save Settings</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AISettingsModal;
