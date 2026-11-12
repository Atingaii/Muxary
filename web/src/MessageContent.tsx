import { memo, useState } from 'react';
import { Markdown } from './vendor/agent-elements/markdown';
import { UserMessage } from './vendor/agent-elements/user-message';

// Large results stay complete, but do not all invoke a Markdown parser on every
// refresh. Native details provides keyboard access without another UI runtime.
function LongMessage({content}: {content: string}) {
  const [expanded, setExpanded] = useState(false);
  return <div className="long-message">
    <pre className="message-preview">{content.slice(0, 2000)}…</pre>
    <details onToggle={event => setExpanded(event.currentTarget.open)}>
      <summary>查看完整原文（{content.length.toLocaleString()} 字符）</summary>
      {expanded && <pre className="message-full-text">{content}</pre>}
    </details>
    <small>长内容按需展开为纯文本；完整内容未裁剪。</small>
  </div>;
}

export const MessageContent = memo(function MessageContent({id, content, user = false}: {id: string; content: string; user?: boolean}) {
  if (content.length > 12_000) return <LongMessage content={content}/>;
  return user ? <UserMessage message={{id, role: 'user', parts: [{type: 'text', text: content}]}}/> : <Markdown content={content}/>;
});
