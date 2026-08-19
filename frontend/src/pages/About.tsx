import { useState, useEffect } from "react";
import {
  Shield,
  Users,
  Zap,
  Database,
  GitBranch,
  Activity,
  Check,
  ArrowRight,
  Cpu,
  Cloud,
  Globe,
} from "lucide-react";
import { travelApi } from "../services/api";
import type { MetricsResponse } from "../types";
import "./About.css";

const About = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await travelApi.getMetrics();
        setMetrics(data);
      } catch (err) {
        console.error("Failed to fetch metrics:", err);
      }
    };
    fetchMetrics();
  }, []);

  const agents = [
    {
      name: "Supervisor",
      icon: Cpu,
      color: "#6366f1",
      description: "Routes tasks to specialist agents",
    },
    {
      name: "Flight Agent",
      icon: Globe,
      color: "#8b5cf6",
      description: "Searches flights & airlines",
    },
    {
      name: "Hotel Agent",
      icon: Cloud,
      color: "#ec4899",
      description: "Finds accommodation",
    },
    {
      name: "Weather Agent",
      icon: Activity,
      color: "#f59e0b",
      description: "Provides weather data",
    },
    {
      name: "Budget Agent",
      icon: Database,
      color: "#10b981",
      description: "Analyzes costs",
    },
    {
      name: "Itinerary Agent",
      icon: GitBranch,
      color: "#3b82f6",
      description: "Creates travel plans",
    },
  ];

  const technologies = [
    { name: "LangGraph", category: "Orchestration", icon: GitBranch },
    { name: "FastAPI", category: "Backend", icon: Zap },
    { name: "PostgreSQL", category: "Database", icon: Database },
    { name: "React + TypeScript", category: "Frontend", icon: Cpu },
    { name: "Groq LLM", category: "AI Model", icon: Cloud },
    { name: "MCP Tools", category: "Integration", icon: Globe },
  ];

  const features = [
    {
      title: "Input Guardrails",
      description: "Validates all requests before processing",
      icon: Shield,
    },
    {
      title: "Human-in-the-Loop",
      description: "Requires approval before finalizing plans",
      icon: Users,
    },
    {
      title: "Multi-Agent System",
      description: "6 specialized agents working together",
      icon: GitBranch,
    },
    {
      title: "Online Monitoring",
      description: "Real-time evaluation and metrics",
      icon: Activity,
    },
  ];

  return (
    <div className="about-page fade-in">
      {/* Hero Section */}
      <div className="about-hero">
        <div className="hero-content">
          <h1 className="hero-title gradient-text">graph-voyage-ai</h1>
          <p className="hero-subtitle">
            Multi-Agent AI Travel Planning System with LangGraph, Supervisor
            Patterns, and Human-in-the-Loop
          </p>

          {metrics && (
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-value">
                  {metrics.rolling_metrics?.total_requests?.toLocaleString() ||
                    "0"}
                </div>
                <div className="stat-label">Total Requests</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{agents.length}</div>
                <div className="stat-label">AI Agents</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {metrics.rolling_metrics?.pass_rate?.toFixed(0) || "0"}%
                </div>
                <div className="stat-label">Success Rate</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Architecture Section */}
      <section className="architecture-section">
        <h2 className="section-title">System Architecture</h2>
        <p className="section-description">
          GraphVoyageAI uses a sophisticated multi-agent architecture with
          supervisor pattern and guardrails
        </p>

        <div className="architecture-diagram">
          {/* User Input */}
          <div className="arch-node user-node">
            <Users size={24} />
            <span>User Request</span>
          </div>

          <ArrowRight className="arch-arrow" />

          {/* Guardrail */}
          <div className="arch-node guardrail-node">
            <Shield size={24} />
            <span>Input Guardrail</span>
          </div>

          <ArrowRight className="arch-arrow" />

          {/* Supervisor */}
          <div className="arch-node supervisor-node">
            <Cpu size={28} />
            <span>Supervisor Agent</span>
          </div>

          <div className="arch-flow">
            <ArrowRight className="arch-arrow vertical" />

            {/* Agent Grid */}
            <div className="agent-grid">
              {agents.slice(1).map((agent, idx) => (
                <div
                  key={idx}
                  className="agent-card"
                  style={{ borderColor: agent.color }}
                >
                  <agent.icon size={32} style={{ color: agent.color }} />
                  <h4>{agent.name}</h4>
                  <p>{agent.description}</p>
                </div>
              ))}
            </div>

            <ArrowRight className="arch-arrow vertical" />
          </div>

          {/* HITL */}
          <div className="arch-node hitl-node">
            <Users size={24} />
            <span>Human Approval</span>
          </div>

          <ArrowRight className="arch-arrow" />

          {/* Final Response */}
          <div className="arch-node final-node">
            <Check size={24} />
            <span>Final Plan</span>
          </div>
        </div>
      </section>

      {/* Agents Section */}
      <section className="agents-section">
        <h2 className="section-title">Specialized AI Agents</h2>
        <div className="agents-list">
          {agents.map((agent, idx) => (
            <div key={idx} className="agent-item card">
              <div className="agent-icon" style={{ background: agent.color }}>
                <agent.icon size={24} color="white" />
              </div>
              <div className="agent-info">
                <h3>{agent.name}</h3>
                <p>{agent.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2 className="section-title">Key Features</h2>
        <div className="features-grid">
          {features.map((feature, idx) => (
            <div key={idx} className="feature-card card">
              <feature.icon size={40} className="feature-icon" />
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Technologies Section */}
      <section className="tech-section">
        <h2 className="section-title">Technology Stack</h2>
        <div className="tech-grid">
          {technologies.map((tech, idx) => (
            <div key={idx} className="tech-card">
              <tech.icon size={28} />
              <div className="tech-info">
                <h4>{tech.name}</h4>
                <span className="tech-category">{tech.category}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow Section */}
      <section className="workflow-section">
        <h2 className="section-title">How It Works</h2>
        <div className="workflow-steps">
          <div className="workflow-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>Input Validation</h3>
              <p>
                Guardrail agent validates that the request is travel-related and
                safe
              </p>
            </div>
          </div>

          <div className="workflow-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>Task Routing</h3>
              <p>
                Supervisor agent analyzes the request and routes to appropriate
                specialist agents
              </p>
            </div>
          </div>

          <div className="workflow-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h3>Parallel Execution</h3>
              <p>
                Specialist agents work in parallel: flights, hotels, weather,
                budget analysis
              </p>
            </div>
          </div>

          <div className="workflow-step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h3>Itinerary Creation</h3>
              <p>
                Itinerary agent synthesizes all information into a cohesive
                travel plan
              </p>
            </div>
          </div>

          <div className="workflow-step">
            <div className="step-number">5</div>
            <div className="step-content">
              <h3>Human Approval</h3>
              <p>
                User reviews and approves/revises the plan before finalization
              </p>
            </div>
          </div>

          <div className="workflow-step">
            <div className="step-number">6</div>
            <div className="step-content">
              <h3>Final Response</h3>
              <p>
                System generates polished, actionable travel plan ready for
                booking
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Evaluation Section */}
      <section className="eval-section card">
        <h2>Online Monitoring & Evaluation</h2>
        <p>
          Every request is logged to PostgreSQL. A sampling system (configurable
          rate) evaluates requests for safety, latency, and completeness. The
          Dashboard provides real-time metrics and insights into system
          performance.
        </p>
        <div className="eval-metrics">
          <div className="eval-metric">
            <Activity size={24} />
            <span>Real-time tracking</span>
          </div>
          <div className="eval-metric">
            <Shield size={24} />
            <span>Safety checks</span>
          </div>
          <div className="eval-metric">
            <Zap size={24} />
            <span>Performance monitoring</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;
