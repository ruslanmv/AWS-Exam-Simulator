import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';

const MarkdownContent = ({ content, className = '' }) => {
  if (!content) return null;

  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          h1: ({ children }) => <h2 className="text-lg font-bold text-gray-900 mt-3 mb-1">{children}</h2>,
          h2: ({ children }) => <h3 className="text-base font-bold text-gray-900 mt-3 mb-1">{children}</h3>,
          h3: ({ children }) => <h4 className="text-sm font-bold text-gray-900 mt-2 mb-1">{children}</h4>,
          p: ({ children }) => <p className="my-1.5 text-gray-700 leading-relaxed text-sm">{children}</p>,
          ul: ({ children }) => <ul className="list-disc ml-4 my-1.5 text-sm text-gray-700">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal ml-4 my-1.5 text-sm text-gray-700">{children}</ol>,
          li: ({ children }) => <li className="my-0.5">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
          code: ({ inline, children }) =>
            inline ? (
              <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
            ) : (
              <pre className="bg-gray-800 text-green-300 p-3 rounded-lg my-2 overflow-x-auto text-xs">
                <code>{children}</code>
              </pre>
            ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-purple-300 pl-3 my-2 text-gray-600 italic text-sm">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full border border-gray-200 text-sm">{children}</table>
            </div>
          ),
          th: ({ children }) => <th className="border border-gray-200 px-2 py-1 bg-gray-50 font-semibold text-left">{children}</th>,
          td: ({ children }) => <td className="border border-gray-200 px-2 py-1">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownContent;
