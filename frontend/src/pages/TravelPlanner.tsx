import { useState, useEffect } from "react";
import { Send, CheckCircle, XCircle, Loader2, Shield } from "lucide-react";
import { travelApi } from "../services/api";
import { AGENT_INFO } from "../types";
import type { TravelResponse } from "../types";
import TravelPlanDisplay from "../components/TravelPlanDisplay";
import "./TravelPlanner.css";

const TravelPlanner = () => {
  const [message, setMessage] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<TravelResponse | null>(null);
  const [showApproval, setShowApproval] = useState(false);
  const [approvalFeedback, setApprovalFeedback] = useState("");

  useEffect(() => {
    const savedThreadId = localStorage.getItem("travel_thread_id");
    if (savedThreadId) {
      setThreadId(savedThreadId);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    setLoading(true);
    setShowApproval(false);
    setResponse(null);

    try {
      const result = await travelApi.submitTravelRequest({
        message: message.trim(),
        thread_id: threadId,
      });

      setResponse(result);

      if (result.thread_id) {
        setThreadId(result.thread_id);
        localStorage.setItem("travel_thread_id", result.thread_id);
      }

      if (result.requires_approval) {
        setShowApproval(true);
      }
    } catch (error: any) {
      setResponse({
        success: false,
        thread_id: threadId || "",
        error:
          error.response?.data?.error || error.message || "An error occurred",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (approved: boolean) => {
    if (!threadId) return;

    setLoading(true);

    try {
      const result = await travelApi.approveTravelPlan({
        thread_id: threadId,
        approved,
        feedback: approvalFeedback,
      });

      setResponse(result);
      setShowApproval(false);
      setApprovalFeedback("");
    } catch (error: any) {
      setResponse({
        success: false,
        thread_id: threadId,
        error:
          error.response?.data?.error || error.message || "An error occurred",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    localStorage.removeItem("travel_thread_id");
    setThreadId(null);
    setMessage("");
    setResponse(null);
    setShowApproval(false);
    setApprovalFeedback("");
  };

  const quickPrompts = [
    "Plan a complete 7 days Japan trip from India including flights, hotels and sightseeing under 2 lakhs.",
    "Plan a 5 days Dubai trip from Dhaka with flights, hotels and sightseeing.",
    "Plan a 7 days Thailand trip from India with budget hotels and sightseeing.",
  ];

  return (
    <div className="travel-planner fade-in">
      <div className="hero-section">
        <div className="badge gradient-bg">
          ✈️ graph-voyage-ai — Multi-Agent Travel Planning with LangGraph,
          Guardrails, MCP & HITL
        </div>
        <h1>Plan Your Perfect Trip with AI</h1>
        <p className="hero-description">
          Search flights, discover hotels, check weather, assess your budget,
          and review the AI-generated draft before the final itinerary is
          created.
        </p>
      </div>

      <div className="planner-card card">
        <div className="card-header">
          <div>
            <h2>Where do you want to go?</h2>
            <p className="card-subtitle">
              Example: Plan a complete 7 days Japan trip from India under 2
              lakhs.
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            {threadId && (
              <button
                onClick={handleNewConversation}
                className="btn btn-secondary"
                style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                title="Start a new conversation"
              >
                🔄 New Chat
              </button>
            )}
            <div className="status-badge success">
              <div className="status-dot"></div>
              Online
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakhs..."
            className="message-input"
            rows={4}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary submit-btn"
            disabled={loading || !message.trim()}
          >
            {loading ? (
              <>
                <Loader2 className="loading-spinner" size={20} />
                Processing...
              </>
            ) : (
              <>
                <Send size={20} />
                Generate Draft
              </>
            )}
          </button>
        </form>

        <div className="quick-prompts">
          {quickPrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => setMessage(prompt)}
              className="btn btn-secondary quick-prompt-btn"
              disabled={loading}
            >
              {prompt.split(" ").slice(0, 4).join(" ")}...
            </button>
          ))}
        </div>
      </div>

      {response?.supervisor_reasoning && (
        <div className="workflow-section card fade-in">
          <div className="section-header">
            <div>
              <span className="eyebrow">Supervisor Agent</span>
              <h3>Execution Plan</h3>
            </div>
            <div
              className={`badge ${response.guardrail_allowed ? "success" : "error"}`}
            >
              {response.guardrail_allowed ? (
                <>
                  <Shield size={16} />
                  Guardrail Passed
                </>
              ) : (
                <>
                  <XCircle size={16} />
                  Guardrail Failed
                </>
              )}
            </div>
          </div>
          <p className="reasoning-text">{response.supervisor_reasoning}</p>
          {response.agents_involved && response.agents_involved.length > 0 && (
            <div className="agent-chips">
              {response.agents_involved.map((agent) => {
                const info = AGENT_INFO[agent];
                return info ? (
                  <div key={agent} className="agent-chip">
                    <span className="agent-icon">{info.icon}</span>
                    <span className="agent-label">{info.label}</span>
                  </div>
                ) : null;
              })}
            </div>
          )}
        </div>
      )}

      {showApproval && (
        <div className="approval-section card fade-in">
          <div className="approval-icon">👤</div>
          <div className="approval-content">
            <span className="eyebrow">Human-in-the-Loop</span>
            <h3>Review the draft itinerary</h3>
            <p>
              Approve the draft or provide feedback before the final plan is
              generated.
            </p>

            <textarea
              value={approvalFeedback}
              onChange={(e) => setApprovalFeedback(e.target.value)}
              placeholder="Add revision feedback, for example: reduce the hotel cost and add one free day..."
              className="feedback-input"
              rows={3}
            />

            <div className="approval-actions">
              <button
                onClick={() => handleApproval(true)}
                className="btn btn-primary"
                disabled={loading}
              >
                <CheckCircle size={20} />
                Approve & Generate Final
              </button>
              <button
                onClick={() => handleApproval(false)}
                className="btn btn-outline"
                disabled={loading}
              >
                <XCircle size={20} />
                Revise Using Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      {response?.answer && (
        <div className="fade-in">
          <TravelPlanDisplay
            content={response.answer}
            threadId={threadId || undefined}
            latency={response.latency_seconds}
          />
        </div>
      )}

      {response?.error && (
        <div className="error-section card fade-in">
          <XCircle className="error-icon" />
          <div>
            <h4>Error</h4>
            <p>{response.error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TravelPlanner;
