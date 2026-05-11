import { useState, useRef, useEffect } from 'react';
import { Send, Eye, Sparkles } from 'lucide-react';
import { api } from '../lib/api';
import { formatTime } from '../lib/format';

const SUGGESTIONS = [
  '📊 ¿Cómo viene marzo comparado con febrero?',
  '💸 ¿Cuánto gasté en materia prima este mes?',
  '📈 Proyección de ingresos próximos 30 días',
  '⚠️ ¿Hay facturas vencidas?',
];

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hola 👋 Soy **Argos**, tu asesor financiero IA. Estoy conectado a los datos de Café Aruba en tiempo real.\n\nPodés preguntarme cualquier cosa sobre tu negocio en lenguaje natural. ¿En qué te puedo ayudar hoy?',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  useEffect(scrollToBottom, [messages]);

  async function sendMessage(text) {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg, timestamp: new Date().toISOString() }]);
    setLoading(true);

    try {
      const res = await api.sendMessage(userMsg, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.response, timestamp: new Date().toISOString() },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Disculpá, hubo un error procesando tu consulta. ¿Podés intentar de nuevo?',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function renderContent(content) {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />');
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Chat header */}
      <div className="flex items-center gap-3 pb-4 border-b border-surface-200 mb-4">
        <div className="w-10 h-10 bg-gradient-to-br from-argos-400 to-argos-600 rounded-2xl flex items-center justify-center shadow-sm shadow-argos-600/30">
          <Eye size={18} className="text-white" />
        </div>
        <div>
          <p className="font-sans font-bold text-surface-900">Argos</p>
          <p className="text-xs text-argos-400 flex items-center gap-1">
            <Sparkles size={10} />
            Conectado a tus datos en tiempo real
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 bg-gradient-to-br from-argos-400 to-argos-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <Eye size={14} className="text-white" />
              </div>
            )}
            <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-argos-400/10 border border-argos-400/25 text-surface-800 rounded-br-md'
                    : 'bg-surface-100 border border-surface-200 text-surface-700 rounded-bl-md'
                }`}
                dangerouslySetInnerHTML={{ __html: renderContent(msg.content) }}
              />
              <p className={`text-[10px] text-surface-400 mt-1 ${msg.role === 'user' ? 'text-right' : ''}`}>
                {formatTime(msg.timestamp)}
              </p>
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 bg-surface-200 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold text-surface-500">
                Yo
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-argos-400 to-argos-600 rounded-xl flex items-center justify-center flex-shrink-0">
              <Eye size={14} className="text-white" />
            </div>
            <div className="bg-surface-100 border border-surface-200 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-surface-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-surface-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-surface-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-surface-200 pt-4">
        {/* Suggestions */}
        {messages.length <= 2 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => sendMessage(s)}
                className="text-xs text-surface-500 border border-surface-200 rounded-full px-3 py-1.5 hover:bg-argos-400/10 hover:border-argos-400/30 hover:text-argos-400 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="flex gap-2 items-end">
          <div className="flex-1 bg-surface-100 border border-surface-200 rounded-2xl px-4 py-3 flex items-center gap-2">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Preguntale algo a Argos sobre tu negocio..."
              className="flex-1 bg-transparent outline-none text-sm text-surface-800 placeholder:text-surface-400"
              disabled={loading}
            />
          </div>
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="w-10 h-10 bg-argos-600 rounded-xl flex items-center justify-center text-white hover:bg-argos-500 disabled:opacity-40 transition-colors flex-shrink-0"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
