import { useState, useRef } from 'react'
import type { Message } from '../api/types'
import './DialogueInput.css'

interface Props {
  onSubmit: (messages: Message[]) => void
  isLoading: boolean
}

function parseDialogue(raw: string): Message[] {
  const lines = raw.split('\n').filter((l) => l.trim())
  const messages: Message[] = []

  for (const line of lines) {
    // Try "Role: text" format
    const colonMatch = line.match(/^([A-Za-z0-9_-]+):\s*(.+)/)
    if (colonMatch) {
      messages.push({ role: colonMatch[1], text: colonMatch[2] })
      continue
    }
    // Fallback: append to last message or create new one
    if (messages.length > 0) {
      messages[messages.length - 1].text += '\n' + line.trim()
    } else {
      messages.push({ role: 'A', text: line.trim() })
    }
  }

  return messages
}

export function DialogueInput({ onSubmit, isLoading }: Props) {
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = () => {
    setError(null)
    const trimmed = text.trim()
    if (!trimmed) {
      setError('Please enter or upload a dialogue.')
      return
    }
    const messages = parseDialogue(trimmed)
    if (messages.length === 0) {
      setError('Could not parse any messages from the input.')
      return
    }
    onSubmit(messages)
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 100_000) {
      setError('File too large (max 100KB).')
      return
    }
    const content = await file.text()
    setText(content)
    setError(null)
    e.target.value = ''
  }

  return (
    <div className="dialogue-input">
      <div className="input-header">
        <h2 className="input-title">Dialogue Input</h2>
        <div className="input-actions">
          <button
            className="btn btn--secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
          >
            Upload File
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.csv,.json"
            onChange={handleFileUpload}
            hidden
          />
        </div>
      </div>

      <textarea
        className="dialogue-textarea"
        placeholder={"Paste dialogue here...\n\nFormat: one line per message, e.g.:\nA: Ich bin mir unsicher.\nB: Was meinst du damit?"}
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={8}
        disabled={isLoading}
        aria-label="Dialogue text input"
      />

      {error && (
        <div className="input-error" role="alert">{error}</div>
      )}

      <div className="input-footer">
        <span className="input-hint">
          Format: &quot;Role: text&quot; per line
        </span>
        <button
          className="btn btn--primary"
          onClick={handleSubmit}
          disabled={isLoading || !text.trim()}
        >
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </div>
  )
}
