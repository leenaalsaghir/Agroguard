import { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "../services/api";
import "../styles/chat.css";

function ChatScreen() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const content = input.trim();
    setInput("");
    await sendUserMessage(content);
  }

  async function sendUserMessage(content) {
    if (!content || isLoading) return;

    const userMessage = { role: "user", content };
    const historyBeforeNewMessage = messages.filter((message) => !message.error);

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const data = await sendChatMessage(userMessage.content, historyBeforeNewMessage);

      const botMessage = {
        role: "assistant",
        content: data.answer || data.response || data.message || "No response received.",
        escalated: data.escalated || data.needs_escalation || false,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `I could not connect to AgroGuardAI. ${error.message}`,
          escalated: false,
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="chat-card">
        <header className="chat-header">
          <div className="brand-block">
            <img src="/agrobot.png" alt="AgroGuardAI logo" className="header-logo" />
            <div>
              <h1>AgroGuardAI</h1>
              <p>Safe product support for agricultural customers</p>
            </div>
          </div>

          <span className="status">
            <span className="status-dot"></span>
            Ready
          </span>
        </header>

        <div className="chat-body">
          {messages.length === 0 ? (
            <div className="welcome-box">
              <img src="/agrobot.png" alt="AgroGuard Assistant" className="welcome-avatar" />
              <h2>How can we help?</h2>
              <p>Ask about agricultural products, usage, safety, or crop issues.</p>
              <div className="prompt-chips">
                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() => sendUserMessage("What is the shelf life of this product?")}
                >
                  What is the shelf life of this product?
                </button>
                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() => sendUserMessage("How should I apply this pesticide?")}
                >
                  How should I apply this pesticide?
                </button>
                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() => sendUserMessage("Is this product safe for organic farming?")}
                >
                  Is this product safe for organic farming?
                </button>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`message-row ${
                    message.role === "user" ? "user-row" : "assistant-row"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <div className="assistant-message">
                      <img
                        src="/agrobot.png"
                        alt="AgroGuard Assistant"
                        className="assistant-avatar"
                      />

                      <div className={`message-bubble assistant-bubble ${message.error ? "error-bubble" : ""}`}>
                        <p>{message.content}</p>

                        {message.escalated && (
                          <button className="representative-button" type="button">
                            Refer me to a representative
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="message-bubble user-bubble">
                      <p>{message.content}</p>
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="message-row assistant-row">
                  <div className="assistant-message">
                    <img
                      src="/agrobot.png"
                      alt="AgroGuard Assistant"
                      className="assistant-avatar"
                    />

                    <div className="message-bubble assistant-bubble loading-bubble">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <form className="chat-input-area" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about product use, safety, or crop issues..."
            disabled={isLoading}
          />

          <button type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? "Checking" : "Send"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default ChatScreen;
